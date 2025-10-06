'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

export default function RegisterPage() {
  const router = useRouter();
  const { isAuthenticated, _hasHydrated } = useAuthStore();

  // ✅ 所有 Hooks 必须在顶部调用（React 规则）
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | React.ReactElement>('');
  const [success, setSuccess] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });

  const [errors, setErrors] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  // ✅ 如果已登录，自动跳转到聊天页面
  useEffect(() => {
    if (_hasHydrated && isAuthenticated) {
      router.push('/chat');
    }
  }, [_hasHydrated, isAuthenticated, router]);

  // ✅ 等待水合完成
  if (!_hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  // ✅ 水合完成后，如果已登录则跳转
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">跳转中...</p>
        </div>
      </div>
    );
  }

  // 表单验证
  const validateForm = () => {
    const newErrors = {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    };

    // 用户名验证
    if (!formData.username.trim()) {
      newErrors.username = '用户名不能为空';
    } else if (formData.username.length < 3) {
      newErrors.username = '用户名至少3个字符';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = '用户名只能包含字母、数字和下划线';
    }

    // 邮箱验证
    if (!formData.email.trim()) {
      newErrors.email = '邮箱不能为空';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '邮箱格式不正确';
    }

    // 密码验证
    if (!formData.password) {
      newErrors.password = '密码不能为空';
    } else if (formData.password.length < 6) {
      newErrors.password = '密码至少6个字符';
    }

    // 确认密码验证
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '请确认密码';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次密码输入不一致';
    }

    setErrors(newErrors);
    return !Object.values(newErrors).some(err => err !== '');
  };

  // 提交注册
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const response = await apiClient.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || undefined,
      });

      setRegisteredEmail(response.email);
      setSuccess(true);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || '注册失败，请稍后重试';

      // 检查是否是邮箱已存在的错误
      if (errorDetail.includes('邮箱已被注册') || errorDetail.includes('已注册')) {
        setError(
          <div>
            {errorDetail}
            <br />
            <a
              href={`/resend-verification?email=${encodeURIComponent(formData.email)}`}
              className="text-primary-600 hover:text-primary-700 font-medium underline mt-2 inline-block"
            >
              如果您未收到验证邮件或链接已过期，点击这里重新发送
            </a>
          </div>
        );
      } else {
        setError(errorDetail);
      }
    } finally {
      setLoading(false);
    }
  };

  // 注册成功页面
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="w-full max-w-md">
          <div className="card text-center">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">注册成功！</h1>
              <p className="text-gray-600">
                验证邮件已发送到
                <br />
                <span className="font-medium text-primary-600">{registeredEmail}</span>
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-medium text-blue-900 mb-2">下一步：</h3>
              <ol className="list-decimal list-inside text-sm text-blue-800 space-y-1">
                <li>检查您的邮箱（包括垃圾邮件文件夹）</li>
                <li>点击邮件中的验证链接</li>
                <li>验证完成后即可登录</li>
              </ol>
            </div>

            <button
              onClick={() => router.push('/login')}
              className="w-full btn-primary"
            >
              返回登录
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 注册表单
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 py-12">
      <div className="w-full max-w-md">
        <div className="card">
          {/* Logo和标题 */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">创建账号</h1>
            <p className="text-gray-600">加入 Agent AI 平台</p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* 注册表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                用户名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className={`input-field ${errors.username ? 'border-red-500' : ''}`}
                placeholder="字母、数字、下划线，至少3个字符"
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                邮箱地址 <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className={`input-field ${errors.email ? 'border-red-500' : ''}`}
                placeholder="your@email.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                密码 <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className={`input-field ${errors.password ? 'border-red-500' : ''}`}
                placeholder="至少6个字符"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                确认密码 <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                className={`input-field ${errors.confirmPassword ? 'border-red-500' : ''}`}
                placeholder="再次输入密码"
              />
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                姓名（可选）
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="input-field"
                placeholder="您的真实姓名"
              />
            </div>

            <div className="text-xs text-gray-500">
              注册即表示您同意我们的
              <a href="#" className="text-primary-600 hover:text-primary-700 mx-1">服务条款</a>
              和
              <a href="#" className="text-primary-600 hover:text-primary-700 mx-1">隐私政策</a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary"
            >
              {loading ? '注册中...' : '立即注册'}
            </button>
          </form>

          {/* 登录链接 */}
          <div className="mt-6 text-center text-sm text-gray-600">
            已有账号？
            <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium ml-1">
              立即登录
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
