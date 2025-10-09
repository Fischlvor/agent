'use client';

import { useEffect, useRef, useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import MessageItem from './MessageItem';
import StreamingMessageItem from './StreamingMessageItem';

export default function MessageList() {
  const { messages, streamingMessage, status, currentSession } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [userScrolledUp, setUserScrolledUp] = useState(false); // 用户是否主动向上滚动
  const prevSessionIdRef = useRef<string | null>(null);
  const prevMessagesLengthRef = useRef(0);
  const prevScrollTopRef = useRef(0); // 记录上一次的 scrollTop
  const prevStatusRef = useRef(status);

  // ✅ 只显示当前会话的流式消息
  const shouldShowStreaming = streamingMessage && currentSession &&
    streamingMessage.session_id === (currentSession.session_id || currentSession.id);

  // ✅ 强制滚动到底部（立即滚动，用于切换会话和发送消息）
  const forceScrollToBottom = () => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
    setUserScrolledUp(false); // 重置用户滚动状态
  };

  // ✅ 智能滚动：只有用户未主动向上滚动时才自动滚动
  const smartScrollToBottom = () => {
    if (!containerRef.current) return;
    if (userScrolledUp) {
      console.log('[滚动] 用户已向上滚动，停止自动滚动');
      return;
    }
    // 使用 scrollTop 直接滚动，比 scrollIntoView 更可靠
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  };

  // ✅ 监听用户滚动行为（检测向上滚动）
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50; // 距离底部 50px 内算是在底部

      if (isAtBottom) {
        // 用户滚动到底部，重置状态
        if (userScrolledUp) {
          console.log('[滚动] 用户滚回底部，恢复自动滚动');
        }
        setUserScrolledUp(false);
      } else if (status === 'generating') {
        // ✅ 只在生成过程中，且 scrollTop 减小（向上滚动）时，才标记
        if (scrollTop < prevScrollTopRef.current) {
          console.log('[滚动] 检测到用户向上滚动，停止自动滚动');
          setUserScrolledUp(true);
        }
      }

      prevScrollTopRef.current = scrollTop;
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [status]);

  // ✅ 生成开始时，重置滚动状态
  useEffect(() => {
    if (status === 'generating' && prevStatusRef.current !== 'generating') {
      console.log('[滚动] 生成开始，重置为跟随滚动模式');
      setUserScrolledUp(false); // 生成开始时，重置为跟随滚动
    }
    prevStatusRef.current = status;
  }, [status]);

  // ✅ 场景1：切换会话时，强制滚动到底部
  useEffect(() => {
    const currentSessionId = currentSession?.session_id || currentSession?.id;
    if (currentSessionId && currentSessionId !== prevSessionIdRef.current) {
      prevSessionIdRef.current = currentSessionId;
      forceScrollToBottom();
    }
  }, [currentSession]);

  // ✅ 场景2：发送新消息时（messages数组增加），强制滚动到底部
  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      const lastMessage = messages[messages.length - 1];
      // 如果是用户消息，强制滚动
      if (lastMessage?.role === 'user') {
        forceScrollToBottom();
      }
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages]);

  // ✅ 场景3：流式生成时，智能滚动（尊重用户向上滚动的行为）
  useEffect(() => {
    if (shouldShowStreaming && streamingMessage) {
      smartScrollToBottom();
    }
  }, [streamingMessage, shouldShowStreaming, userScrolledUp]);

  return (
    <div
      ref={containerRef}
      className="h-full overflow-y-auto px-4 py-6 space-y-6"
    >
      {messages.length === 0 && !shouldShowStreaming && (
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

      {/* ✅ 只显示属于当前会话的流式消息 */}
      {shouldShowStreaming && (
        <StreamingMessageItem message={streamingMessage} />
      )}

      {/* 加载指示器 */}
      {status === 'generating' && !shouldShowStreaming && (
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

