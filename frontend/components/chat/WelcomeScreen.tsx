'use client';

import { useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import ModelSelector from './ModelSelector';
import { BookOpenIcon } from '@heroicons/react/24/outline';

interface WelcomeScreenProps {
  onSendMessage: (content: string, kbId?: number | null) => Promise<void>;
}

export default function WelcomeScreen({ onSendMessage }: WelcomeScreenProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedKbId, setSelectedKbId] = useState<number | null>(null);
  const [showKbSelector, setShowKbSelector] = useState(false);
  const { knowledgeBases } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setIsLoading(true);
    try {
      await onSendMessage(input.trim(), selectedKbId);
      setInput('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="h-full flex flex-col items-center justify-center px-4 py-8">
      <div className="w-full max-w-3xl">
        {/* Logo 和标题 */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <svg
              className="w-10 h-10 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            开始新对话
          </h1>
          <p className="text-gray-600">
            输入消息开始与 AI 的对话
          </p>
        </div>

        {/* 模型选择器 */}
        <div className="flex justify-center mb-6">
          <ModelSelector />
        </div>

        {/* 知识库选择器 */}
        {knowledgeBases.length > 0 && (
          <div className="mb-4 flex items-center justify-center space-x-2">
            <button
              type="button"
              onClick={() => setShowKbSelector(!showKbSelector)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg border-2 transition-all ${
                selectedKbId
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 hover:border-gray-400 text-gray-700'
              }`}
            >
              <BookOpenIcon className="w-5 h-5" />
              <span className="text-sm font-medium">
                {selectedKbId
                  ? knowledgeBases.find((kb) => kb.id === selectedKbId)?.name || '选择知识库'
                  : '选择知识库'}
              </span>
            </button>

            {selectedKbId && (
              <button
                type="button"
                onClick={() => setSelectedKbId(null)}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                清除
              </button>
            )}

            {showKbSelector && (
              <div className="absolute z-10 mt-2 bg-white border-2 border-gray-200 rounded-lg shadow-lg p-2 min-w-[300px] max-h-[300px] overflow-y-auto">
                <div className="text-xs text-gray-500 px-3 py-2 font-medium">选择知识库</div>
                {knowledgeBases.map((kb) => (
                  <button
                    key={kb.id}
                    type="button"
                    onClick={() => {
                      setSelectedKbId(kb.id);
                      setShowKbSelector(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded hover:bg-gray-100 transition-colors ${
                      selectedKbId === kb.id ? 'bg-blue-50 text-blue-700' : ''
                    }`}
                  >
                    <div className="font-medium text-sm">{kb.name}</div>
                    {kb.description && (
                      <div className="text-xs text-gray-500 truncate">{kb.description}</div>
                    )}
                    <div className="text-xs text-gray-400 mt-1">
                      {kb.doc_count} 文档 · {kb.chunk_count} 向量
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* RAG提示 */}
        {selectedKbId && (
          <div className="mb-4 flex items-center justify-center space-x-2 text-xs text-blue-600 bg-blue-50 rounded-lg py-2 px-3">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>
              已启用 RAG 检索 • AI 将搜索{' '}
              <strong>{knowledgeBases.find(kb => kb.id === selectedKbId)?.name}</strong>{' '}
              中的相关内容来回答问题
            </span>
          </div>
        )}

        {/* 输入框 */}
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative bg-white rounded-xl shadow-lg border border-gray-200 focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-200 transition-all">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息开始新对话..."
              disabled={isLoading}
              className="w-full px-6 py-4 text-gray-900 placeholder-gray-500 resize-none focus:outline-none rounded-xl"
              style={{ minHeight: '120px', maxHeight: '300px' }}
              rows={4}
            />

            {/* 底部工具栏 */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs font-mono">
                  Enter
                </kbd>
                <span>发送</span>
                <span className="text-gray-400">|</span>
                <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs font-mono">
                  Shift + Enter
                </kbd>
                <span>换行</span>
              </div>

              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <span>发送中...</span>
                  </>
                ) : (
                  <>
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                    <span>发送</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>

        {/* 快捷提示（可选） */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setInput('帮我写一篇关于人工智能的文章')}
            className="p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all text-left group"
          >
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">📝</span>
              <span className="font-medium text-gray-900">写作助手</span>
            </div>
            <p className="text-sm text-gray-600">
              帮我写一篇文章...
            </p>
          </button>

          <button
            onClick={() => setInput('帮我解释一下这段代码的作用')}
            className="p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all text-left group"
          >
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">💻</span>
              <span className="font-medium text-gray-900">代码助手</span>
            </div>
            <p className="text-sm text-gray-600">
              解释或优化代码...
            </p>
          </button>

          <button
            onClick={() => setInput('请将以下内容翻译成英文')}
            className="p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all text-left group"
          >
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">🌐</span>
              <span className="font-medium text-gray-900">翻译工具</span>
            </div>
            <p className="text-sm text-gray-600">
              翻译文本内容...
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}

