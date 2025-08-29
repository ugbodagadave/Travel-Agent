import 'react-native-get-random-values';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { v4 as uuidv4 } from 'uuid';
import { STORAGE_KEYS } from '../constants';
import { Message } from '../types';
import { DeviceInfo, DeviceUtilsInterface } from '../types/auth';

// Export accessibility utilities
export * from './accessibility';

// Storage Utilities
export class StorageService {
  // Secure Storage (for sensitive data like tokens)
  static async setSecure(key: string, value: string): Promise<void> {
    if (!key || typeof key !== 'string') {
      throw new Error('Invalid storage key provided');
    }
    if (!value || typeof value !== 'string') {
      throw new Error('Invalid storage value provided');
    }

    try {
      await SecureStore.setItemAsync(key, value);
    } catch (error) {
      console.error('SecureStore setItem error:', error);
      // Fallback to AsyncStorage for development/testing
      if (__DEV__) {
        console.warn('Falling back to AsyncStorage for development');
        await AsyncStorage.setItem(key, value);
      } else {
        throw new Error(`Failed to store secure data: ${error}`);
      }
    }
  }

  static async getSecure(key: string): Promise<string | null> {
    if (!key || typeof key !== 'string') {
      console.error('Invalid storage key provided');
      return null;
    }

    try {
      const value = await SecureStore.getItemAsync(key);
      return value;
    } catch (error) {
      console.error('SecureStore getItem error:', error);
      // Fallback to AsyncStorage for development/testing
      if (__DEV__) {
        console.warn('Falling back to AsyncStorage for development');
        return await AsyncStorage.getItem(key);
      } else {
        console.error(`Failed to retrieve secure data for key ${key}:`, error);
        return null;
      }
    }
  }

  static async removeSecure(key: string): Promise<void> {
    if (!key || typeof key !== 'string') {
      console.error('Invalid storage key provided');
      return;
    }

    try {
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      console.error('SecureStore removeItem error:', error);
      // Fallback to AsyncStorage for development/testing
      if (__DEV__) {
        console.warn('Falling back to AsyncStorage for development');
        await AsyncStorage.removeItem(key);
      } else {
        console.error(`Failed to remove secure data for key ${key}:`, error);
      }
    }
  }

  static async clearSecure(): Promise<void> {
    try {
      // Clear common secure keys
      const secureKeys = [
        STORAGE_KEYS.authToken,
        STORAGE_KEYS.refreshToken,
        STORAGE_KEYS.deviceId,
      ];
      
      await Promise.all(
        secureKeys.map(key => this.removeSecure(key))
      );
    } catch (error) {
      console.error('Failed to clear secure storage:', error);
    }
  }

  // Regular Storage (for non-sensitive data)
  static async setItem(key: string, value: any): Promise<void> {
    try {
      const jsonValue = JSON.stringify(value);
      await AsyncStorage.setItem(key, jsonValue);
    } catch (error) {
      console.error('AsyncStorage setItem error:', error);
    }
  }

  static async getItem<T = any>(key: string): Promise<T | null> {
    try {
      const jsonValue = await AsyncStorage.getItem(key);
      return jsonValue ? JSON.parse(jsonValue) : null;
    } catch (error) {
      console.error('AsyncStorage getItem error:', error);
      return null;
    }
  }

  static async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error('AsyncStorage removeItem error:', error);
    }
  }

  static async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('AsyncStorage clear error:', error);
    }
  }
}

// Date Utilities
export class DateUtils {
  // Safe date validation
  static isValidDate(date: any): date is Date {
    return date instanceof Date && !isNaN(date.getTime());
  }

  // Safe date conversion from various formats
  static toDate(input: any): Date {
    if (this.isValidDate(input)) {
      return input;
    }
    
    if (typeof input === 'string' || typeof input === 'number') {
      const parsed = new Date(input);
      if (this.isValidDate(parsed)) {
        return parsed;
      }
    }
    
    // Fallback to current date for invalid inputs
    console.warn('Invalid date input, using current time:', input);
    return new Date();
  }

