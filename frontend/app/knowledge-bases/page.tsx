'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { KnowledgeBase, knowledgeBaseApi } from '@/lib/api/rag';
import { toast } from 'react-hot-toast';
import {
  PlusIcon,
  TrashIcon,
  FolderIcon,
  DocumentTextIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

export default function KnowledgeBasesPage() {
  const router = useRouter();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKbName, setNewKbName] = useState('');
  const [newKbDescription, setNewKbDescription] = useState('');
  const [creating, setCreating] = useState(false);

  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    try {
      setLoading(true);
      const data = await knowledgeBaseApi.list();
      setKnowledgeBases(data.items);
    } catch (error: any) {
      toast.error('加载知识库失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  // 创建知识库
  const handleCreate = async () => {
    if (!newKbName.trim()) {
      toast.error('请输入知识库名称');
      return;
    }

    try {
      setCreating(true);
      await knowledgeBaseApi.create({
        name: newKbName.trim(),
        description: newKbDescription.trim() || undefined,
      });
      toast.success('知识库创建成功');
      setShowCreateModal(false);
      setNewKbName('');
      setNewKbDescription('');
      loadKnowledgeBases();
    } catch (error: any) {
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setCreating(false);
    }
  };

  // 删除知识库
  const handleDelete = async (kb: KnowledgeBase) => {
    if (!confirm(`确定要删除知识库 "${kb.name}" 吗？这将同时删除所有文档和向量数据。`)) {
      return;
    }

    try {
      await knowledgeBaseApi.delete(kb.id);
      toast.success('知识库已删除');
      loadKnowledgeBases();
    } catch (error: any) {
      toast.error('删除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">📚 知识库管理</h1>
            <p className="text-gray-600">管理您的文档知识库，支持 PDF/Word/TXT 等格式</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors shadow-lg hover:shadow-xl"
          >
            <PlusIcon className="w-5 h-5" />
            <span>新建知识库</span>
          </button>
        </div>

        {/* 知识库列表 */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : knowledgeBases.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <FolderIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">还没有知识库</h3>
            <p className="text-gray-600 mb-6">点击"新建知识库"按钮开始创建您的第一个知识库</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              <span>新建知识库</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {knowledgeBases.map((kb) => (
              <div
                key={kb.id}
                className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 overflow-hidden group cursor-pointer"
                onClick={() => router.push(`/knowledge-bases/${kb.id}`)}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                        {kb.name}
                      </h3>
                      {kb.description && (
                        <p className="text-gray-600 text-sm line-clamp-2">{kb.description}</p>
                      )}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(kb);
                      }}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="删除知识库"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>

                  {/* 统计信息 */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                    <div className="flex items-center space-x-2">
                      <DocumentTextIcon className="w-5 h-5 text-blue-500" />
                      <div>
                        <p className="text-2xl font-bold text-gray-900">{kb.doc_count}</p>
                        <p className="text-xs text-gray-500">文档数</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ChartBarIcon className="w-5 h-5 text-purple-500" />
                      <div>
                        <p className="text-2xl font-bold text-gray-900">{kb.chunk_count}</p>
                        <p className="text-xs text-gray-500">向量数</p>
                      </div>
                    </div>
                  </div>

                  {/* 时间信息 */}
                  <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
                    创建于 {new Date(kb.created_at).toLocaleDateString('zh-CN')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 创建知识库模态框 */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">新建知识库</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    知识库名称 *
                  </label>
                  <input
                    type="text"
                    value={newKbName}
                    onChange={(e) => setNewKbName(e.target.value)}
                    placeholder="例如：学术论文库"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    描述（可选）
                  </label>
                  <textarea
                    value={newKbDescription}
                    onChange={(e) => setNewKbDescription(e.target.value)}
                    placeholder="简要描述这个知识库的用途..."
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewKbName('');
                    setNewKbDescription('');
                  }}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  disabled={creating}
                >
                  取消
                </button>
                <button
                  onClick={handleCreate}
                  disabled={creating || !newKbName.trim()}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {creating ? '创建中...' : '创建'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

