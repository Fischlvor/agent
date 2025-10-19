'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { KnowledgeBase, Document, knowledgeBaseApi, documentApi } from '@/lib/api/rag';
import { toast } from 'react-hot-toast';
import { wsManager, EventType } from '@/lib/websocket';
import {
  ArrowLeftIcon,
  CloudArrowUpIcon,
  DocumentTextIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

export default function KnowledgeBaseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const kbId = parseInt(params.id as string);

  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});

  // 加载知识库信息
  const loadKnowledgeBase = async () => {
    try {
      const data = await knowledgeBaseApi.get(kbId);
      setKb(data);
    } catch (error: any) {
      toast.error('加载知识库失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 加载文档列表
  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const data = await documentApi.list(kbId);
      setDocuments(data.items);
    } catch (error: any) {
      toast.error('加载文档列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  }, [kbId]);

  // 初始加载
  useEffect(() => {
    loadKnowledgeBase();
    loadDocuments();
  }, [kbId, loadDocuments]);

  // 订阅文档状态更新（使用全局WebSocket）
  useEffect(() => {
    const handleDocumentStatus = (message: any) => {
      try {
        const eventData = message.event_data ? JSON.parse(message.event_data) : {};
        const { kb_id, doc_id, status, error_msg } = eventData;

        // 只处理当前知识库的文档更新
        if (kb_id === kbId) {
          console.log(`Document ${doc_id} status updated: ${status}`);

          // 刷新文档列表和知识库信息
          loadDocuments();
          loadKnowledgeBase();

          // 显示通知
          if (status === 'completed') {
            toast.success('文档处理完成！');
          } else if (status === 'failed') {
            toast.error(`文档处理失败: ${error_msg || '未知错误'}`);
          }
        }
      } catch (error) {
        console.error('Failed to handle document status:', error);
      }
    };

    // 订阅文档状态更新事件
    const unsubscribe = wsManager.subscribe(EventType.DOCUMENT_STATUS_UPDATE, handleDocumentStatus);

    // 组件卸载时取消订阅
    return unsubscribe;
  }, [kbId, loadDocuments, loadKnowledgeBase]);

  // 处理文件上传
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setUploading(true);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // 检查文件类型
        const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.md'];
        const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
        if (!allowedTypes.includes(fileExt)) {
          toast.error(`${file.name}: 不支持的文件格式，仅支持 PDF、Word、TXT、Markdown`);
          continue;
        }

        // 检查文件大小 (50MB)
        if (file.size > 50 * 1024 * 1024) {
          toast.error(`${file.name}: 文件大小超过 50MB`);
          continue;
        }

        try {
          setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));

          const result = await documentApi.upload(kbId, file);

          setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }));
          toast.success(`${file.name} 上传成功`);
        } catch (error: any) {
          toast.error(`${file.name} 上传失败: ${error.response?.data?.detail || error.message}`);
        }
      }

      // 刷新列表
      await loadDocuments();
      await loadKnowledgeBase();
    } finally {
      setUploading(false);
      setUploadProgress({});
    }
  };

  // 删除文档
  const handleDelete = async (doc: Document) => {
    if (!confirm(`确定要删除文档 "${doc.filename}" 吗？`)) {
      return;
    }

    try {
      await documentApi.delete(doc.id);
      toast.success('文档已删除');
      loadDocuments();
      loadKnowledgeBase();
    } catch (error: any) {
      toast.error('删除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 获取状态图标和颜色
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircleIcon className="w-4 h-4" />
            <span>已完成</span>
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <ArrowPathIcon className="w-4 h-4 animate-spin" />
            <span>处理中</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <ExclamationCircleIcon className="w-4 h-4" />
            <span>失败</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            <ClockIcon className="w-4 h-4" />
            <span>待处理</span>
          </span>
        );
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 头部 */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/knowledge-bases')}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            <span>返回知识库列表</span>
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{kb?.name || '加载中...'}</h1>
              {kb?.description && <p className="text-gray-600">{kb.description}</p>}
              <div className="flex items-center space-x-6 mt-4 text-sm text-gray-600">
                <div>
                  <span className="font-medium">{kb?.doc_count || 0}</span> 个文档
                </div>
                <div>
                  <span className="font-medium">{kb?.chunk_count || 0}</span> 个向量块
                </div>
              </div>
            </div>

            {/* 上传按钮 */}
            <label className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors shadow-lg hover:shadow-xl cursor-pointer">
              <CloudArrowUpIcon className="w-5 h-5" />
              <span>{uploading ? '上传中...' : '上传文档'}</span>
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.md"
                onChange={(e) => handleFileUpload(e.target.files)}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* 上传进度 */}
        {Object.keys(uploadProgress).length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">上传进度</h3>
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <div key={filename} className="mb-2">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span className="truncate max-w-xs">{filename}</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 文档列表 */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">还没有文档</h3>
            <p className="text-gray-600 mb-6">点击"上传文档"按钮开始添加文档到知识库</p>
            <label className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors cursor-pointer">
              <CloudArrowUpIcon className="w-5 h-5" />
              <span>上传文档</span>
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.md"
                onChange={(e) => handleFileUpload(e.target.files)}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    文档名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    大小
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    页数
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    向量数
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    上传时间
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <DocumentTextIcon className="w-5 h-5 text-gray-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{doc.filename}</div>
                          {doc.metadata?.title && (
                            <div className="text-xs text-gray-500">{doc.metadata.title}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(doc.status)}
                      {doc.error_msg && (
                        <p className="text-xs text-red-600 mt-1">{doc.error_msg}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatFileSize(doc.filesize)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {doc.page_count || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {doc.chunk_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(doc.created_at).toLocaleString('zh-CN')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDelete(doc)}
                        className="text-red-600 hover:text-red-900 transition-colors"
                        title="删除文档"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

