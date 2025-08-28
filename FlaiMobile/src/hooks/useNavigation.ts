import { useNavigation as useRNNavigation, useRoute as useRNRoute } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { RootStackParamList, TabParamList, AuthStackParamList } from '../types';

// Type-safe navigation hooks
export function useNavigation<T extends keyof RootStackParamList = keyof RootStackParamList>() {
  return useRNNavigation<StackNavigationProp<RootStackParamList, T>>();
}

export function useTabNavigation<T extends keyof TabParamList = keyof TabParamList>() {
  return useRNNavigation<BottomTabNavigationProp<TabParamList, T>>();
}

export function useAuthNavigation<T extends keyof AuthStackParamList = keyof AuthStackParamList>() {
  return useRNNavigation<StackNavigationProp<AuthStackParamList, T>>();
}

export function useRoute<T extends keyof RootStackParamList>() {
  return useRNRoute<{ key: string; name: T; params: RootStackParamList[T] }>();
}

// Navigation utilities
export const NavigationUtils = {
  // Navigate to chat with optional pre-filled message
  navigateToChat: (navigation: any, message?: string) => {
    navigation.navigate('Chat');
    // If message provided, could trigger chat input pre-fill
  },

  // Navigate to flight details
  navigateToFlightDetails: (navigation: any, flightId: string) => {
    navigation.navigate('FlightDetails', { flightId });
  },

  // Navigate to payment with method
  navigateToPayment: (navigation: any, method: 'card' | 'usdc' | 'circlelayer') => {
    navigation.navigate('Payment', { method });
  },

  // Navigate to ticket details
  navigateToTicketDetails: (navigation: any, ticketId: string) => {
    navigation.navigate('TicketDetail', { ticketId });
  },

  // Reset to main app (after onboarding)
  resetToMain: (navigation: any) => {
    navigation.reset({
      index: 0,
      routes: [{ name: 'Main' }],
    });
  },

  // Reset to auth flow
  resetToAuth: (navigation: any) => {
    navigation.reset({
      index: 0,
      routes: [{ name: 'Auth' }],
    });
  },

  // Go back with fallback
  goBackWithFallback: (navigation: any, fallbackRoute: string) => {
    if (navigation.canGoBack()) {
      navigation.goBack();
    } else {
      navigation.navigate(fallbackRoute);
    }
  },

  // Navigate to tab and specific screen
  navigateToTab: (navigation: any, tab: keyof TabParamList) => {
    navigation.navigate('Main', { screen: tab });
  },
};

// Route name utilities
export const RouteUtils = {
  // Check if current route is in auth flow
  isAuthFlow: (routeName: string): boolean => {
    const authRoutes = ['Welcome', 'Terms', 'AuthChoice'];
    return authRoutes.includes(routeName);
  },

  // Check if current route is in main app
  isMainApp: (routeName: string): boolean => {
    const mainRoutes = ['Chat', 'Tickets', 'Settings', 'FlightResults', 'FlightDetails', 'Payment', 'TicketDetail'];
    return mainRoutes.includes(routeName);
  },

  // Check if current route is a modal/overlay
  isModalRoute: (routeName: string): boolean => {
    const modalRoutes = ['Payment', 'FlightDetails', 'TicketDetail'];
    return modalRoutes.includes(routeName);
  },

  // Get tab name from route
  getTabFromRoute: (routeName: string): keyof TabParamList | null => {
    const tabRoutes: Record<string, keyof TabParamList> = {
      'Chat': 'Chat',
      'Tickets': 'Tickets',
      'Settings': 'Settings',
    };
    return tabRoutes[routeName] || null;
  },
};

// Deep linking utilities
export const DeepLinkUtils = {
  // Parse flight deep link
  parseFlightLink: (url: string): { flightId?: string } | null => {
    const match = url.match(/\/flight\/([^\/\?]+)/);
    return match ? { flightId: match[1] } : null;
  },

  // Parse payment deep link
  parsePaymentLink: (url: string): { method?: 'card' | 'usdc' | 'circlelayer' } | null => {
    const match = url.match(/\/payment\/([^\/\?]+)/);
    const method = match?.[1] as 'card' | 'usdc' | 'circlelayer';
    return method ? { method } : null;
  },

  // Parse ticket deep link
  parseTicketLink: (url: string): { ticketId?: string } | null => {
    const match = url.match(/\/ticket\/([^\/\?]+)/);
    return match ? { ticketId: match[1] } : null;
  },

  // Build deep link URLs
  buildFlightLink: (flightId: string): string => {
    return `flai://flight/${flightId}`;
  },

  buildPaymentLink: (method: 'card' | 'usdc' | 'circlelayer'): string => {
    return `flai://payment/${method}`;
  },

  buildTicketLink: (ticketId: string): string => {
    return `flai://ticket/${ticketId}`;
  },
};

// Navigation state utilities
export const NavigationStateUtils = {
  // Track screen views for analytics
  trackScreenView: (screenName: string, params?: any) => {
    console.log(`Screen viewed: ${screenName}`, params);
    // TODO: Integrate with analytics service
  },

  // Track navigation events
  trackNavigation: (action: string, from: string, to: string) => {
    console.log(`Navigation: ${action} from ${from} to ${to}`);
    // TODO: Integrate with analytics service
  },
};