'use client';

import { useEffect, useRef } from 'react';
import { useChatStore } from '@/store/chatStore';
import MessageItem from './MessageItem';
import StreamingMessageItem from './StreamingMessageItem';

export default function MessageList() {
  const { messages, streamingMessage, status } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // ✅ 智能滚动：只有用户在底部时才自动滚动
  const scrollToBottom = () => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 150; // 距离底部 150px 内

    // 只有在底部附近才自动滚动
    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  return (
    <div
      ref={containerRef}
      className="h-full overflow-y-auto px-4 py-6 space-y-6"
    >
      {messages.length === 0 && !streamingMessage && (
        <div className="h-full flex items-center justify-center">
          <div className="text-center max-w-2xl px-4">
            <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              准备好开始对话了！
            </h3>
            <p className="text-gray-600">
              输入您的问题，我会尽力帮您解答
            </p>
          </div>
        </div>
      )}

      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {streamingMessage && (
        <StreamingMessageItem message={streamingMessage} />
      )}

      {/* 加载指示器 */}
      {status === 'generating' && !streamingMessage && (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
          <span className="text-sm">AI 正在思考...</span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}

