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
  const { editMessageAndRegenerate, deleteMessage } = useChatStore();
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
      // ✅ 编辑消息并重新生成回复（不会创建重复的用户消息）
      await editMessageAndRegenerate(message.id, trimmedContent);
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditContent(message.content || '');
  };

  const handleDelete = async () => {
    if (confirm('确定要删除这条消息吗？这将删除该消息之后的所有回复。')) {
      await deleteMessage(message.id);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content || '');
    // TODO: 显示复制成功提示
  };

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
        </div>
      );
    }

    return null;
  };

  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className={`max-w-3xl w-full flex ${isUser ? 'flex-row-reverse' : 'flex-row'} space-x-3`}>
        {/* 头像 */}
        <div className="flex-shrink-0">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center ${
              isUser
                ? 'bg-primary-500 text-white'
                : 'bg-gradient-to-br from-purple-500 to-pink-500 text-white'
            }`}
          >
            {isUser ? (
              <svg
                className="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z"
                />
                <path
                  d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z"
                />
              </svg>
            )}
          </div>
        </div>

        {/* 消息内容 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center mb-1 space-x-2">
            <span className="font-semibold text-sm text-gray-900">
              {isUser ? '你' : 'AI 助手'}
            </span>
            {message.is_edited && (
              <span className="text-xs text-gray-500">(已编辑)</span>
            )}
            {message.model_name && (
              <span className="text-xs text-gray-500">• {message.model_name}</span>
            )}
          </div>

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
                  <button
                    onClick={handleDelete}
                    className="text-xs text-red-600 hover:text-red-700 transition-colors"
                  >
                    删除
                  </button>
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

