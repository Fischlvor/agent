"""检索服务（召回+重排+去重）- 基于 PGVector"""

import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
import logging

from app.models.rag import Document, DocumentChunk, ChunkType
from app.services.rag.model_manager import get_embeddings, get_reranker
from app.schemas.rag import RetrievalResult, MatchedChild

logger = logging.getLogger(__name__)


class RetrievalService:
    """检索服务 - 基于 PGVector 向量检索"""

    def __init__(self, db: Session):
        self.db = db
        # 使用全局单例的模型（不会重复加载）
        self.embeddings = get_embeddings()
        self.reranker = get_reranker()

    async def retrieve(
        self,
        query: str,
        kb_id: int,
        top_k: int = 5,
        top_k_recall: int = 20,
        similarity_threshold: float = 0.7,
        use_rerank: bool = True
    ) -> tuple[List[RetrievalResult], int]:
        """
        两阶段检索：召回 + 重排 + 去重

        Args:
            query: 查询文本
            kb_id: 知识库ID
            top_k: 最终返回的父块数量
            top_k_recall: 召回的子块数量
            similarity_threshold: 相似度阈值（0-1，余弦相似度）
            use_rerank: 是否使用重排序

        Returns:
            (results, search_time_ms)
        """
        start_time = time.time()

        # ===== 阶段 1：向量召回（使用 pgvector）=====
        logger.info(f"开始检索: query='{query[:50]}...', kb_id={kb_id}")

        # 1.1 将查询文本转换为向量
        query_embedding = self.embeddings.embed_query(query)
        logger.info(f"🔍 query_embedding类型={type(query_embedding)}, 维度={len(query_embedding)}, 前5值={query_embedding[:5]}")

        # 1.2 使用 pgvector 的余弦相似度搜索（1 - 余弦距离 = 余弦相似度）
        # pgvector 的 <=> 操作符计算余弦距离，需要转换为相似度
        sql = text("""
            SELECT
                dc.id,
                dc.parent_id,
                dc.content,
                dc.chunk_index,
                dc.page_number,
                dc.section_title,
                dc.metadata,
                1 - (dc.embedding <=> :query_embedding) AS similarity
            FROM document_chunks dc
            JOIN documents d ON dc.doc_id = d.id
            WHERE d.kb_id = :kb_id
                AND dc.chunk_type = 'CHILD'
                AND dc.embedding IS NOT NULL
                AND 1 - (dc.embedding <=> :query_embedding) >= :threshold
            ORDER BY dc.embedding <=> :query_embedding
            LIMIT :limit
        """)

        query_embedding_str = str(query_embedding)
        logger.info(f"🔍 query_embedding字符串格式: {query_embedding_str[:100]}...")
        logger.info(f"🔍 查询参数: kb_id={kb_id}, threshold={similarity_threshold}, limit={top_k_recall}")

        result = self.db.execute(
            sql,
            {
                "query_embedding": query_embedding_str,  # pgvector 接受字符串格式的向量
                "kb_id": kb_id,
                "threshold": similarity_threshold,
                "limit": top_k_recall
            }
        )

        child_results = result.fetchall()

        if not child_results:
            logger.warning(f"❌ 未找到相关内容 (kb_id={kb_id}, threshold={similarity_threshold})")
            return [], int((time.time() - start_time) * 1000)

        logger.info(f"召回 {len(child_results)} 个子块")

        # 构造子块数据
        child_ids = [row[0] for row in child_results]
        child_scores = {row[0]: float(row[7]) for row in child_results}

        # ===== 阶段 2：重排序（可选）=====
        if use_rerank and len(child_results) > 1:
            chunk_texts = [row[2] for row in child_results]  # content
            rerank_scores = await self.reranker.rerank(query, chunk_texts)

            logger.info(f"重排序完成")

            # 更新分数
            for cid, rerank_score in zip(child_ids, rerank_scores):
                child_scores[cid] = rerank_score

        # ===== 阶段 3：聚合父块 + 去重 =====
        parent_groups = {}

        for row in child_results:
            child_id, parent_id, content, chunk_index, page_number, section_title, metadata, similarity = row

            if parent_id is None:
                logger.warning(f"子块 {child_id} 没有父块")
                continue

            if parent_id not in parent_groups:
                parent_groups[parent_id] = {
                    'children': [],
                    'max_score': 0.0
                }

            score = child_scores.get(child_id, 0.0)
            parent_groups[parent_id]['children'].append({
                'child_id': child_id,
                'content': content,
                'chunk_index': chunk_index,
                'page_number': page_number,
                'score': score
            })
            parent_groups[parent_id]['max_score'] = max(
                parent_groups[parent_id]['max_score'],
                score
            )

        logger.info(f"聚合到 {len(parent_groups)} 个父块")

        # ===== 阶段 4：按最高分数排序 + 取 Top-K =====
        sorted_parents = sorted(
            parent_groups.items(),
            key=lambda x: x[1]['max_score'],
            reverse=True
        )[:top_k]

        # ===== 阶段 5：构造返回结果 =====
        results = []
        parent_ids = [pid for pid, _ in sorted_parents]

        # 批量查询父块
        parents = self.db.query(DocumentChunk).filter(
            and_(
                DocumentChunk.id.in_(parent_ids),
                DocumentChunk.chunk_type == ChunkType.PARENT
            )
        ).all()
        parent_dict = {p.id: p for p in parents}

        # 批量查询文档
        doc_ids = list(set(p.doc_id for p in parents))
        documents = self.db.query(Document).filter(
            Document.id.in_(doc_ids)
        ).all()
        doc_dict = {d.id: d for d in documents}

        for pid, group_data in sorted_parents:
            if pid not in parent_dict:
                continue

            parent = parent_dict[pid]
            doc = doc_dict.get(parent.doc_id)

            # 构造匹配的子块列表
            matched_children = []
            for child_data in group_data['children']:
                matched_children.append(MatchedChild(
                    child_id=child_data['child_id'],
                    child_text=child_data['content'],
                    score=child_data['score'],
                    chunk_index=child_data['chunk_index']
                ))

            # 按分数排序子块
            matched_children.sort(key=lambda x: x.score, reverse=True)

            result = RetrievalResult(
                parent_id=parent.id,
                parent_text=parent.content,
                doc_id=parent.doc_id,
                doc_title=doc.metadata_.get('title') if doc and doc.metadata_ else None,
                section=parent.section_title,
                page_number=parent.page_number,
                matched_children=matched_children,
                max_score=group_data['max_score'],
                source=doc.filename if doc else "Unknown"
            )
            results.append(result)

        search_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"检索完成: 返回 {len(results)} 个结果, 耗时 {search_time_ms}ms")

        return results, search_time_ms
