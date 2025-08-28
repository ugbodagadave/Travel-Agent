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
  Auth: undefined;
  Main: undefined;
  Chat: undefined;
  FlightResults: undefined;
  FlightDetails: { flightId: string };
  Payment: { method: PaymentMethod };
  Tickets: undefined;
  TicketDetail: { ticketId: string };
  Settings: undefined;
};

export type AuthStackParamList = {
  Welcome: undefined;
  Terms: undefined;
  AuthChoice: undefined;
};

export type TabParamList = {
  Chat: undefined;
  Tickets: undefined;
  Settings: undefined;
};

// Navigation hook types
export interface NavigationState {
  hasCompletedOnboarding: boolean;
  currentRoute: string;
  isDeepLink: boolean;
  deepLinkUrl?: string;
}

export interface NavigationStore extends NavigationState {
  setHasCompletedOnboarding: (completed: boolean) => void;
  setCurrentRoute: (route: string) => void;
  setDeepLink: (url: string) => void;
  clearDeepLink: () => void;
  initializeNavigation: () => Promise<void>;
}

// Screen component props
export interface ScreenProps {
  navigation: any;
  route: any;
}

export interface OnboardingScreenProps extends ScreenProps {
  onNext?: () => void;
  onSkip?: () => void;
  onComplete?: () => void;
}

// Theme and UI related types
export type Theme = 'light' | 'dark';

export interface ThemeColors {
  // Primary Colors
  primary: string;
  primaryDark: string;
  primaryLight: string;
  
  // Secondary Colors
  secondary: string;
  secondaryDark: string;
  secondaryLight: string;
  
  // Background Colors
  background: string;
  surface: string;
  card: string;
  
  // Text Colors
  text: string;
  textSecondary: string;
  textOnPrimary: string;
  
  // Border Colors
  border: string;
  divider: string;
  
  // State Colors
  success: string;
  warning: string;
  error: string;
  info: string;
  
  // Message Colors
  userMessage: string;
  botMessage: string;
  userMessageText: string;
  botMessageText: string;
}

export interface ThemeContextType {
  theme: Theme;
  colors: ThemeColors;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  isLoading: boolean;
}

// Component prop types
export interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'text';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  style?: any;
  accessibilityLabel?: string;
}

export interface InputProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  keyboardType?: 'default' | 'email-address' | 'numeric' | 'phone-pad';
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  autoCorrect?: boolean;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  leftIcon?: string;
  rightIcon?: string;
  onRightIconPress?: () => void;
  style?: any;
  accessibilityLabel?: string;
}

export interface CardProps {
  children: React.ReactNode;
  variant?: 'elevated' | 'outlined' | 'flat';
  padding?: 'none' | 'small' | 'medium' | 'large';
  onPress?: () => void;
  style?: any;
}

export interface TypographyProps {
  children: React.ReactNode;
  variant?: 'h1' | 'h2' | 'h3' | 'body' | 'caption' | 'label';
  color?: string;
  align?: 'left' | 'center' | 'right';
  numberOfLines?: number;
  style?: any;
}

export interface LoadingProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  style?: any;
}