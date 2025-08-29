import { apiService } from './api';
import { StorageService, DeviceUtils, ValidationUtils, NetworkUtils } from '../utils';
import { STORAGE_KEYS, API_CONFIG } from '../constants';
import {
  DeviceInfo,
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  MobileUser,
} from '../types/auth';

// Development mode flag - set to true when backend is not available
const MOCK_MODE = __DEV__ && API_CONFIG.apiBaseUrl.includes('localhost');

export class AuthService {
  /**
   * Register a new user with device information
   * @param deviceInfo - Optional partial device info to override defaults
   * @returns Promise with registration response
   */
  static async register(deviceInfo?: Partial<DeviceInfo>): Promise<RegisterResponse> {
    try {
      // Get full device information
      const fullDeviceInfo = {
        ...(await DeviceUtils.getDeviceInfo()),
        ...deviceInfo,
      };

      // Validate device info
      if (!fullDeviceInfo.deviceId || !fullDeviceInfo.platform || !fullDeviceInfo.appVersion) {
        throw new AuthError({
          message: 'Invalid device information',
          code: 'INVALID_DEVICE_INFO',
        });
      }

      // Check network connectivity
      const isConnected = await NetworkUtils.checkConnectivity();
      if (!isConnected && !MOCK_MODE) {
        throw new AuthError({
          message: 'No internet connection available',
          code: 'NETWORK_ERROR',
        });
      }

      let response;
      
      if (MOCK_MODE) {
        // Mock implementation for development
        console.log('AuthService: Using mock mode for development');
        const mockUserId = `mobile:${fullDeviceInfo.deviceId}`;
        response = {
          success: true,
          data: {
            user_id: mockUserId,
            jwt: 'mock_jwt_token_' + Date.now(),
            refresh_token: 'mock_refresh_token_' + Date.now(),
          }
        };
      } else {
        // Prepare registration request
        const registerRequest: RegisterRequest = {
          device_info: fullDeviceInfo,
        };

        // Make API call
        response = await apiService.register(registerRequest.device_info);
      }

      // Validate response
      if (!response.success || !response.data?.user_id || !response.data?.jwt) {
        throw new AuthError({
          message: response.error || 'Registration failed',
          code: 'REGISTRATION_FAILED',
        });
      }

      // Store tokens securely
      await StorageService.setSecure(STORAGE_KEYS.authToken, response.data.jwt);
      if (response.data.refresh_token) {
        await StorageService.setSecure(STORAGE_KEYS.refreshToken, response.data.refresh_token);
      }
      await StorageService.setItem(STORAGE_KEYS.userId, response.data.user_id);

      return response.data as RegisterResponse;
    } catch (error) {
      console.error('Registration error:', error);
      if (error instanceof AuthError) {
        throw error;
      }
      throw new AuthError({
        message: NetworkUtils.getErrorMessage(error),
        code: 'REGISTRATION_ERROR',
        originalError: error instanceof Error ? error : new Error(String(error)),
      });
    }
  }

  /**
   * Login existing user with email or phone
   * @param credentials - Email or phone for login
   * @returns Promise with login response
   */
  static async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // Validate input
      if (!credentials.email && !credentials.phone) {
        throw new AuthError({
          message: 'Email or phone is required',
          code: 'MISSING_CREDENTIALS',
        });
      }

      if (credentials.email && !ValidationUtils.isEmail(credentials.email)) {
        throw new AuthError({
          message: 'Invalid email format',
          code: 'INVALID_EMAIL',
          field: 'email',
        });
      }

      if (credentials.phone && !ValidationUtils.isPhone(credentials.phone)) {
        throw new AuthError({
          message: 'Invalid phone format',
          code: 'INVALID_PHONE',
          field: 'phone',
        });
      }

      // Check network connectivity
      const isConnected = await NetworkUtils.checkConnectivity();
      if (!isConnected && !MOCK_MODE) {
        throw new AuthError({
          message: 'No internet connection available',
          code: 'NETWORK_ERROR',
        });
      }

      let response;
      
      if (MOCK_MODE) {
        // Mock implementation for development
        console.log('AuthService: Using mock mode for login');
        const mockUserId = credentials.email ? `mobile:${credentials.email}` : `mobile:${credentials.phone}`;
        response = {
          success: true,
          data: {
            user_id: mockUserId,
            jwt: 'mock_jwt_token_' + Date.now(),
            refresh_token: 'mock_refresh_token_' + Date.now(),
          }
        };
      } else {
        // Make API call
        response = await apiService.login(credentials);
      }

      // Validate response
      if (!response.success || !response.data?.user_id || !response.data?.jwt) {
        throw new AuthError({
          message: response.error || 'Login failed',
          code: 'LOGIN_FAILED',
        });
      }

      // Store tokens securely
      await StorageService.setSecure(STORAGE_KEYS.authToken, response.data.jwt);
      if (response.data.refresh_token) {
        await StorageService.setSecure(STORAGE_KEYS.refreshToken, response.data.refresh_token);
      }
      await StorageService.setItem(STORAGE_KEYS.userId, response.data.user_id);

