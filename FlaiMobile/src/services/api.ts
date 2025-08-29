import axios, { AxiosInstance, AxiosResponse, AxiosError, AxiosRequestConfig } from 'axios';
import { API_CONFIG, API_ENDPOINTS } from '../constants';
import { StorageService, NetworkUtils } from '../utils';
import { STORAGE_KEYS } from '../constants';
import { ApiResponse, DeviceInfo } from '../types';
import { AuthApiResponse } from '../types/auth';

class ApiService {
  private client: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (error?: any) => void;
    config: AxiosRequestConfig;
  }> = [];

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.apiBaseUrl,
      timeout: 30000, // Increased timeout for mobile networks
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token and handle network issues
    this.client.interceptors.request.use(
      async (config) => {
        // Add auth token if available
        const token = await StorageService.getSecure(STORAGE_KEYS.authToken);
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp for debugging
        config.metadata = { startTime: new Date() };
        
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log successful responses
        const duration = response.config.metadata ? 
          new Date().getTime() - response.config.metadata.startTime.getTime() : 0;
        console.log(`API Response: ${response.status} ${response.config.url} (${duration}ms)`);
        
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config;
        
        // Log error details
        console.error('API Error:', {
          url: originalRequest?.url,
          status: error.response?.status,
          message: error.message,
        });

        // Handle token expiration with queue management
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Add request to queue
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject, config: originalRequest });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            await this.refreshToken();
            this.processQueue(null);
            this.isRefreshing = false;
            
            // Retry the original request
            return this.client.request(originalRequest);
          } catch (refreshError) {
            this.processQueue(refreshError);
            this.isRefreshing = false;
            await this.handleAuthFailure();
            throw refreshError;
          }
        }

        // Handle network errors
        if (!error.response) {
          const networkError = new Error('Network error - please check your connection');
          networkError.name = 'NetworkError';
          throw networkError;
        }

        return Promise.reject(error);
      }
    );
  }

  private processQueue(error: any) {
    this.failedQueue.forEach(({ resolve, reject, config }) => {
      if (error) {
        reject(error);
      } else {
        resolve(this.client.request(config));
      }
    });
    
    this.failedQueue = [];
  }

  private async handleAuthFailure(): Promise<void> {
    try {
      // Clear all stored auth data
      await StorageService.removeSecure(STORAGE_KEYS.authToken);
      await StorageService.removeSecure(STORAGE_KEYS.refreshToken);
      await StorageService.removeItem(STORAGE_KEYS.userId);
      
      console.log('Authentication failed - user logged out');
      
      // In a real app, you might want to emit an event or navigate to login
      // This would be handled by the auth store or navigation system
    } catch (error) {
      console.error('Error during auth failure cleanup:', error);
    }
  }

  private async refreshToken(): Promise<void> {
    const refreshToken = await StorageService.getSecure(STORAGE_KEYS.refreshToken);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      console.log('Attempting to refresh authentication token...');
      
      // Check network connectivity
      const isConnected = await NetworkUtils.checkConnectivity();
      if (!isConnected) {
        throw new Error('No internet connection available');
      }

      const response = await fetch(`${API_CONFIG.apiBaseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error(`Token refresh failed with status: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data.jwt) {
        throw new Error('Invalid refresh response - no JWT token');
      }

      // Store new tokens
      await StorageService.setSecure(STORAGE_KEYS.authToken, data.jwt);
      if (data.refresh_token) {
        await StorageService.setSecure(STORAGE_KEYS.refreshToken, data.refresh_token);
      }
      
      console.log('Authentication token refreshed successfully');
    } catch (error) {
      console.error('Token refresh error:', error);
      throw new Error(`Token refresh failed: ${error.message}`);
    }
  }

  // Authentication endpoints
  async register(deviceInfo: DeviceInfo): Promise<AuthApiResponse> {
    try {
      console.log('API: Registering device with backend...');
      const response = await this.client.post(API_ENDPOINTS.register, { device_info: deviceInfo });
      return response.data;
    } catch (error) {
      console.error('API: Registration failed:', error);
      throw new Error(NetworkUtils.getErrorMessage(error));
    }
  }

  async login(credentials: { email?: string; phone?: string }): Promise<AuthApiResponse> {
    try {
      console.log('API: Logging in user...');
      const response = await this.client.post(API_ENDPOINTS.login, credentials);
      return response.data;
    } catch (error) {
      console.error('API: Login failed:', error);
      throw new Error(NetworkUtils.getErrorMessage(error));
    }
  }

  async registerDevice(deviceData: {
    push_token: string;
    platform: 'ios' | 'android';
    app_version: string;
  }): Promise<AuthApiResponse> {
    try {
      console.log('API: Registering device for push notifications...');
      const response = await this.client.post(API_ENDPOINTS.devices, deviceData);
      return response.data;
    } catch (error) {
      console.error('API: Device registration failed:', error);
      throw new Error(NetworkUtils.getErrorMessage(error));
    }
  }

  // Messaging endpoints
  async sendMessage(data: { user_id: string; text: string }): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.message, data);
    return response.data;
  }

  async getMessages(since?: string): Promise<ApiResponse> {
    const params = since ? { since } : {};
    const response = await this.client.get(API_ENDPOINTS.messages, { params });
    return response.data;
  }

  // Flight endpoints
  async getOffers(): Promise<ApiResponse> {
    const response = await this.client.get(API_ENDPOINTS.offers);
    return response.data;
  }

  async getOffer(id: string): Promise<ApiResponse> {
    const response = await this.client.get(`${API_ENDPOINTS.offers}/${id}`);
    return response.data;
  }

  async selectOffer(offerId: string): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.selectOffer, {
      offer_id: offerId,
    });
    return response.data;
  }

  // Payment endpoints
  async createStripePayment(offerId: string): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.paymentsStripe, {
      offer_id: offerId,
    });
    return response.data;
  }

  async createUsdcPayment(offerId: string): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.paymentsUsdc, {
      offer_id: offerId,
    });
    return response.data;
  }

  async createCircleLayerPayment(offerId: string): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.paymentsCircleLayer, {
      offer_id: offerId,
    });
    return response.data;
  }

  // Ticket endpoints
  async getTickets(): Promise<ApiResponse> {
    const response = await this.client.get(API_ENDPOINTS.tickets);
    return response.data;
  }

  // Generic request methods for flexibility
  async get<T = any>(url: string, params?: any): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post<T = any>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async put<T = any>(url: string, data?: any): Promise<T> {
    const response = await this.client.put(url, data);
    return response.data;
  }

  async delete<T = any>(url: string): Promise<T> {
    const response = await this.client.delete(url);
    return response.data;
  }
}

export const apiService = new ApiService();