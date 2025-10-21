"""知识库检索工具"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.ai.tools.base import BaseTool

LOGGER = logging.getLogger(__name__)


class KnowledgeSearchTool(BaseTool):
    """知识库检索工具，用于在知识库中搜索相关文档"""

    def __init__(self):
        """初始化知识库检索工具"""
        pass

    async def execute(
        self,
        query: str,
        kb_id: int,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        在知识库中检索相关文档

        :param query: 搜索查询
        :param kb_id: 知识库ID
        :param top_k: 返回结果数量，默认为5
        :return: 包含检索结果的字典
        """
        LOGGER.info("执行知识库检索: query='%s', kb_id=%d, top_k=%d", query[:50], kb_id, top_k)

        try:
            # 从 context 获取数据库会话
            from app.ai.context import get_current_db_session
            db = get_current_db_session()

            if db is None:
                error_msg = "数据库会话未设置，无法执行检索"
                LOGGER.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "documents": []
                }

            # 导入服务
            from app.services.rag.retrieval_service import RetrievalService

            # 创建检索服务
            retrieval_service = RetrievalService(db)

            # 执行检索
            results, search_time_ms = await retrieval_service.retrieve(
                query=query,
                kb_id=kb_id,
                top_k=top_k,
                top_k_recall=top_k * 4,  # 召回数量是返回数量的4倍
                similarity_threshold=0.2,  # 相似度阈值（降低以支持跨语言检索）
                use_rerank=True  # 使用重排序
            )

            if not results:
                LOGGER.info("未找到相关文档 (kb_id=%d)", kb_id)
                return {
                    "success": True,
                    "message": f"No relevant documents found in knowledge base {kb_id}",
                    "documents": [],
                    "total_found": 0,
                    "search_time_ms": search_time_ms
                }

            # 格式化返回结果
            documents = []
            for i, result in enumerate(results, 1):
                doc_dict = {
                    "index": i,
                    "content": result.parent_text,
                    "source": result.source or "Unknown",
                    "doc_id": result.doc_id,
                    "score": round(result.max_score, 4)
                }

                # 添加可选字段
                if result.page_number:
                    doc_dict["page"] = result.page_number
                if result.section:
                    doc_dict["section"] = result.section
                if result.doc_title:
                    doc_dict["doc_title"] = result.doc_title

                # 添加匹配的子块信息
                if result.matched_children:
                    doc_dict["matched_children"] = [
                        {
                            "content": child.child_text,
                            "score": round(child.score, 4),
                            "chunk_index": child.chunk_index
                        }
                        for child in result.matched_children[:3]  # 只返回前3个子块
                    ]

                documents.append(doc_dict)

            LOGGER.info("检索成功: 找到 %d 个文档，耗时 %dms", len(documents), search_time_ms)

            return {
                "success": True,
                "documents": documents,
                "total_found": len(documents),
                "search_time_ms": search_time_ms,
                "kb_id": kb_id,
                "query": query
            }

        except Exception as e:
            error_message = f"知识库检索失败: {str(e)}"
            LOGGER.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message,
                "documents": []
            }

    @classmethod
    def get_description(cls) -> str:
        """获取工具描述（会被动态更新知识库列表）"""
        return """Search the knowledge base for relevant documents.

This tool retrieves documents from the knowledge base that are relevant to the user's query.
Use this when the user asks about topics that might be covered in our documentation.

The tool will return relevant document chunks with their sources and page numbers.
Cite the sources when using information from the retrieved documents."""

