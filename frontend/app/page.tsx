'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { apiClient } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const { setUser, hasInitialized, markAsInitialized } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // ✅ 调用函数检查，函数内部会读取 store 的最新值
    if (hasInitialized()) {
      return;
    }

    // ✅ 立即标记
    markAsInitialized();

    const initAuth = async () => {
      // 检查 localStorage 中是否有 access token
      const token = apiClient.getToken();

      if (token) {
        // 如果有 token，尝试获取用户信息
        try {
          const userData = await apiClient.getCurrentUser();
          setUser(userData);
          // 登录成功，跳转到聊天页面
          router.push('/chat');
        } catch (error) {
          // Token 无效或已过期，清除 token
          apiClient.removeToken();
          router.push('/login');
        }
      } else {
        // 没有 token，跳转到登录页面
        router.push('/login');
      }

      setIsLoading(false);
    };

    initAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 空依赖数组，只在组件挂载时执行（Strict Mode 会执行两次，但 useRef 会防止）

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">加载中...</p>
      </div>
    </div>
  );
}

