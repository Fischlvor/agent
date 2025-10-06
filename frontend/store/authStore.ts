import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User } from '@/types/user';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  _isInitialized: boolean; // 内部状态（不要直接从 hook 读取）
  _hasHydrated: boolean; // 🆕 标记 persist 是否已完成水合
  verifiedTokens: Set<string>; // 记录已验证的 token，防止重复请求
  setUser: (user: User | null) => void;
  logout: () => void;
  markAsInitialized: () => void;
  hasInitialized: () => boolean; // ✅ 改成函数，每次调用都读取最新值
  markTokenAsVerified: (token: string) => void;
  hasTokenBeenVerified: (token: string) => boolean;
  setHasHydrated: (state: boolean) => void; // 🆕 设置水合状态
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      _isInitialized: false, // 内部状态
      _hasHydrated: false, // 初始未水合
      verifiedTokens: new Set(),

      setUser: (user) => set({ user, isAuthenticated: !!user }),

      logout: () => set({ user: null, isAuthenticated: false }),

      markAsInitialized: () => set({ _isInitialized: true }),

      hasInitialized: () => get()._isInitialized, // ✅ 函数形式，每次调用都读取最新值

      markTokenAsVerified: (token) => set((state) => {
        const newTokens = new Set(state.verifiedTokens);
        newTokens.add(token);
        return { verifiedTokens: newTokens };
      }),

      hasTokenBeenVerified: (token) => get().verifiedTokens.has(token),

      setHasHydrated: (state) => set({ _hasHydrated: state }), // 🆕
    }),
    {
      name: 'auth-storage', // localStorage key
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        // ✅ 只持久化这两个关键状态，其他状态不持久化
      }),
      onRehydrateStorage: () => (state) => {
        // 🆕 水合完成后的回调
        state?.setHasHydrated(true);
      },
    }
  )
);

