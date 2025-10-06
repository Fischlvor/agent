'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [message, setMessage] = useState('');
  const [countdown, setCountdown] = useState(5);

  // 使用 Zustand 状态管理防止重复请求
  const { hasTokenBeenVerified, markTokenAsVerified } = useAuthStore();

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setMessage('缺少验证令牌，请检查邮件链接是否完整');
      return;
    }

    // 检查此 token 是否已验证过（防止 React 18 严格模式重复请求）
    if (hasTokenBeenVerified(token)) {
      return;
    }

    // 标记为已验证
    markTokenAsVerified(token);

    // 调用验证API
    const verifyToken = async () => {
      try {
        const response = await apiClient.verifyEmail(token);
        setStatus('success');
        setMessage(response.message || '邮箱验证成功！');

        // 5秒后自动跳转到登录页
        let count = 5;
        const timer = setInterval(() => {
          count--;
          setCountdown(count);
          if (count <= 0) {
            clearInterval(timer);
            router.push('/login');
          }
        }, 1000);

        return () => clearInterval(timer);
      } catch (error: any) {
        const errorDetail = error.response?.data?.detail || '验证失败，令牌可能已过期或无效';

        // 检查是否是"已验证"的错误
        if (errorDetail.includes('已经验证') || errorDetail.includes('已验证')) {
          setStatus('success');
          setMessage('您的邮箱已经验证过了，请直接登录');

          // 5秒后自动跳转到登录页
          let count = 5;
          const timer = setInterval(() => {
            count--;
            setCountdown(count);
            if (count <= 0) {
              clearInterval(timer);
              router.push('/login');
            }
          }, 1000);
        } else {
          setStatus('error');
          setMessage(errorDetail);
        }
      }
    };

    verifyToken();
  }, [searchParams, router]);

  // 验证中状态
  if (status === 'verifying') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="w-full max-w-md">
          <div className="card text-center">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4 animate-pulse">
                <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">正在验证邮箱...</h1>
              <p className="text-gray-600">请稍候</p>
            </div>

            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 验证成功状态
  if (status === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100">
        <div className="w-full max-w-md">
          <div className="card text-center">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4 animate-bounce">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">验证成功！</h1>
              <p className="text-gray-600 mb-4">{message}</p>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <p className="text-green-800 text-sm">
                您的账号已激活，现在可以登录使用了
              </p>
            </div>

            <div className="mb-4 text-gray-500 text-sm">
              {countdown} 秒后自动跳转到登录页...
            </div>

            <button
              onClick={() => router.push('/login')}
              className="w-full btn-primary"
            >
              立即登录
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 验证失败状态
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-rose-100">
      <div className="w-full max-w-md">
        <div className="card text-center">
          <div className="mb-6">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">验证失败</h1>
            <p className="text-gray-600 mb-4">{message}</p>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-medium text-red-900 mb-2">可能的原因：</h3>
            <ul className="list-disc list-inside text-sm text-red-800 space-y-1">
              <li>验证链接已过期（有效期24小时）</li>
              <li>验证链接已被使用</li>
              <li>链接不完整或已损坏</li>
            </ul>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => router.push('/resend-verification')}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              重新发送验证邮件
            </button>
            <button
              onClick={() => router.push('/login')}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
              返回登录
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

