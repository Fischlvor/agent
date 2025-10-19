/**
 * RAG 知识库 API 客户端
 */

import { apiClient } from '@/lib/api';

// 复用 apiClient 的 axios 实例，自动继承 token 刷新等拦截器
const api = apiClient.getAxiosInstance();

// ==================== 类型定义 ====================

export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  doc_count: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  kb_id: number;
  filename: string;
  filepath: string;
  filesize?: number;
  filehash?: string;
  metadata?: {
    title?: string;
    authors?: string[];
    abstract?: string;
    keywords?: string[];
  };
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_msg?: string;
  page_count?: number;
  chunk_count: number;
  parent_chunk_count: number;
  processed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface RetrievalResult {
  parent_id: number;
  parent_text: string;
  doc_id: number;
  doc_title?: string;
  section?: string;
  page_number?: number;
  matched_children: {
    child_id: number;
    child_text: string;
    score: number;
    chunk_index: number;
  }[];
  max_score: number;
  source: string;
}

export interface RetrievalResponse {
  query: string;
  results: RetrievalResult[];
  total_found: number;
  search_time_ms: number;
}

// ==================== 知识库管理 ====================

export const knowledgeBaseApi = {
  /**
   * 创建知识库
   */
  create: async (data: { name: string; description?: string }) => {
    const response = await api.post<KnowledgeBase>('/rag/knowledge-bases', data);
    return response.data;
  },

  /**
   * 获取知识库列表
   */
  list: async (params?: { skip?: number; limit?: number }) => {
    const response = await api.get<{ items: KnowledgeBase[]; total: number }>(
      '/rag/knowledge-bases',
      { params }
    );
    return response.data;
  },

  /**
   * 获取知识库详情
   */
  get: async (kbId: number) => {
    const response = await api.get<KnowledgeBase>(`/rag/knowledge-bases/${kbId}`);
    return response.data;
  },

  /**
   * 更新知识库
   */
  update: async (kbId: number, data: { name?: string; description?: string }) => {
    const response = await api.put<KnowledgeBase>(`/rag/knowledge-bases/${kbId}`, data);
    return response.data;
  },

  /**
   * 删除知识库
   */
  delete: async (kbId: number) => {
    await api.delete(`/rag/knowledge-bases/${kbId}`);
  },
};

// ==================== 文档管理 ====================

export const documentApi = {
  /**
   * 上传文档
   */
  upload: async (kbId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<{
      doc_id: number;
      filename: string;
      status: string;
      message: string;
    }>(`/rag/knowledge-bases/${kbId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  /**
   * 获取文档列表
   */
  list: async (kbId: number, params?: { skip?: number; limit?: number }) => {
    const response = await api.get<{ items: Document[]; total: number }>(
      `/rag/knowledge-bases/${kbId}/documents`,
      { params }
    );
    return response.data;
  },

  /**
   * 获取文档详情
   */
  get: async (docId: number) => {
    const response = await api.get<Document>(`/rag/knowledge-bases/documents/${docId}`);
    return response.data;
  },

  /**
   * 获取文档处理状态
   */
  getStatus: async (docId: number) => {
    const response = await api.get<{
      doc_id: number;
      status: string;
      progress: number;
      message?: string;
      error?: string;
    }>(`/rag/knowledge-bases/documents/${docId}/status`);
    return response.data;
  },

  /**
   * 删除文档
   */
  delete: async (docId: number) => {
    await api.delete(`/rag/knowledge-bases/documents/${docId}`);
  },
};

// ==================== 检索 ====================

export const retrievalApi = {
  /**
   * 检索知识库
   */
  retrieve: async (
    kbId: number,
    params: {
      query: string;
      top_k?: number;
      similarity_threshold?: number;
      use_rerank?: boolean;
    }
  ) => {
    const response = await api.post<RetrievalResponse>(
      `/rag/knowledge-bases/${kbId}/retrieve`,
      {
        query: params.query,
        kb_id: kbId,
        top_k: params.top_k ?? 5,
        similarity_threshold: params.similarity_threshold ?? 0.7,
        use_rerank: params.use_rerank ?? true,
      }
    );
    return response.data;
  },
};

