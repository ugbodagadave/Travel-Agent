import { AppConfig } from '../types';

// API Configuration
export const API_CONFIG: AppConfig = {
  apiBaseUrl: __DEV__ ? 'http://localhost:5000' : 'https://your-production-api.com',
  websocketUrl: __DEV__ ? 'ws://localhost:5000' : 'wss://your-production-api.com',
  stripePublishableKey: 'pk_test_your_stripe_key_here',
  environment: __DEV__ ? 'development' : 'production',
};

// App Metadata
export const APP_INFO = {
  name: 'Flai',
  version: '1.0.0',
  description: 'AI-Powered Travel Agent',
  developer: 'Travel Agent Team',
};

// Colors (Design System)
export const COLORS = {
  // Primary Colors
  primary: '#007AFF',
  primaryDark: '#0056CC',
  primaryLight: '#4DA6FF',
  
  // Secondary Colors
  secondary: '#FF9500',
  secondaryDark: '#CC7700',
  secondaryLight: '#FFBB4D',
  
  // Neutral Colors
  white: '#FFFFFF',
  black: '#000000',
  gray50: '#F9FAFB',
  gray100: '#F3F4F6',
  gray200: '#E5E7EB',
  gray300: '#D1D5DB',
  gray400: '#9CA3AF',
  gray500: '#6B7280',
  gray600: '#4B5563',
  gray700: '#374151',
  gray800: '#1F2937',
  gray900: '#111827',
  
  // Semantic Colors
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  
  // Message Colors
  userMessage: '#007AFF',
  botMessage: '#F3F4F6',
  userMessageText: '#FFFFFF',
  botMessageText: '#1F2937',
};

// Typography
export const FONTS = {
  regular: 'System',
  medium: 'System',
  semiBold: 'System',
  bold: 'System',
};

export const FONT_SIZES = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 32,
  '4xl': 36,
};

// Spacing
export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  '2xl': 48,
  '3xl': 64,
};

// Screen Dimensions
export const SCREEN_PADDING = SPACING.md;
export const HEADER_HEIGHT = 60;
export const TAB_BAR_HEIGHT = 80;

// Animation Durations
export const ANIMATION_DURATION = {
  fast: 200,
  normal: 300,
  slow: 500,
};

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  register: '/mobile/register',
  login: '/mobile/login',
  devices: '/mobile/devices',
  
  // Messaging
  message: '/mobile/message',
  messages: '/mobile/messages',
  realtime: '/mobile/realtime',
  
  // Flights
  offers: '/mobile/offers',
  selectOffer: '/mobile/select-offer',
  
  // Payments
  paymentsStripe: '/mobile/payments/stripe',
  paymentsUsdc: '/mobile/payments/usdc',
  paymentsCircleLayer: '/mobile/payments/circlelayer',
  
  // Tickets
  tickets: '/mobile/tickets',
};

// Storage Keys
export const STORAGE_KEYS = {
  // Authentication
  authToken: 'flai_auth_token',
  refreshToken: 'flai_refresh_token',
  userId: 'flai_user_id',
  
  // User Preferences
  theme: 'flai_theme',
  notificationSettings: 'flai_notifications',
  savedTravelers: 'flai_saved_travelers',
  
  // Chat Data
  messages: 'flai_messages',
  conversationState: 'flai_conversation_state',
  
  // App State
  hasOnboarded: 'flai_has_onboarded',
  onboardingCompleted: 'flai_onboarding_completed',
  appVersion: 'flai_app_version',
};

// Message Types for Real-time Communication
export const MESSAGE_TYPES = {
  CHAT_MESSAGE: 'chat_message',
  STATE_CHANGE: 'state_change',
  FLIGHT_RESULTS: 'flight_results',
  PAYMENT_UPDATE: 'payment_update',
  TICKET_DELIVERED: 'ticket_delivered',
  TYPING_START: 'typing_start',
  TYPING_END: 'typing_end',
};

// Travel Classes
export const TRAVEL_CLASSES = [
  { id: 'ECONOMY', name: 'Economy', description: 'Standard comfort and service' },
  { id: 'PREMIUM_ECONOMY', name: 'Premium Economy', description: 'Extra legroom and amenities' },
  { id: 'BUSINESS', name: 'Business', description: 'Premium comfort and service' },
  { id: 'FIRST', name: 'First Class', description: 'Ultimate luxury experience' },
];

// Payment Methods
export const PAYMENT_METHODS = [
  {
    id: 'card',
    name: 'Credit/Debit Card',
    description: 'Secure payment via Stripe',
    icon: 'card-outline',
  },
  {
    id: 'usdc',
    name: 'USDC Cryptocurrency',
    description: 'Pay with USDC stablecoin',
    icon: 'logo-bitcoin',
  },
  {
    id: 'circlelayer',
    name: 'Circle Layer (On-chain)',
    description: 'Pay with CLAYER tokens',
    icon: 'link-outline',
  },
];

// App Limits and Constraints
export const LIMITS = {
  maxTravelers: 9,
  maxMessageLength: 1000,
  maxRetries: 3,
  sessionTimeout: 30 * 60 * 1000, // 30 minutes
  messageTimeout: 10 * 1000, // 10 seconds
};

// Feature Flags
export const FEATURES = {
  pushNotifications: true,
  offlineMode: true,
  biometricAuth: true,
  analytics: true,
  crashReporting: true,
  webSocketFallback: true,
};