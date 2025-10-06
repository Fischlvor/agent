'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import type { StreamingMessage } from '@/types/chat';
import 'highlight.js/styles/github-dark.css';

interface StreamingMessageItemProps {
  message: StreamingMessage;
}

export default function StreamingMessageItem({ message }: StreamingMessageItemProps) {
  return (
    <div className="flex justify-start">
      <div className="max-w-3xl w-full flex flex-row space-x-3">
        {/* AI 头像 */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white">
            <svg
              className="w-5 h-5 animate-pulse"
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
          </div>
        </div>

        {/* 消息内容 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center mb-1">
            <span className="font-semibold text-sm text-gray-900">AI 助手</span>
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
              <svg
                className="animate-spin -ml-0.5 mr-1 h-3 w-3"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              生成中
            </span>
          </div>

          {/* ✅ 渲染 timeline 事件 */}
          {message.timeline && message.timeline.length > 0 && (
            <div className="space-y-2 mb-3">
              {message.timeline.map((event, index) => {
                if (event.type === 'thinking') {
                  const isCompleted = event.status === 'success' || event.status === '已完成思考';
                  const isActive = !isCompleted;

                  return (
                    <div key={event.thinking_id || index} className={`p-3 rounded-lg border transition-opacity ${
                      isCompleted
                        ? 'bg-yellow-50 border-yellow-200 opacity-60'
                        : 'bg-yellow-50 border-yellow-300 animate-pulse'
                    }`}>
                      <div className="flex items-center space-x-2 text-sm text-yellow-800">
                        {isCompleted ? (
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                        )}
                        <span className="font-medium">
                          {isCompleted ? '✓ 已完成思考' : '💭 深度思考中...'}
                        </span>
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
                  const isPending = event.status === 'pending';
                  const isSuccess = event.status === 'success';

                  return (
                    <div key={event.tool_id || index} className={`p-3 rounded-lg border transition-opacity ${
                      isPending
                        ? 'bg-blue-50 border-blue-300 animate-pulse'
                        : isSuccess
                        ? 'bg-green-50 border-green-200 opacity-60'
                        : 'bg-red-50 border-red-200'
                    }`}>
                      <div className="flex items-center space-x-2 mb-2">
                        {isPending ? (
                          <svg className="w-4 h-4 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                        ) : isSuccess ? (
                          <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                        )}
                        <span className="text-sm font-medium">
                          {isPending && '⚙️ 正在调用'}
                          {isSuccess && '✓ 调用成功'}
                          {event.status === 'error' && '✗ 调用失败'}
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
              })}
            </div>
          )}


          {/* 流式内容 */}
          {message.content && (
            <div className="rounded-lg px-4 py-3 bg-white border border-gray-200 text-gray-900">
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
                    {message.content}
                  </ReactMarkdown>
              </div>

              {/* 光标动画 */}
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 bg-gray-900 ml-1 animate-pulse"></span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

