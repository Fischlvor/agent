export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  role: 'user' | 'admin';
  is_active: boolean;
  is_verified: boolean;
  last_login_at: string | null;
  login_count: number;
  preferences: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type?: string;
  expires_in: number;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
  email: string;
}

export interface VerifyEmailResponse {
  message: string;
  user_id: string;
}

export interface LoginRequest {
  login: string;
  password: string;
}

export interface EmailCodeLoginRequest {
  email: string;
  code: string;
}

