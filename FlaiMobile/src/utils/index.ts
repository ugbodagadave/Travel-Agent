import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { STORAGE_KEYS } from '../constants';

// Storage Utilities
export class StorageService {
  // Secure Storage (for sensitive data like tokens)
  static async setSecure(key: string, value: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(key, value);
    } catch (error) {
      console.error('SecureStore setItem error:', error);
      // Fallback to AsyncStorage for development
      await AsyncStorage.setItem(key, value);
    }
  }

  static async getSecure(key: string): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(key);
    } catch (error) {
      console.error('SecureStore getItem error:', error);
      // Fallback to AsyncStorage for development
      return await AsyncStorage.getItem(key);
    }
  }

  static async removeSecure(key: string): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      console.error('SecureStore removeItem error:', error);
      await AsyncStorage.removeItem(key);
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
  static formatDate(date: Date): string {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  static formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  static formatDateTime(date: Date): string {
    return `${this.formatDate(date)} at ${this.formatTime(date)}`;
  }

  static isToday(date: Date): boolean {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  }

  static isYesterday(date: Date): boolean {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return (
      date.getDate() === yesterday.getDate() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getFullYear() === yesterday.getFullYear()
    );
  }

  static getRelativeTime(date: Date): string {
    if (this.isToday(date)) {
      return this.formatTime(date);
    } else if (this.isYesterday(date)) {
      return 'Yesterday';
    } else {
      return this.formatDate(date);
    }
  }

  static parseISOString(isoString: string): Date {
    return new Date(isoString);
  }

  static addMinutes(date: Date, minutes: number): Date {
    return new Date(date.getTime() + minutes * 60000);
  }

  static getDuration(start: Date, end: Date): string {
    const diffMs = end.getTime() - start.getTime();
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
export class DeviceUtils {
  static generateDeviceId(): string {
    return `mobile_${Date.now()}_${Math.random().toString(36).substring(2)}`;
  }

  static getDeviceInfo() {
    // This would typically use expo-device or react-native-device-info
    return {
      platform: 'ios', // or 'android'
      version: '1.0.0',
      deviceId: this.generateDeviceId(),
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