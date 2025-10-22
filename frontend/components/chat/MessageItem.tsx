'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import type { ChatMessage, TimelineEvent } from '@/types/chat';
import { useChatStore } from '@/store/chatStore';
import 'highlight.js/styles/github-dark.css';

interface MessageItemProps {
  message: ChatMessage;
}

export default function MessageItem({ message }: MessageItemProps) {
  const { editMessageAndRegenerate } = useChatStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content || '');
  const [showActions, setShowActions] = useState(false);

  const handleEdit = () => {
    setIsEditing(true);
    setEditContent(message.content || '');
  };

  const handleSaveEdit = async () => {
    const trimmedContent = editContent.trim();
    if (trimmedContent && trimmedContent !== message.content) {
      await editMessageAndRegenerate(message.message_id || message.id, trimmedContent);
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditContent(message.content || '');
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content || '');
  };

  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  // ✅ 渲染时间线事件（与 StreamingMessageItem 保持一致的卡片样式）
  const renderTimelineEvent = (event: TimelineEvent, index: number) => {
    if (event.type === 'thinking') {
      const isCompleted = event.status === 'success' || event.status === '已完成思考';

      return (
        <div key={event.thinking_id || index} className="p-3 rounded-lg border bg-yellow-50 border-yellow-200 opacity-60 mb-2">
          <div className="flex items-center space-x-2 text-sm text-yellow-800">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">✓ 已完成思考</span>
          </div>
          {event.content && (
            <details className="mt-2 text-xs text-yellow-900">
              <summary className="cursor-pointer hover:text-yellow-700">查看思考过程</summary>
              <div className="mt-2 pt-2 border-t border-yellow-200 whitespace-pre-wrap">
                {event.content}
              </div>
            </details>
          )}
        </div>
      );
    }

    if (event.type === 'tool_call') {
      const isSuccess = event.status === 'success';

      return (
        <div key={event.tool_id || index} className={`p-3 rounded-lg border opacity-60 mb-2 ${
          isSuccess
            ? 'bg-green-50 border-green-200'
            : event.status === 'error'
            ? 'bg-red-50 border-red-200'
            : 'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center space-x-2 mb-2">
            {isSuccess ? (
              <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : event.status === 'error' ? (
              <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
              </svg>
            )}
            <span className="text-sm font-medium">
              {isSuccess && '✓ 调用成功'}
              {event.status === 'error' && '✗ 调用失败'}
              {event.status === 'pending' && '⚙️ 正在调用'}
            </span>
            <code className="text-xs bg-white px-2 py-0.5 rounded font-mono">
              {event.tool_name}
            </code>
          </div>

          {/* ✅ 专门处理search_knowledge_base的结果显示 */}
          {isSuccess && event.tool_name === 'search_knowledge_base' && event.result && (() => {
            try {
              // 解析result（可能是字符串或对象）
              let resultData = event.result.result;
              if (typeof resultData === 'string') {
                resultData = JSON.parse(resultData);
              }

              const documents = resultData?.documents || [];
              const totalFound = resultData?.total_found || documents.length;

              if (totalFound === 0) return null;

              // ✅ 按文档名聚合（合并同一文档的不同chunk）
              const groupedDocs = new Map();
              documents.forEach((doc: any) => {
                const fileName = doc.source?.split('/').pop() || '未命名文档';
                if (!groupedDocs.has(fileName)) {
                  groupedDocs.set(fileName, {
                    fileName,
                    pages: new Set(),
                    maxScore: doc.score || 0,
                    chunks: []
                  });
                }
                const group = groupedDocs.get(fileName);
                if (doc.page) group.pages.add(doc.page);
                group.maxScore = Math.max(group.maxScore, doc.score || 0);
                group.chunks.push(doc);
              });

              const uniqueDocs = Array.from(groupedDocs.values());

              return (
                <div className="text-xs space-y-1.5 mt-2">
                  <div className="font-medium text-green-900">
                    📚 检索到 {uniqueDocs.length} 个文档，{totalFound} 个相关片段
                  </div>
                  <details className="bg-green-100 border border-green-200 rounded p-2">
                    <summary className="cursor-pointer hover:text-green-700 font-medium">
                      查看检索结果
                    </summary>
                    <div className="mt-2 pt-2 border-t border-green-300 space-y-2">
                      {uniqueDocs.slice(0, 3).map((group: any, idx: number) => {
                        const pagesArray = Array.from(group.pages).sort((a: any, b: any) => a - b);
                        const pagesText = pagesArray.length > 0
                          ? pagesArray.length <= 3
                            ? `p.${pagesArray.join(', ')}`
                            : `p.${pagesArray.slice(0, 2).join(', ')}...等${pagesArray.length}页`
                          : '';

                        const displayFileName = group.fileName.length > 100
                          ? group.fileName.substring(0, Math.floor(group.fileName.length * 0.8)) + '...'
                          : group.fileName;

                        return (
                          <details key={idx} className="bg-white border border-green-200 rounded p-1.5">
                            <summary
                              className="cursor-pointer hover:text-green-700 font-medium text-green-800"
                              title={group.fileName}
                            >
                              📄 {displayFileName}
                              {pagesText && ` (${pagesText})`}
                              {' - '}
                              <span className="text-green-600">{(group.maxScore * 100).toFixed(0)}%</span>
                              {group.chunks.length > 1 && (
                                <span className="ml-1 text-xs text-gray-500">({group.chunks.length}个片段)</span>
                              )}
                            </summary>
                            <div className="mt-2 pt-2 border-t border-green-200 space-y-1.5 pl-4">
                              {group.chunks.map((chunk: any, cidx: number) => {
                                const contentLength = chunk.content?.length || 0;
                                const summaryLength = Math.floor(contentLength * 0.8);
                                const detailLength = Math.floor(contentLength * 0.8);

                                return (
                                  <details key={cidx} className="text-green-700 bg-green-50 rounded p-1.5 text-xs border-l-2 border-green-300">
                                    <summary className="cursor-pointer font-medium hover:text-green-800">
                                      {chunk.page && <span className="text-green-600">p.{chunk.page}: </span>}
                                      <span className="line-clamp-2">{chunk.content?.substring(0, summaryLength)}...</span>
                                    </summary>
                                    <div className="mt-2 pt-2 border-t border-green-200 text-green-700 whitespace-pre-wrap">
                                      {chunk.content?.substring(0, detailLength)}...
                                    </div>
                                  </details>
                                );
                              })}
                            </div>
                          </details>
                        );
                      })}
                      {uniqueDocs.length > 3 && (
                        <div className="text-center text-green-600">
                          ...还有 {uniqueDocs.length - 3} 个文档
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              );
            } catch (e) {
              console.error('Failed to parse search result:', e);
              return null;
            }
          })()}

          {/* 其他工具的结果 */}
          {!isSuccess || event.tool_name !== 'search_knowledge_base' ? (
            <details className="text-xs">
              <summary className="cursor-pointer text-gray-600 hover:text-gray-900">查看详情</summary>
              <div className="mt-2 space-y-2">
                {event.tool_args && (
                  <div>
                    <div className="font-medium text-gray-600 mb-1">参数:</div>
                    <pre className="p-2 bg-white rounded overflow-x-auto">
                      {JSON.stringify(event.tool_args, null, 2)}
                    </pre>
                  </div>
                )}
                {event.result && (
                  <div>
                    <div className="font-medium text-gray-600 mb-1">结果:</div>
                    <pre className="p-2 bg-white rounded overflow-x-auto max-h-40">
                      {typeof event.result === 'string' ? event.result : JSON.stringify(event.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </details>
          ) : null}
        </div>
      );
    }

    return null;
  };

  return (
    <div className={`flex ${isUser ? 'flex-row-reverse space-x-reverse' : ''} space-x-3`}>
      {/* 头像 */}
      <div className="flex-shrink-0">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isUser
              ? 'bg-gradient-to-br from-primary-400 to-primary-600'
              : 'bg-gradient-to-br from-gray-400 to-gray-600'
          }`}
        >
          <span className="text-white text-sm font-medium">
            {isUser ? 'U' : 'AI'}
          </span>
        </div>
      </div>

      {/* 消息内容 */}
      <div
        className={`flex-1 ${isUser ? 'max-w-2xl ml-auto' : 'max-w-4xl'}`}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        <div>
          {isEditing ? (
            <div className="space-y-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="input w-full min-h-[100px] font-mono text-sm"
                autoFocus
              />
              <div className="flex space-x-2">
                <button
                  onClick={handleSaveEdit}
                  className="btn-primary text-sm px-3 py-1"
                >
                  保存
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="btn-secondary text-sm px-3 py-1"
                >
                  取消
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {/* ✅ 按时间线顺序展示事件 */}
              {isAssistant && message.timeline && message.timeline.length > 0 && (
                <>
                  {message.timeline.map((event, index) => renderTimelineEvent(event, index))}
                </>
              )}

              {/* 消息内容 */}
              <div
                className={`rounded-lg px-4 py-3 ${
                  isUser
                    ? 'bg-primary-500 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                {isAssistant ? (
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeHighlight, rehypeRaw]}
                      components={{
                        code({ node, inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '');
                          return !inline && match ? (
                            <div className="relative group">
                              <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                  onClick={() => navigator.clipboard.writeText(String(children))}
                                  className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded"
                                >
                                  复制
                                </button>
                              </div>
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </div>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        }
                      }}
                    >
                      {message.content || ''}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
            </div>
          )}

          {/* 操作按钮和元数据 */}
          <div className="flex items-center justify-between mt-2">
            {/* 左侧：操作按钮 */}
            <div className="flex items-center space-x-2">
              {showActions && !isEditing && (
                <>
                  <button
                    onClick={handleCopy}
                    className="text-xs text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    复制
                  </button>
                  {isUser && (
                    <button
                      onClick={handleEdit}
                      className="text-xs text-gray-600 hover:text-gray-900 transition-colors"
                    >
                      编辑
                    </button>
                  )}
                </>
              )}
            </div>

            {/* 右侧：时间和用时 */}
            <div className="flex items-center space-x-3 text-xs text-gray-500">
              <span>{new Date(message.created_at).toLocaleTimeString('zh-CN')}</span>
              {message.total_tokens && (
                <span>{message.total_tokens} tokens</span>
              )}
              {message.generation_time && (
                <span>{message.generation_time.toFixed(2)}s</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