  // Safe time formatting with fallback
  static formatTime(input: any): string {
    const date = this.toDate(input);
    try {
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (error) {
      console.warn('Failed to format time, using fallback:', error);
      return 'Invalid Time';
    }
  }

  // Safe date formatting with fallback
  static formatDate(input: any): string {
    const date = this.toDate(input);
    try {
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch (error) {
      console.warn('Failed to format date, using fallback:', error);
      return 'Invalid Date';
    }
  }

  static formatDateTime(input: any): string {
    return `${this.formatDate(input)} at ${this.formatTime(input)}`;
  }

  static isToday(input: any): boolean {
    const date = this.toDate(input);
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  }

  static isYesterday(input: any): boolean {
    const date = this.toDate(input);
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return (
      date.getDate() === yesterday.getDate() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getFullYear() === yesterday.getFullYear()
    );
  }

  static getRelativeTime(input: any): string {
    if (this.isToday(input)) {
      return this.formatTime(input);
    } else if (this.isYesterday(input)) {
      return 'Yesterday';
    } else {
      return this.formatDate(input);
    }
  }

  static parseISOString(isoString: string): Date {
    return this.toDate(isoString);
  }

  static addMinutes(input: any, minutes: number): Date {
    const date = this.toDate(input);
    return new Date(date.getTime() + minutes * 60000);
  }

  static getDuration(start: any, end: any): string {
    const startDate = this.toDate(start);
    const endDate = this.toDate(end);
    const diffMs = endDate.getTime() - startDate.getTime();
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  }
}

// String Utilities
export class StringUtils {
  static capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  }

  static truncate(str: string, length: number): string {
    return str.length > length ? `${str.substring(0, length)}...` : str;
  }

  static generateId(): string {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  }

  static formatCurrency(amount: number, currency = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  }

  static formatPhoneNumber(phone: string): string {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    return phone;
  }

  static validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

// Message Data Utilities
export class MessageUtils {
  // Validate and transform message data to ensure type safety
  static validateMessage(messageData: any): Message {
    const validated: Message = {
      id: typeof messageData.id === 'string' ? messageData.id : StringUtils.generateId(),
      text: typeof messageData.text === 'string' ? messageData.text : '',
      isUser: Boolean(messageData.isUser),
      timestamp: DateUtils.toDate(messageData.timestamp),
      status: this.validateStatus(messageData.status),
    };

    return validated;
  }

  // Validate message status
  static validateStatus(status: any): Message['status'] {
    const validStatuses = ['sending', 'sent', 'delivered', 'error'];
    return validStatuses.includes(status) ? status : undefined;
  }

  // Transform array of messages ensuring all have valid timestamps
  static validateMessages(messages: any[]): Message[] {
    if (!Array.isArray(messages)) {
      console.warn('Invalid messages array, returning empty array');
      return [];
    }

    return messages.map(this.validateMessage).filter(Boolean);
  }

  // Safe message creation
  static createMessage(data: Omit<Message, 'id' | 'timestamp'>): Message {
    return {
      ...data,
      id: StringUtils.generateId(),
      timestamp: new Date(),
    };
  }

  // Format message timestamp for display
  static formatMessageTime(message: Message): string {
    return DateUtils.formatTime(message.timestamp);
  }

  // Get relative time for message
  static getMessageRelativeTime(message: Message): string {
    return DateUtils.getRelativeTime(message.timestamp);
  }

  static sanitizeInput(input: string): string {
    return input.trim().replace(/[<>]/g, '');
  }
}

// Network Utilities
export class NetworkUtils {
  static async checkConnectivity(): Promise<boolean> {
    try {
      const response = await fetch('https://www.google.com', {
        method: 'HEAD',
        mode: 'no-cors',
      });
      return true;
    } catch {
      return false;
    }
  }

  static getErrorMessage(error: any): string {
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  }

  static isNetworkError(error: any): boolean {
    return (
      error.code === 'NETWORK_ERROR' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('timeout')
    );
  }
}

// Validation Utilities
export class ValidationUtils {
  static isRequired(value: any): boolean {
    if (typeof value === 'string') {
      return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
  }

  static isMinLength(value: string, length: number): boolean {
    return value.length >= length;
  }

  static isMaxLength(value: string, length: number): boolean {
    return value.length <= length;
  }

  static isEmail(email: string): boolean {
    return StringUtils.validateEmail(email);
  }

  static isPhone(phone: string): boolean {
    const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
  }

  static isAlpha(value: string): boolean {
    const alphaRegex = /^[a-zA-Z\s]+$/;
    return alphaRegex.test(value);
  }

  static isNumeric(value: string): boolean {
    const numericRegex = /^\d+$/;
    return numericRegex.test(value);
  }
}

// Device Utilities
export class DeviceUtils implements DeviceUtilsInterface {
  static generateDeviceId(): string {
    return uuidv4();
  }

  static getPlatform(): 'ios' | 'android' {
    return Device.osName === 'iOS' ? 'ios' : 'android';
  }

  static getAppVersion(): string {
    return Constants.expoConfig?.version || '1.0.0';
  }

  static getOSVersion(): string {
    return Device.osVersion || 'Unknown';
  }

  static getDeviceName(): string {
    return Device.deviceName || `${Device.brand} ${Device.modelName}` || 'Unknown Device';
  }

  static getModelName(): string {
    return Device.modelName || 'Unknown';
  }

  static isDevice(): boolean {
    return Device.isDevice;
  }

  static async getStoredDeviceId(): Promise<string> {
    try {
      let deviceId = await StorageService.getSecure(STORAGE_KEYS.deviceId);
      if (!deviceId) {
        deviceId = this.generateDeviceId();
        await StorageService.setSecure(STORAGE_KEYS.deviceId, deviceId);
      }
      return deviceId;
    } catch (error) {
      console.warn('Failed to get stored device ID, generating new one:', error);
      return this.generateDeviceId();
    }
  }

  static async getDeviceInfo(): Promise<DeviceInfo> {
    const deviceId = await this.getStoredDeviceId();
    
    return {
      platform: this.getPlatform(),
      version: this.getAppVersion(),
      deviceId,
      deviceName: this.getDeviceName(),
      appVersion: this.getAppVersion(),
      osVersion: this.getOSVersion(),
      modelName: this.getModelName(),
      isDevice: this.isDevice(),
    };
  }
}

// Error Handling Utilities
export class ErrorUtils {
  static logError(error: Error, context?: string): void {
    console.error(`Error ${context ? `in ${context}` : ''}:`, error);
    // In production, you would send this to a crash reporting service
    // like Sentry or Crashlytics
  }

  static createErrorResponse(message: string, code?: string) {
    return {
      success: false,
      error: message,
      code,
    };
  }

  static handleAsyncError(
    asyncFn: () => Promise<any>,
    fallbackValue?: any
  ): () => Promise<any> {
    return async () => {
      try {
        return await asyncFn();
      } catch (error) {
        this.logError(error as Error);
        return fallbackValue;
      }
    };
  }
}

// Debounce utility for search and input handling
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

// Throttle utility for preventing rapid API calls
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;
  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func(...args);
    }
  };
}

// Retry utility for failed operations
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }
  throw new Error('Max retry attempts reached');
}