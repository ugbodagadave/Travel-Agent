// Authentication-specific type definitions
export interface DeviceInfo {
  platform: 'ios' | 'android';
  version: string;
  deviceId: string;
  deviceName?: string;
  appVersion: string;
  pushToken?: string;
  osVersion?: string;
  modelName?: string;
  isDevice?: boolean;
}

// Registration request/response types
export interface RegisterRequest {
  device_info: DeviceInfo;
}

export interface RegisterResponse {
  user_id: string;
  jwt: string;
  refresh_token: string;
  success: boolean;
}

// Login request/response types
export interface LoginRequest {
  email?: string;
  phone?: string;
}

export interface LoginResponse {
  user_id: string;
  jwt: string;
  refresh_token?: string;
  success: boolean;
}

// Token refresh types
export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  jwt: string;
  refresh_token: string;
  success: boolean;
}

// Device registration types
export interface DeviceRegistrationRequest {
  push_token: string;
  platform: 'ios' | 'android';
  app_version: string;
}

export interface DeviceRegistrationResponse {
  success: boolean;
  message?: string;
}

// Push notification types
export interface NotificationPermissions {
  status: 'granted' | 'denied' | 'undetermined';
  canAskAgain?: boolean;
  canAskAgainAsync?: boolean;
}

export interface PushToken {
  data: string;
  type: 'expo' | 'ios' | 'android';
}

// Authentication error types
export interface AuthError {
  message: string;
  code?: string;
  field?: string;
  originalError?: Error;
}

// Authentication states
export type AuthenticationStatus = 
  | 'unauthenticated'
  | 'authenticating'
  | 'authenticated'
  | 'error';

// Enhanced user interface for mobile
export interface MobileUser {
  id: string;
  email?: string;
  phone?: string;
  name?: string;
  deviceId: string;
  registeredAt: string;
  lastActiveAt?: string;
  pushNotificationsEnabled: boolean;
}

// Storage keys type safety
export interface SecureStorageKeys {
  AUTH_TOKEN: 'flai_auth_token';
  REFRESH_TOKEN: 'flai_refresh_token';
  USER_ID: 'flai_user_id';
  DEVICE_ID: 'flai_device_id';
  PUSH_TOKEN: 'flai_push_token';
}

export interface RegularStorageKeys {
  THEME: 'flai_theme';
  ONBOARDING_COMPLETED: 'flai_onboarding_completed';
  NOTIFICATION_SETTINGS: 'flai_notifications';
  APP_VERSION: 'flai_app_version';
}

// API response wrapper for authentication
export interface AuthApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  code?: string;
}

// Device utilities types
export interface DeviceUtilsInterface {
  getDeviceInfo(): DeviceInfo;
  generateDeviceId(): string;
  getPlatform(): 'ios' | 'android';
  getAppVersion(): string;
  getOSVersion(): string;
  getDeviceName(): string;
  getModelName(): string;
  isDevice(): boolean;
}