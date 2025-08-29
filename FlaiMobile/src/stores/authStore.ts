import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthState, User } from '../types';
import { DeviceInfo } from '../types/auth';
import { StorageService } from '../utils';
import { STORAGE_KEYS } from '../constants';
import { AuthService } from '../services/auth';
import { DeviceRegistrationService } from '../services/deviceRegistration';

interface AuthStore extends AuthState {
  // Additional state
  error: string | null;
  deviceToken: string | null;
  
  // Actions
  setUser: (user: User) => void;
  setTokens: (token: string, refreshToken: string) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  logout: () => void;
  register: (deviceInfo?: Partial<DeviceInfo>) => Promise<void>;
  login: (email?: string, phone?: string) => Promise<void>;
  refreshAuth: () => Promise<void>;
  initializeAuth: () => Promise<void>;
  registerDevice: () => Promise<void>;
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
      error: null,
      deviceToken: null,

      // Actions
      setUser: (user: User) => {
        set({ user, isAuthenticated: true, error: null });
      },

      setTokens: async (token: string, refreshToken: string) => {
        await StorageService.setSecure(STORAGE_KEYS.authToken, token);
        await StorageService.setSecure(STORAGE_KEYS.refreshToken, refreshToken);
        set({ token, refreshToken, isAuthenticated: true, error: null });
      },

      setError: (error: string | null) => {
        set({ error, isLoading: false });
      },

      clearError: () => {
        set({ error: null });
      },

      logout: async () => {
        try {
          await AuthService.logout();
          await DeviceRegistrationService.clearRegistration();
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
            deviceToken: null,
          });
        } catch (error) {
          console.error('Logout error:', error);
          // Force logout even if there's an error
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
            deviceToken: null,
          });
        }
      },

      register: async (deviceInfo?: Partial<DeviceInfo>) => {
        set({ isLoading: true, error: null });
        try {
          console.log('AuthStore: Starting user registration...');
          
          // Register user with backend
          const response = await AuthService.register(deviceInfo);
          
          // Create user object
          const user: User = {
            id: response.user_id,
          };

          // Store tokens and user
          await get().setTokens(response.jwt, response.refresh_token);
          get().setUser(user);
          await StorageService.setItem(STORAGE_KEYS.userId, response.user_id);
          
          console.log('AuthStore: User registration successful');
          
          // Register device for push notifications
          try {
            await get().registerDevice();
          } catch (deviceError) {
            console.warn('Device registration failed, but user auth successful:', deviceError);
            // Don't fail the entire registration if device registration fails
          }
        } catch (error) {
          console.error('AuthStore: Registration failed:', error);
          const errorMessage = error instanceof Error ? error.message : 'Registration failed';
          get().setError(errorMessage);
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      login: async (email?: string, phone?: string) => {
        set({ isLoading: true, error: null });
        try {
          console.log('AuthStore: Starting user login...');
          
          // Login user with backend
          const response = await AuthService.login({ email, phone });
          
          // Create user object
          const user: User = {
            id: response.user_id,
            email,
            phone,
          };

          // Store tokens and user
          if (response.refresh_token) {
            await get().setTokens(response.jwt, response.refresh_token);
          } else {
            await StorageService.setSecure(STORAGE_KEYS.authToken, response.jwt);
            set({ token: response.jwt });
          }
          
          get().setUser(user);
          await StorageService.setItem(STORAGE_KEYS.userId, response.user_id);
          
          console.log('AuthStore: User login successful');
          
          // Register device for push notifications
          try {
            await get().registerDevice();
          } catch (deviceError) {
            console.warn('Device registration failed, but user auth successful:', deviceError);
            // Don't fail the entire login if device registration fails
          }
        } catch (error) {
          console.error('AuthStore: Login failed:', error);
          const errorMessage = error instanceof Error ? error.message : 'Login failed';
          get().setError(errorMessage);
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
          console.log('AuthStore: Refreshing authentication token...');
          
          const response = await AuthService.refreshToken(refreshToken);
          
          // Update stored tokens
          await get().setTokens(response.jwt, response.refresh_token);
          
          console.log('AuthStore: Token refresh successful');
        } catch (error) {
          console.error('AuthStore: Token refresh failed:', error);
          const errorMessage = error instanceof Error ? error.message : 'Token refresh failed';
          get().setError(errorMessage);
          
          // Logout user if refresh fails
          await get().logout();
          throw error;
        }
      },

      initializeAuth: async () => {
        set({ isLoading: true, error: null });
        try {
          console.log('AuthStore: Initializing authentication state...');
          
          // Validate authentication state
          const authState = await AuthService.validateAuthState();
          
          if (authState.isValid && authState.user) {
            const token = await StorageService.getSecure(STORAGE_KEYS.authToken);
            const refreshToken = await StorageService.getSecure(STORAGE_KEYS.refreshToken);
            
            set({
              user: { id: authState.user.id },
              token,
              refreshToken,
              isAuthenticated: true,
            });
            
            console.log('AuthStore: Authentication state restored successfully');
            
            // Initialize device registration if not already done
            try {
              const isRegistered = await DeviceRegistrationService.isDeviceRegistered();
              if (!isRegistered) {
                await get().registerDevice();
              }
            } catch (deviceError) {
              console.warn('Device registration initialization failed:', deviceError);
              // Don't fail auth initialization if device registration fails
            }
          } else {
            console.log('AuthStore: No valid authentication state found');
            set({
              user: null,
              token: null,
              refreshToken: null,
              isAuthenticated: false,
            });
          }
        } catch (error) {
          console.error('AuthStore: Auth initialization failed:', error);
          await get().logout();
          const errorMessage = error instanceof Error ? error.message : 'Authentication initialization failed';
          get().setError(errorMessage);
        } finally {
          set({ isLoading: false });
        }
      },

      registerDevice: async () => {
        try {
          console.log('AuthStore: Starting device registration for push notifications...');
          
          const result = await DeviceRegistrationService.registerDevice();
          
          if (result.success && result.pushToken) {
            set({ deviceToken: result.pushToken });
            console.log('AuthStore: Device registration successful');
          } else {
            throw new Error(result.error || 'Device registration failed');
          }
        } catch (error) {
          console.error('AuthStore: Device registration failed:', error);
          // Don't set error state for device registration failures
          // as it's not critical for authentication
          throw error;
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