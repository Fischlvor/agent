'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, _hasHydrated, setUser } = useAuthStore();

  // ✅ 所有 Hooks 必须在顶部调用（React 规则）
  const [loginMethod, setLoginMethod] = useState<'password' | 'email'>('password');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | React.ReactElement>('');
  const [sendingCode, setSendingCode] = useState(false);
  const [codeSent, setCodeSent] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // 密码登录表单
  const [passwordForm, setPasswordForm] = useState({
    login: '',
    password: '',
  });

  // 验证码登录表单
  const [emailForm, setEmailForm] = useState({
    email: '',
    code: '',
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

  // 密码登录
  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.loginWithPassword(passwordForm);
      setUser(response.user);
      router.push('/chat');
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || '登录失败，请检查用户名和密码';

      // 检查是否是邮箱未验证错误
      if (errorDetail.includes('邮箱未验证') || errorDetail.includes('未验证')) {
        setError(
          <div>
            {errorDetail}
            <br />
            <a
              href="/resend-verification"
              className="text-primary-600 hover:text-primary-700 font-medium underline mt-2 inline-block"
            >
              点击这里重新发送验证邮件
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

  // 发送验证码
  const handleSendCode = async () => {
    if (!emailForm.email) {
      setError('请输入邮箱地址');
      return;
    }

    setSendingCode(true);
    setError('');

    try {
      await apiClient.sendLoginCode(emailForm.email);
      setCodeSent(true);
      setCountdown(60);

      // 倒计时
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            setCodeSent(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || '发送验证码失败';

      // 检查是否是邮箱未验证错误
      if (errorDetail.includes('邮箱未验证') || errorDetail.includes('未验证')) {
        setError(
          <div>
            {errorDetail}
            <br />
            <a
              href={`/resend-verification?email=${encodeURIComponent(emailForm.email)}`}
              className="text-primary-600 hover:text-primary-700 font-medium underline mt-2 inline-block"
            >
              点击这里重新发送验证邮件
            </a>
          </div>
        );
      } else {
        setError(errorDetail);
      }
    } finally {
      setSendingCode(false);
    }
  };

  // 验证码登录
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.loginWithEmailCode(emailForm);
      setUser(response.user);
      router.push('/chat');
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || '登录失败，请检查验证码';

      // 检查是否是邮箱未验证错误
      if (errorDetail.includes('邮箱未验证') || errorDetail.includes('未验证')) {
        setError(
          <div>
            {errorDetail}
            <br />
            <a
              href={`/resend-verification?email=${encodeURIComponent(emailForm.email)}`}
              className="text-primary-600 hover:text-primary-700 font-medium underline mt-2 inline-block"
            >
              点击这里重新发送验证邮件
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100">
      <div className="w-full max-w-md">
        <div className="card">
          {/* Logo和标题 */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">欢迎回来</h1>
            <p className="text-gray-600">登录到 Agent AI 平台</p>
          </div>

          {/* 登录方式切换 */}
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => {
                setLoginMethod('password');
                setError(''); // 清空错误提示
              }}
              className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
                loginMethod === 'password'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              密码登录
            </button>
            <button
              onClick={() => {
                setLoginMethod('email');
                setError(''); // 清空错误提示
              }}
              className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
                loginMethod === 'email'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              验证码登录
            </button>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* 密码登录表单 */}
          {loginMethod === 'password' && (
            <form onSubmit={handlePasswordLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  用户名或邮箱
                </label>
                <input
                  type="text"
                  value={passwordForm.login}
                  onChange={(e) => setPasswordForm({ ...passwordForm, login: e.target.value })}
                  className="input-field"
                  placeholder="请输入用户名或邮箱"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  密码
                </label>
                <input
                  type="password"
                  value={passwordForm.password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, password: e.target.value })}
                  className="input-field"
                  placeholder="请输入密码"
                  required
                />
              </div>

              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-gray-600">记住我</span>
                </label>
                <a href="#" className="text-primary-600 hover:text-primary-700">
                  忘记密码？
                </a>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary"
              >
                {loading ? '登录中...' : '登录'}
              </button>
            </form>
          )}

          {/* 验证码登录表单 */}
          {loginMethod === 'email' && (
            <form onSubmit={handleEmailLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  邮箱地址
                </label>
                <input
                  type="email"
                  value={emailForm.email}
                  onChange={(e) => setEmailForm({ ...emailForm, email: e.target.value })}
                  className="input-field"
                  placeholder="请输入邮箱地址"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  验证码
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={emailForm.code}
                    onChange={(e) => setEmailForm({ ...emailForm, code: e.target.value })}
                    className="input-field flex-1"
                    placeholder="请输入6位验证码"
                    maxLength={6}
                    required
                  />
                  <button
                    type="button"
                    onClick={handleSendCode}
                    disabled={sendingCode || codeSent}
                    className="btn-secondary whitespace-nowrap"
                  >
                    {sendingCode ? '发送中...' : codeSent ? `${countdown}秒` : '发送验证码'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary"
              >
                {loading ? '登录中...' : '登录'}
              </button>
            </form>
          )}

          {/* 注册链接 */}
          <div className="mt-6 text-center space-y-2">
            <div className="text-sm text-gray-600">
              还没有账号？
              <a href="/register" className="text-primary-600 hover:text-primary-700 font-medium ml-1">
                立即注册
              </a>
            </div>
            <div className="text-sm text-gray-600">
              未收到验证邮件？
              <a href="/resend-verification" className="text-primary-600 hover:text-primary-700 font-medium ml-1">
                重新发送
              </a>
            </div>
          </div>
        </div>

        {/* 底部信息 */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>登录即表示同意我们的服务条款和隐私政策</p>
        </div>
      </div>
    </div>
  );
}

