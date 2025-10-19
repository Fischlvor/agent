'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useChatStore } from '@/store/chatStore';
import type { ChatSession } from '@/types/chat';
import { BookOpenIcon } from '@heroicons/react/24/outline';
import UserMenu from './UserMenu';

interface SessionSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  currentSessionId?: string | null;
}

export default function SessionSidebar({ isOpen, onToggle, onNewChat, currentSessionId }: SessionSidebarProps) {
  const router = useRouter();
  const { sessions, selectSession, deleteSession, updateSessionTitle } = useChatStore();
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const handleSelectSession = (sessionId: string) => {
    // 跳转到会话详情页
    router.push(`/chat/${sessionId}`);
  };

  const handleStartEdit = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.session_id || session.id);
    setEditingTitle(session.title || '');
  };

  const handleSaveEdit = async (sessionId: string) => {
    if (editingTitle.trim()) {
      await updateSessionTitle(sessionId, editingTitle.trim());
    }
    setEditingSessionId(null);
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('确定要删除这个会话吗？')) {
      // ✅ 检查是否删除的是当前会话
      const isDeletingCurrentSession = currentSessionId === sessionId;

      // ✅ 如果删除的是当前会话，先跳转
      if (isDeletingCurrentSession) {
        router.push('/chat');
      }

      // ✅ 立即调用删除（store 会设置 deletingSessionId 标记，会话页面会检测并跳过加载）
      await deleteSession(sessionId);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* 头部 */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          {/* 用户头像 */}
          <UserMenu />

          {/* 新建对话按钮 */}
          <button
            onClick={onNewChat}
            className="flex-1 btn-primary flex items-center justify-center space-x-2"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            <span>新建对话</span>
          </button>
        </div>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <svg
              className="w-12 h-12 mx-auto mb-2 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="text-sm">暂无对话</p>
          </div>
        ) : (
          <div className="py-2">
            {sessions.map((session) => (
              <div
                key={session.session_id || session.id}
                onClick={() => handleSelectSession(session.session_id || session.id)}
                className={`
                  px-4 py-3 cursor-pointer transition-colors relative group
                  ${currentSessionId === (session.session_id || session.id)
                    ? 'bg-primary-50 border-l-4 border-primary-500'
                    : 'hover:bg-gray-50 border-l-4 border-transparent'
                  }
                `}
              >
                {editingSessionId === (session.session_id || session.id) ? (
                  <div onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onBlur={() => handleSaveEdit(session.session_id || session.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleSaveEdit(session.session_id || session.id);
                        } else if (e.key === 'Escape') {
                          handleCancelEdit();
                        }
                      }}
                      className="input w-full text-sm"
                      autoFocus
                    />
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-gray-900 truncate text-sm mb-1">
                            {session.title || '新对话'}
                          </h3>
                          {/* ✅ 新消息角标 */}
                          {session.hasNewMessage && (
                            <span className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full"></span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span>{session.message_count} 条消息</span>
                          <span>•</span>
                          <span>{formatDate(session.last_activity_at || session.created_at)}</span>
                        </div>
                      </div>

                      {/* 操作按钮 */}
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1 ml-2">
                        <button
                          onClick={(e) => handleStartEdit(session, e)}
                          className="p-1 rounded hover:bg-gray-200 transition-colors"
                          title="重命名"
                        >
                          <svg
                            className="w-4 h-4 text-gray-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => handleDelete(session.session_id || session.id, e)}
                          className="p-1 rounded hover:bg-red-100 transition-colors"
                          title="删除"
                        >
                          <svg
                            className="w-4 h-4 text-red-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>

                    {session.is_pinned && (
                      <div className="mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          置顶
                        </span>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部 - 知识库管理入口 */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={() => router.push('/knowledge-bases')}
          className="w-full flex items-center justify-center space-x-2 px-4 py-3 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <BookOpenIcon className="w-5 h-5" />
          <span className="font-medium">知识库管理</span>
        </button>
      </div>
    </div>
  );
}

