'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiClient } from '@/lib/api';

export default function ResendVerificationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailParam = searchParams.get('email') || '';

  const [email, setEmail] = useState(emailParam);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!email.trim()) {
      setError('请输入邮箱地址');
      setLoading(false);
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('邮箱格式不正确');
      setLoading(false);
      return;
    }

    try {
      await apiClient.resendVerificationEmail(email);
      setSuccess(true);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        '发送失败，请检查邮箱地址或稍后重试'
      );
    } finally {
      setLoading(false);
    }
  };

  // 发送成功页面
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="w-full max-w-md">
          <div className="card text-center">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">验证邮件已发送！</h1>
              <p className="text-gray-600">
                新的验证邮件已发送到
                <br />
                <span className="font-medium text-primary-600">{email}</span>
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-medium text-blue-900 mb-2">请注意：</h3>
              <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
                <li>验证链接有效期为 24 小时</li>
                <li>请检查垃圾邮件文件夹</li>
                <li>旧的验证链接将失效</li>
              </ul>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => router.push('/login')}
                className="w-full btn-primary"
              >
                返回登录
              </button>
              <button
                onClick={() => setSuccess(false)}
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                再次发送
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 表单页面
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
      <div className="w-full max-w-md">
        <div className="card">
          {/* 标题 */}
          <div className="text-center mb-6">
            <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">重新发送验证邮件</h1>
            <p className="text-gray-600">输入您注册时使用的邮箱地址</p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* 提示信息 */}
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="font-medium text-yellow-900 mb-2 flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              什么情况下需要重新发送？
            </h3>
            <ul className="list-disc list-inside text-sm text-yellow-800 space-y-1">
              <li>验证链接已过期</li>
              <li>没有收到验证邮件</li>
              <li>邮件被误删除</li>
              <li>注册后无法登录（未验证）</li>
            </ul>
          </div>

          {/* 表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                邮箱地址 <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="your@email.com"
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary"
            >
              {loading ? '发送中...' : '发送验证邮件'}
            </button>
          </form>

          {/* 底部链接 */}
          <div className="mt-6 text-center space-y-2">
            <div className="text-sm text-gray-600">
              已经验证了？
              <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium ml-1">
                立即登录
              </a>
            </div>
            <div className="text-sm text-gray-600">
              还没有账号？
              <a href="/register" className="text-primary-600 hover:text-primary-700 font-medium ml-1">
                立即注册
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