      return response.data as LoginResponse;
    } catch (error) {
      console.error('Login error:', error);
      if (error instanceof AuthError) {
        throw error;
      }
      throw new AuthError({
        message: NetworkUtils.getErrorMessage(error),
        code: 'LOGIN_ERROR',
        originalError: error instanceof Error ? error : new Error(String(error)),
      });
    }
  }

  /**
   * Refresh authentication token
   * @param refreshToken - Optional refresh token, will use stored if not provided
   * @returns Promise with new tokens
   */
  static async refreshToken(refreshToken?: string): Promise<RefreshTokenResponse> {
    try {
      const token = refreshToken || await StorageService.getSecure(STORAGE_KEYS.refreshToken);
      
      if (!token) {
        throw new AuthError({
          message: 'No refresh token available',
          code: 'NO_REFRESH_TOKEN',
        });
      }

      // Check network connectivity
      const isConnected = await NetworkUtils.checkConnectivity();
      if (!isConnected) {
        throw new AuthError({
          message: 'No internet connection available',
          code: 'NETWORK_ERROR',
        });
      }

      // Make API call directly to avoid circular dependency with interceptors
      const response = await fetch(`${apiService['client'].defaults.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: token }),
      });

      if (!response.ok) {
        throw new AuthError({
          message: 'Token refresh failed',
          code: 'REFRESH_FAILED',
        });
      }

      const data = await response.json();

      // Validate response
      if (!data.success || !data.jwt) {
        throw new AuthError({
          message: data.error || 'Token refresh failed',
          code: 'REFRESH_FAILED',
        });
      }

      // Store new tokens
      await StorageService.setSecure(STORAGE_KEYS.authToken, data.jwt);
      if (data.refresh_token) {
        await StorageService.setSecure(STORAGE_KEYS.refreshToken, data.refresh_token);
      }

      return data as RefreshTokenResponse;
    } catch (error) {
      console.error('Token refresh error:', error);
      if (error instanceof AuthError) {
        throw error;
      }
      throw new AuthError({
        message: NetworkUtils.getErrorMessage(error),
        code: 'REFRESH_ERROR',
        originalError: error instanceof Error ? error : new Error(String(error)),
      });
    }
  }

  /**
   * Logout user and clear all stored data
   */
  static async logout(): Promise<void> {
    try {
      // Clear secure storage
      await StorageService.clearSecure();
      
      // Clear regular storage items
      await StorageService.removeItem(STORAGE_KEYS.userId);
      
      console.log('User logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
      // Don't throw error on logout, just log it
    }
  }

  /**
   * Check if user is currently authenticated
   * @returns Promise with authentication status
   */
  static async isAuthenticated(): Promise<boolean> {
    try {
      const token = await StorageService.getSecure(STORAGE_KEYS.authToken);
      const userId = await StorageService.getItem(STORAGE_KEYS.userId);
      
      return !!(token && userId);
    } catch (error) {
      console.error('Authentication check error:', error);
      return false;
    }
  }

  /**
   * Get current user information
   * @returns Promise with user data or null
   */
  static async getCurrentUser(): Promise<MobileUser | null> {
    try {
      const userId = await StorageService.getItem(STORAGE_KEYS.userId);
      const deviceId = await StorageService.getSecure(STORAGE_KEYS.deviceId);
      
      if (!userId || !deviceId) {
        return null;
      }

      // Create basic user object
      const user: MobileUser = {
        id: userId,
        deviceId,
        registeredAt: new Date().toISOString(), // Would come from API in real implementation
        pushNotificationsEnabled: false, // Would be determined by actual notification status
      };

      return user;
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  }

  /**
   * Validate stored authentication state
   * @returns Promise with validation result
   */
  static async validateAuthState(): Promise<{
    isValid: boolean;
    user: MobileUser | null;
    needsRefresh: boolean;
  }> {
    try {
      const isAuthenticated = await this.isAuthenticated();
      
      if (!isAuthenticated) {
        return {
          isValid: false,
          user: null,
          needsRefresh: false,
        };
      }

      const user = await this.getCurrentUser();
      
      // In a real implementation, you might check token expiration here
      // For now, assume token is valid if it exists
      
      return {
        isValid: true,
        user,
        needsRefresh: false,
      };
    } catch (error) {
      console.error('Auth state validation error:', error);
      return {
        isValid: false,
        user: null,
        needsRefresh: false,
      };
    }
  }

  /**
   * Clear all authentication data (for testing/debugging)
   */
  static async clearAuthData(): Promise<void> {
    try {
      await this.logout();
      console.log('All authentication data cleared');
    } catch (error) {
      console.error('Clear auth data error:', error);
    }
  }
}

// Custom error class for authentication errors
class AuthError extends Error {
  code?: string;
  field?: string;
  originalError?: Error;

  constructor({ message, code, field, originalError }: {
    message: string;
    code?: string;
    field?: string;
    originalError?: Error;
  }) {
    super(message);
    this.name = 'AuthError';
    this.code = code;
    this.field = field;
    this.originalError = originalError;
  }
}