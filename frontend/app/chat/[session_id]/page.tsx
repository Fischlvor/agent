'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';
import { apiClient } from '@/lib/api';
import SessionSidebar from '@/components/chat/SessionSidebar';
import MessageList from '@/components/chat/MessageList';
import MessageInput from '@/components/chat/MessageInput';
import ModelSelector from '@/components/chat/ModelSelector';
import ContextProgress from '@/components/chat/ContextProgress';

export default function ChatSessionPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params?.session_id as string;

  const { isAuthenticated, _hasHydrated } = useAuthStore();
  const {
    status,
    error,
    currentSession,
    pendingMessage,
    deletingSessionId,
    isInitialized,
    initialize,
    disconnect,
    selectSession,
    sendMessage,
    setPendingMessage
  } = useChatStore();

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // ✅ 初始化聊天（全局只初始化一次）
  useEffect(() => {
    if (!_hasHydrated || !isAuthenticated) return;
    if (isInitialized) return;

    const initChat = async () => {
      try {
        const token = await apiClient.ensureValidToken();
        if (!token) {
          router.push('/login');
          return;
        }

        // ✅ 使用全局初始化方法，避免重复初始化
        await initialize(token);
      } catch (error) {
        console.error('Failed to initialize chat', error);
      }
    };

    initChat();
  }, [_hasHydrated, isAuthenticated, isInitialized, initialize, router]);

  // ✅ 加载指定会话
  useEffect(() => {
    if (!isInitialized || !sessionId) return;

    // ✅ 如果当前会话正在被删除，不要尝试加载（避免404请求）
    if (deletingSessionId === sessionId) {
      console.log('[ChatSessionPage] 当前会话正在被删除，跳过加载');
      return;
    }

    // 如果当前会话不是要显示的会话，切换到指定会话
    if (currentSession?.session_id !== sessionId && currentSession?.id !== sessionId) {
      const loadSession = async () => {
        try {
          await selectSession(sessionId); // selectSession 会自动检测并发送 pendingMessage
        } catch (error) {
          // ✅ 加载会话失败（404等），跳转到欢迎界面
          console.error('会话加载失败，跳转到欢迎界面:', error);
          router.push('/chat');
        }
      };
      loadSession();
    }
  }, [isInitialized, sessionId, currentSession, deletingSessionId, selectSession, router]);

  // ✅ 处理待发送消息（针对从欢迎页面创建会话的情况）
  useEffect(() => {
    if (!pendingMessage) return;
    if (!currentSession) return;
    if (currentSession.session_id !== sessionId && currentSession.id !== sessionId) return;
    if (status !== 'connected') return;

    console.log('[ChatSessionPage] 检测到待发送消息，准备发送');

    // 延迟一点确保页面渲染完成
    const timer = setTimeout(() => {
      setPendingMessage(null); // 清空待发送消息
      sendMessage(pendingMessage);
    }, 300);

    return () => clearTimeout(timer);
  }, [pendingMessage, currentSession, sessionId, status, sendMessage, setPendingMessage]);

  // ✅ 检测会话是否加载失败（error 状态且没有 currentSession）
  useEffect(() => {
    if (!isInitialized) return;

    // 如果有错误且没有当前会话，跳转到欢迎界面
    if (error && !currentSession) {
      console.error('会话状态错误，跳转到欢迎界面:', error);
      router.push('/chat');
    }
  }, [isInitialized, error, currentSession, router]);

  // 新建对话（返回欢迎界面）
  const handleNewChat = () => {
    router.push('/chat');
  };

  // 等待水合
  if (!_hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  // 未登录跳转
  if (!isAuthenticated) {
    router.push('/login');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">跳转中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      {/* 会话侧边栏 */}
      <SessionSidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChat={handleNewChat}
        currentSessionId={sessionId}
      />

      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部工具栏 */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {/* 侧边栏切换按钮 */}
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>

            {/* 会话标题 */}
            <h1 className="text-lg font-semibold text-gray-800">
              {currentSession?.title || '新对话'}
            </h1>

            {/* 上下文使用进度 */}
            {currentSession?.current_context_tokens !== undefined && currentSession?.max_context_tokens !== undefined && (
              <ContextProgress
                currentTokens={currentSession.current_context_tokens}
                maxTokens={currentSession.max_context_tokens}
              />
            )}
          </div>

          {/* 模型选择器 */}
          <ModelSelector />
        </div>

        {/* 连接状态提示 */}
        {status === 'connecting' && (
          <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800">
            正在连接...
          </div>
        )}
        {status === 'error' && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-800">
            连接错误: {error}
          </div>
        )}

        {/* 消息列表 */}
        <div className="flex-1 overflow-hidden">
          {currentSession ? (
            <MessageList />
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">加载会话...</p>
              </div>
            </div>
          )}
        </div>

        {/* 消息输入框 */}
        {currentSession && <MessageInput />}
      </div>
    </div>
  );
}

