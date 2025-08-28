import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { API_CONFIG, API_ENDPOINTS } from '../constants';
import { StorageService } from '../utils';
import { STORAGE_KEYS } from '../constants';
import { ApiResponse, DeviceInfo } from '../types';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.apiBaseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await StorageService.getSecure(STORAGE_KEYS.authToken);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error: AxiosError) => {
        // Handle token expiration
        if (error.response?.status === 401) {
          try {
            await this.refreshToken();
            // Retry the original request
            return this.client.request(error.config!);
          } catch (refreshError) {
            // Refresh failed, logout user
            await this.logout();
            throw refreshError;
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<void> {
    const refreshToken = await StorageService.getSecure(STORAGE_KEYS.refreshToken);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post(`${API_CONFIG.apiBaseUrl}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { jwt, refresh_token } = response.data;
      await StorageService.setSecure(STORAGE_KEYS.authToken, jwt);
      await StorageService.setSecure(STORAGE_KEYS.refreshToken, refresh_token);
    } catch (error) {
      throw new Error('Token refresh failed');
    }
  }

  private async logout(): Promise<void> {
    await StorageService.removeSecure(STORAGE_KEYS.authToken);
    await StorageService.removeSecure(STORAGE_KEYS.refreshToken);
    await StorageService.removeItem(STORAGE_KEYS.userId);
    // You might want to emit an event or call a logout function here
  }

  // Authentication endpoints
  async register(deviceInfo: DeviceInfo): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.register, deviceInfo);
    return response.data;
  }

  async login(credentials: { email?: string; phone?: string }): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.login, credentials);
    return response.data;
  }

  async registerDevice(deviceData: {
    push_token: string;
    platform: 'ios' | 'android';
    app_version: string;
  }): Promise<ApiResponse> {
    const response = await this.client.post(API_ENDPOINTS.devices, deviceData);
    return response.data;
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