'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { UserCircleIcon, ArrowRightOnRectangleIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

export default function UserMenu() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  // 获取用户名首字母作为头像
  const getInitial = () => {
    if (!user?.username) return '?';
    return user.username.charAt(0).toUpperCase();
  };

  // 生成头像背景色（基于用户名）
  const getAvatarColor = () => {
    if (!user?.username) return 'bg-gray-400';
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-red-500',
      'bg-yellow-500',
      'bg-teal-500',
    ];
    const index = user.username.charCodeAt(0) % colors.length;
    return colors[index];
  };

  return (
    <div className="relative" ref={menuRef}>
      {/* 用户头像按钮 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-10 h-10 rounded-full ${getAvatarColor()} flex items-center justify-center text-white font-semibold hover:opacity-80 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2`}
        title={user?.username || '用户'}
      >
        {getInitial()}
      </button>

      {/* 下拉菜单 */}
      {isOpen && (
        <div className="absolute left-0 top-12 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
          {/* 用户信息 */}
          <div className="px-4 py-3 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className={`w-12 h-12 rounded-full ${getAvatarColor()} flex items-center justify-center text-white font-bold text-lg flex-shrink-0`}>
                {getInitial()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {user?.username || '未知用户'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.email || '无邮箱'}
                </p>
              </div>
            </div>
          </div>

          {/* 菜单项 */}
          <div className="py-1">
            {/* 个人信息 */}
            <button
              onClick={() => {
                setIsOpen(false);
                // TODO: 跳转到个人信息页面
                console.log('查看个人信息');
              }}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-3 transition-colors"
            >
              <UserCircleIcon className="w-5 h-5 text-gray-500" />
              <span>个人信息</span>
            </button>

            {/* 设置 */}
            <button
              onClick={() => {
                setIsOpen(false);
                // TODO: 跳转到设置页面
                console.log('打开设置');
              }}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-3 transition-colors"
            >
              <Cog6ToothIcon className="w-5 h-5 text-gray-500" />
              <span>设置</span>
            </button>
          </div>

          {/* 分隔线 */}
          <div className="border-t border-gray-200 my-1"></div>

          {/* 退出登录 */}
          <button
            onClick={handleLogout}
            className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center space-x-3 transition-colors"
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5" />
            <span>退出登录</span>
          </button>
        </div>
      )}
    </div>
  );
}

