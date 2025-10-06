'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';
import { apiClient } from '@/lib/api';
import SessionSidebar from '@/components/chat/SessionSidebar';
import MessageList from '@/components/chat/MessageList';
import MessageInput from '@/components/chat/MessageInput';
import ModelSelector from '@/components/chat/ModelSelector';

export default function ChatPage() {
  const router = useRouter();
  const { isAuthenticated, _hasHydrated } = useAuthStore();
  const {
    status,
    error,
    currentSession,
    connect,
    disconnect,
    loadModels,
    loadSessions,
    createSession
  } = useChatStore();

  const [isInitialized, setIsInitialized] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // ✅ 所有 Hooks 必须在条件 return 之前调用
  useEffect(() => {
    // 只有在已水合且已认证的情况下才初始化
    if (!_hasHydrated || !isAuthenticated) return;
    if (isInitialized) return;

    const initChat = async () => {
      try {
        // ✅ 确保 token 有效（自动刷新机制）
        const token = await apiClient.ensureValidToken();
        if (!token) {
          router.push('/login');
          return;
        }

        // 连接 WebSocket
        await connect(token);

        // 加载模型和会话列表
        await Promise.all([loadModels(), loadSessions()]);

        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize chat', error);
      }
    };

    initChat();

    // 清理函数
    return () => {
      if (isInitialized) {
        disconnect();
      }
    };
  }, [_hasHydrated, isAuthenticated, isInitialized, connect, disconnect, loadModels, loadSessions, router]);

  // 创建新会话
  const handleNewChat = async () => {
    try {
      await createSession();
    } catch (error) {
      console.error('Failed to create session', error);
    }
  };

  // ✅ 条件渲染放在所有 Hooks 之后
  // 等待水合完成
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

  // 水合完成后，如果未登录则跳转
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
              <div className="text-center max-w-md px-4">
                <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-10 h-10 text-primary-600"
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
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  开始新对话
                </h2>
                <p className="text-gray-600 mb-6">
                  选择一个会话或创建新对话开始聊天
                </p>
                <button
                  onClick={handleNewChat}
                  className="btn-primary"
                >
                  创建新对话
                </button>
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
