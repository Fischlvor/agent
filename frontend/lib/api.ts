import axios, { AxiosInstance } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  EmailCodeLoginRequest,
  RegisterRequest,
  RegisterResponse,
  VerifyEmailResponse,
  RefreshTokenResponse
} from '@/types/user';
import type {
  AIModel,
  ChatSession,
  ChatMessage,
  CreateSessionRequest,
  UpdateSessionRequest,
  SessionListResponse,
  UpdateMessageRequest
} from '@/types/chat';

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (reason?: any) => void;
  }> = [];

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // 支持Cookie（refresh_token）
    });

    // 请求拦截器：添加 Access Token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器：自动刷新 Token
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // 排除不需要自动刷新 token 的接口
        const noRetryUrls = [
          '/sso/auth/login/password',
          '/sso/auth/login/email-code',
          '/sso/auth/register',
          '/sso/auth/refresh',
          '/sso/auth/verify-email',
          '/sso/auth/send-login-code'
        ];

        const shouldSkipRefresh = noRetryUrls.some(url =>
          originalRequest.url?.includes(url)
        );

        // 如果是 401 错误且不是登录/注册等公开接口
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          !shouldSkipRefresh
        ) {
          // 如果正在刷新，将请求加入队列
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            })
              .then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return this.client(originalRequest);
              })
              .catch((err) => Promise.reject(err));
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // 调用刷新接口（refresh_token 在 Cookie 中自动发送）
            const response = await this.client.post<RefreshTokenResponse>('/sso/auth/refresh');
            const newAccessToken = response.data.access_token;

            // 保存新的 Access Token
            this.setToken(newAccessToken);

            // 处理队列中的请求
            this.processQueue(null, newAccessToken);

            // 重试原请求
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // 刷新失败，清空队列，跳转登录
            this.processQueue(refreshError, null);
            this.removeToken();
            if (typeof window !== 'undefined') {
              window.location.href = '/login';
            }
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // 处理请求队列
  private processQueue(error: any, token: string | null = null) {
    this.failedQueue.forEach((prom) => {
      if (error) {
        prom.reject(error);
      } else {
        prom.resolve(token);
      }
    });
    this.failedQueue = [];
  }

  // Token管理
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  }

  /**
   * 检查 JWT token 是否过期
   */
  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // 转换为毫秒
      const now = Date.now();
      // 提前 30 秒刷新，避免临界状态
      return exp - now < 30000;
    } catch (error) {
      return true; // 解析失败视为过期
    }
  }

  /**
   * 确保 Token 有效（如果过期会自动刷新）
   * 用于 WebSocket 连接前验证
   */
  async ensureValidToken(): Promise<string | null> {
    const token = this.getToken();
    if (!token) {
      return null;
    }

    // ✅ 先检查是否过期，未过期直接返回
    if (!this.isTokenExpired(token)) {
      return token;
    }

    // ✅ 已过期，发送请求触发自动刷新
    try {
      await this.getCurrentUser();
      return this.getToken();
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  }

  // 认证API
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await this.client.post<RegisterResponse>('/sso/auth/register', data);
    return response.data;
  }

  async verifyEmail(token: string): Promise<VerifyEmailResponse> {
    const response = await this.client.get<VerifyEmailResponse>(`/sso/auth/verify-email?token=${token}`);
    return response.data;
  }

  async resendVerificationEmail(email: string): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>('/sso/auth/resend-verification', { email });
    return response.data;
  }

  async loginWithPassword(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/sso/auth/login/password', data);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async loginWithEmailCode(data: EmailCodeLoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/sso/auth/login/email-code', data);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async sendLoginCode(email: string): Promise<void> {
    await this.client.post('/sso/auth/send-login-code', { email });
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/sso/auth/logout');
    } finally {
      this.removeToken();
    }
  }

  async getCurrentUser() {
    const response = await this.client.get('/users/me');
    return response.data;
  }

  // ============ 聊天 API ============

  // 模型管理
  async getModels(onlyActive: boolean = true): Promise<AIModel[]> {
    const response = await this.client.get<AIModel[]>('/chat/models', {
      params: { only_active: onlyActive }
    });
    return response.data;
  }

  // 会话管理
  async createSession(data: CreateSessionRequest): Promise<ChatSession> {
    const response = await this.client.post<ChatSession>('/chat/sessions', data);
    return response.data;
  }

  async getSessions(cursor?: string, limit: number = 20): Promise<SessionListResponse> {
    const response = await this.client.get<SessionListResponse>('/chat/sessions', {
      params: { cursor, limit }
    });
    return response.data;
  }

  async getSession(sessionId: string): Promise<ChatSession> {
    const response = await this.client.get<ChatSession>(`/chat/sessions/${sessionId}`);
    return response.data;
  }

  async updateSession(sessionId: string, data: UpdateSessionRequest): Promise<ChatSession> {
    const response = await this.client.patch<ChatSession>(`/chat/sessions/${sessionId}`, data);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/chat/sessions/${sessionId}`);
  }

  // 消息管理
  async getMessages(sessionId: string, limit: number = 50): Promise<{ messages: ChatMessage[]; total: number }> {
    const response = await this.client.get<{ messages: ChatMessage[]; total: number }>(
      `/chat/sessions/${sessionId}/messages`,
      { params: { limit } }
    );
    return response.data;
  }

  async updateMessage(messageId: string, data: UpdateMessageRequest): Promise<ChatMessage> {
    const response = await this.client.patch<ChatMessage>(`/chat/messages/${messageId}`, data);
    return response.data;
  }

  async deleteMessage(messageId: string): Promise<void> {
    await this.client.delete(`/chat/messages/${messageId}`);
  }
}

export const apiClient = new ApiClient();

