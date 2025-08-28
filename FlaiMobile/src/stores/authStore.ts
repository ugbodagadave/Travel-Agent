import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthState, User, DeviceInfo } from '../types';
import { StorageService, DeviceUtils } from '../utils';
import { STORAGE_KEYS } from '../constants';

interface AuthStore extends AuthState {
  // Actions
  setUser: (user: User) => void;
  setTokens: (token: string, refreshToken: string) => void;
  logout: () => void;
  register: (deviceInfo?: Partial<DeviceInfo>) => Promise<void>;
  login: (email?: string, phone?: string) => Promise<void>;
  refreshAuth: () => Promise<void>;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      setUser: (user: User) => {
        set({ user, isAuthenticated: true });
      },

      setTokens: async (token: string, refreshToken: string) => {
        await StorageService.setSecure(STORAGE_KEYS.authToken, token);
        await StorageService.setSecure(STORAGE_KEYS.refreshToken, refreshToken);
        set({ token, refreshToken, isAuthenticated: true });
      },

      logout: async () => {
        await StorageService.removeSecure(STORAGE_KEYS.authToken);
        await StorageService.removeSecure(STORAGE_KEYS.refreshToken);
        await StorageService.removeItem(STORAGE_KEYS.userId);
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      register: async (deviceInfo?: Partial<DeviceInfo>) => {
        set({ isLoading: true });
        try {
          const fullDeviceInfo = {
            ...DeviceUtils.getDeviceInfo(),
            ...deviceInfo,
          };

          // TODO: Implement actual API call
          // const response = await AuthService.register(fullDeviceInfo);
          
          // Mock response for now
          const mockResponse = {
            user_id: `mobile:${DeviceUtils.generateDeviceId()}`,
            jwt: 'mock_jwt_token',
            refresh_token: 'mock_refresh_token',
          };

          const user: User = {
            id: mockResponse.user_id,
          };

          await get().setTokens(mockResponse.jwt, mockResponse.refresh_token);
          get().setUser(user);
        } catch (error) {
          console.error('Registration failed:', error);
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      login: async (email?: string, phone?: string) => {
        set({ isLoading: true });
        try {
          // TODO: Implement actual API call
          // const response = await AuthService.login({ email, phone });
          
          // Mock response for now
          const mockResponse = {
            user_id: `mobile:${email || phone || 'guest'}`,
            jwt: 'mock_jwt_token',
          };

          const user: User = {
            id: mockResponse.user_id,
            email,
            phone,
          };

          await StorageService.setSecure(STORAGE_KEYS.authToken, mockResponse.jwt);
          set({ token: mockResponse.jwt });
          get().setUser(user);
        } catch (error) {
          console.error('Login failed:', error);
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      refreshAuth: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          // TODO: Implement actual API call to refresh token
          // const response = await AuthService.refreshToken(refreshToken);
          
          // Mock response for now
          const mockResponse = {
            jwt: 'new_mock_jwt_token',
            refresh_token: 'new_mock_refresh_token',
          };

          await get().setTokens(mockResponse.jwt, mockResponse.refresh_token);
        } catch (error) {
          console.error('Token refresh failed:', error);
          await get().logout();
          throw error;
        }
      },

      initializeAuth: async () => {
        set({ isLoading: true });
        try {
          const token = await StorageService.getSecure(STORAGE_KEYS.authToken);
          const refreshToken = await StorageService.getSecure(STORAGE_KEYS.refreshToken);
          const userId = await StorageService.getItem(STORAGE_KEYS.userId);

          if (token && userId) {
            const user: User = { id: userId };
            set({
              user,
              token,
              refreshToken,
              isAuthenticated: true,
            });
          }
        } catch (error) {
          console.error('Auth initialization failed:', error);
          await get().logout();
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);