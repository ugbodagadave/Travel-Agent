import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { apiService } from './api';
import { StorageService, DeviceUtils } from '../utils';
import { STORAGE_KEYS, API_CONFIG } from '../constants';
import {
  NotificationPermissions,
  PushToken,
  DeviceRegistrationRequest,
  DeviceRegistrationResponse,
} from '../types/auth';

// Development mode flag - set to true when backend is not available or in Expo Go
const MOCK_MODE = __DEV__ && (API_CONFIG.apiBaseUrl.includes('localhost') || !Device.isDevice);

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export class DeviceRegistrationService {
  private static readonly PUSH_TOKEN_KEY = 'flai_push_token';

  /**
   * Request notification permissions from the user
   * @returns Promise with permission status
   */
  static async requestNotificationPermissions(): Promise<NotificationPermissions> {
    try {
      if (!Device.isDevice) {
        console.warn('Push notifications only work on physical devices');
        return {
          status: 'denied',
          canAskAgain: false,
        };
      }

      // Check existing permissions
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      // Request permissions if not already granted
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      const permissions: NotificationPermissions = {
        status: finalStatus as 'granted' | 'denied' | 'undetermined',
        canAskAgain: finalStatus !== 'denied',
      };

      console.log('Notification permissions:', permissions);
      return permissions;
    } catch (error) {
      console.error('Error requesting notification permissions:', error);
      return {
        status: 'denied',
        canAskAgain: false,
      };
    }
  }

  /**
   * Generate push notification token
   * @returns Promise with push token or null
   */
  static async generatePushToken(): Promise<PushToken | null> {
    try {
      if (!Device.isDevice) {
        console.warn('Push tokens only work on physical devices');
        return null;
      }

      // Check if we have valid project ID for Expo
      const projectId = Constants.expoConfig?.extra?.eas?.projectId || Constants.easConfig?.projectId;
      
      if (!projectId) {
        console.warn('No Expo project ID found, using development token');
      }

      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId,
      });

      const pushToken: PushToken = {
        data: tokenData.data,
        type: tokenData.type || 'expo',
      };

      console.log('Generated push token:', pushToken.data);
      return pushToken;
    } catch (error) {
      console.error('Error generating push token:', error);
      return null;
    }
  }

  /**
   * Register device with backend API
   * @param pushToken - Push notification token
   * @returns Promise with registration response
   */
  static async registerDeviceWithBackend(pushToken: string): Promise<DeviceRegistrationResponse> {
    try {
      const deviceInfo = await DeviceUtils.getDeviceInfo();
      
      const registrationData: DeviceRegistrationRequest = {
        push_token: pushToken,
        platform: deviceInfo.platform,
        app_version: deviceInfo.appVersion,
      };

      const response = await apiService.registerDevice(registrationData);
      
      if (!response.success) {
        throw new Error(response.error || 'Device registration failed');
      }

      console.log('Device registered with backend successfully');
      return response as DeviceRegistrationResponse;
    } catch (error) {
      console.error('Error registering device with backend:', error);
      throw new Error(`Device registration failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Complete device registration process
   * @returns Promise with success status and push token
   */
  static async registerDevice(): Promise<{
    success: boolean;
    pushToken?: string;
    error?: string;
  }> {
    try {
      console.log('Starting device registration process...');

      if (MOCK_MODE) {
        // Mock implementation for development/Expo Go
        console.log('DeviceRegistrationService: Using mock mode for development');
        const mockToken = `mock_push_token_${Date.now()}`;
        await StorageService.setSecure(this.PUSH_TOKEN_KEY, mockToken);
        
        return {
          success: true,
          pushToken: mockToken,
        };
      }

      // Step 1: Request notification permissions
      const permissions = await this.requestNotificationPermissions();
      
      if (permissions.status !== 'granted') {
        return {
          success: false,
          error: 'Notification permissions not granted',
        };
      }

      // Step 2: Generate push token
      const tokenData = await this.generatePushToken();
      
      if (!tokenData) {
        return {
          success: false,
          error: 'Failed to generate push token',
        };
      }

      // Step 3: Store token locally
      await StorageService.setSecure(this.PUSH_TOKEN_KEY, tokenData.data);

      // Step 4: Register with backend
      try {
        await this.registerDeviceWithBackend(tokenData.data);
      } catch (error) {
        console.warn('Backend registration failed, but local token stored:', error);
        // Don't fail the entire process if backend registration fails
        // The token is stored locally and can be retried later
      }

      return {
        success: true,
        pushToken: tokenData.data,
      };
    } catch (error) {
      console.error('Device registration error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error during device registration',
      };
    }
  }

  /**
   * Get stored push token
   * @returns Promise with stored push token or null
   */
  static async getStoredPushToken(): Promise<string | null> {
    try {
      return await StorageService.getSecure(this.PUSH_TOKEN_KEY);
    } catch (error) {
      console.error('Error getting stored push token:', error);
      return null;
    }
  }

  /**
   * Check if device is registered for push notifications
   * @returns Promise with registration status
   */
  static async isDeviceRegistered(): Promise<boolean> {
    try {
      const token = await this.getStoredPushToken();
      return !!token;
    } catch (error) {
      console.error('Error checking device registration:', error);
      return false;
    }
  }

  /**
   * Retry backend registration with stored token
   * @returns Promise with retry success status
   */
  static async retryBackendRegistration(): Promise<boolean> {
    try {
      const token = await this.getStoredPushToken();
      
      if (!token) {
        console.log('No stored push token found for retry');
        return false;
      }

      await this.registerDeviceWithBackend(token);
      console.log('Backend registration retry successful');
      return true;
    } catch (error) {
      console.error('Backend registration retry failed:', error);
      return false;
    }
  }

  /**
   * Clear device registration data
   */
  static async clearRegistration(): Promise<void> {
    try {
      await StorageService.removeSecure(this.PUSH_TOKEN_KEY);
      console.log('Device registration data cleared');
    } catch (error) {
      console.error('Error clearing device registration:', error);
    }
  }

  /**
   * Setup notification listeners
   * @returns Function to remove listeners
   */
  static setupNotificationListeners(): () => void {
    // Listener for notifications received while app is foregrounded
    const notificationListener = Notifications.addNotificationReceivedListener(notification => {
      console.log('Notification received:', notification);
      // Handle notification received while app is active
    });

    // Listener for when a user taps on or interacts with a notification
    const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('Notification response:', response);
      // Handle notification interaction
      // This is where you would navigate to specific screens based on notification data
    });

    // Return cleanup function
    return () => {
      Notifications.removeNotificationSubscription(notificationListener);
      Notifications.removeNotificationSubscription(responseListener);
    };
  }

  /**
   * Get notification permission status
   * @returns Promise with current permission status
   */
  static async getNotificationPermissionStatus(): Promise<NotificationPermissions> {
    try {
      const { status } = await Notifications.getPermissionsAsync();
      return {
        status: status as 'granted' | 'denied' | 'undetermined',
        canAskAgain: status !== 'denied',
      };
    } catch (error) {
      console.error('Error getting notification permission status:', error);
      return {
        status: 'denied',
        canAskAgain: false,
      };
    }
  }

  /**
   * Initialize device registration on app start
   * @returns Promise with initialization result
   */
  static async initializeDeviceRegistration(): Promise<{
    success: boolean;
    pushToken?: string;
    permissionsGranted: boolean;
  }> {
    try {
      console.log('Initializing device registration...');

      // Check if already registered
      const existingToken = await this.getStoredPushToken();
      const permissions = await this.getNotificationPermissionStatus();

      if (existingToken && permissions.status === 'granted') {
        console.log('Device already registered with token:', existingToken);
        
        // Try to retry backend registration in case it failed before
        await this.retryBackendRegistration();
        
        return {
          success: true,
          pushToken: existingToken,
          permissionsGranted: true,
        };
      }

      // Register device if not already done
      const registrationResult = await this.registerDevice();

      return {
        success: registrationResult.success,
        pushToken: registrationResult.pushToken,
        permissionsGranted: permissions.status === 'granted',
      };
    } catch (error) {
      console.error('Device registration initialization error:', error);
      return {
        success: false,
        permissionsGranted: false,
      };
    }
  }
}