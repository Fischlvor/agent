'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';
import { apiClient } from '@/lib/api';
import SessionSidebar from '@/components/chat/SessionSidebar';
import WelcomeScreen from '@/components/chat/WelcomeScreen';

export default function ChatPage() {
  const router = useRouter();
  const { isAuthenticated, _hasHydrated } = useAuthStore();
  const {
    isInitialized,
    initialize,
    createSession,
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

  // ✅ 处理发送消息（创建会话 + 保存消息 + 跳转）
  const handleSendMessage = async (content: string) => {
    try {
      // 1. 创建新会话
      const newSession = await createSession();

      if (!newSession || !newSession.session_id) {
        throw new Error('Failed to create session');
      }

      // 2. 保存待发送的消息
      setPendingMessage(content);

      // 3. 跳转到会话详情页（selectSession 会自动检测并发送）
      router.push(`/chat/${newSession.session_id}`);
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
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
        onNewChat={() => router.push('/chat')}
        currentSessionId={null}
      />

      {/* 欢迎界面 */}
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

            <h1 className="text-lg font-semibold text-gray-800">新对话</h1>
          </div>
        </div>

        {/* 欢迎界面 */}
        <WelcomeScreen onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
}
