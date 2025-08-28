// Chat related types
export interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'delivered' | 'error';
}

export interface ChatState {
  messages: Message[];
  isTyping: boolean;
  isConnected: boolean;
  conversationState: ConversationState;
}

// Conversation flow states
export type ConversationState = 
  | 'GATHERING_INFO'
  | 'GATHERING_NAMES'
  | 'AWAITING_CLASS_SELECTION'
  | 'AWAITING_CONFIRMATION'
  | 'SEARCH_IN_PROGRESS'
  | 'FLIGHT_SELECTION'
  | 'AWAITING_PAYMENT_SELECTION'
  | 'AWAITING_PAYMENT'
  | 'AWAITING_USDC_PAYMENT'
  | 'AWAITING_CIRCLE_LAYER_PAYMENT'
  | 'BOOKING_CONFIRMED';

// Flight related types
export interface FlightOffer {
  id: string;
  price: {
    total: string;
    currency: string;
  };
  itineraries: Itinerary[];
  travelerPricings: TravelerPricing[];
  validatingAirlineCodes: string[];
}

export interface Itinerary {
  duration: string;
  segments: Segment[];
}

export interface Segment {
  departure: {
    iataCode: string;
    at: string;
  };
  arrival: {
    iataCode: string;
    at: string;
  };
  carrierCode: string;
  number: string;
  aircraft: {
    code: string;
  };
  operating?: {
    carrierCode: string;
  };
}

export interface TravelerPricing {
  travelerId: string;
  fareOption: string;
  travelerType: string;
  price: {
    currency: string;
    total: string;
    base: string;
  };
}

// User and authentication types
export interface User {
  id: string;
  email?: string;
  phone?: string;
  name?: string;
  savedTravelers?: Traveler[];
}

export interface Traveler {
  id: string;
  firstName: string;
  lastName: string;
  dateOfBirth?: string;
  gender?: 'MALE' | 'FEMALE';
  phone?: string;
  email?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Payment related types
export type PaymentMethod = 'card' | 'usdc' | 'circlelayer';

export interface PaymentState {
  selectedMethod: PaymentMethod | null;
  isProcessing: boolean;
  checkoutUrl?: string;
  paymentAddress?: string;
  expectedAmount?: string;
  currency?: string;
  status: 'idle' | 'pending' | 'completed' | 'failed';
}

// Ticket related types
export interface Ticket {
  id: string;
  filename: string;
  secureUrl: string;
  createdAt: string;
  tripSummary: {
    origin: string;
    destination: string;
    date: string;
    travelers: string[];
  };
  status: 'delivered' | 'processing' | 'failed';
}

// API related types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  messages?: string[];
  state?: ConversationState;
  requiresAction?: string;
}

export interface DeviceInfo {
  platform: 'ios' | 'android';
  version: string;
  deviceId: string;
  pushToken?: string;
}

// App configuration types
export interface AppConfig {
  apiBaseUrl: string;
  websocketUrl: string;
  stripePublishableKey: string;
  environment: 'development' | 'staging' | 'production';
}

// Navigation types
export type RootStackParamList = {
  Onboarding: undefined;
  Main: undefined;
  Chat: undefined;
  FlightResults: undefined;
  FlightDetails: { flightId: string };
  Payment: { method: PaymentMethod };
  Tickets: undefined;
  TicketDetail: { ticketId: string };
  Settings: undefined;
};

export type TabParamList = {
  Chat: undefined;
  Tickets: undefined;
  Settings: undefined;
};