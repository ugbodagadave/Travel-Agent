import { LinkingOptions } from '@react-navigation/native';
import { RootStackParamList } from '../types';

export const linking: LinkingOptions<RootStackParamList> = {
  prefixes: [
    'flai://',
    'https://flai.app',
    'https://app.flai.com',
  ],
  config: {
    screens: {
      Auth: {
        screens: {
          Welcome: 'welcome',
          Terms: 'terms',
          AuthChoice: 'auth',
        },
      },
      Main: {
        screens: {
          Chat: 'chat',
          Tickets: 'tickets',
          Settings: 'settings',
        },
      },
      Chat: 'chat',
      FlightResults: 'flights',
      FlightDetails: {
        path: 'flight/:flightId',
        parse: {
          flightId: (flightId: string) => flightId,
        },
      },
      Payment: {
        path: 'payment/:method',
        parse: {
          method: (method: string) => method as 'card' | 'usdc' | 'circlelayer',
        },
      },
      Tickets: 'tickets',
      TicketDetail: {
        path: 'ticket/:ticketId',
        parse: {
          ticketId: (ticketId: string) => ticketId,
        },
      },
      Settings: 'settings',
    },
  },
  async getInitialURL() {
    // Handle cold start deep links
    // This will be called when the app is opened from a deep link when it's not running
    return null;
  },
  subscribe(listener) {
    // Handle warm start deep links
    // This will be called when the app is already running and receives a deep link
    const onReceiveURL = ({ url }: { url: string }) => {
      listener(url);
    };

    // Listen for deep link events
    // Note: In a real app, you might use react-native-url-polyfill or similar
    // For now, we'll set up the basic structure
    
    return () => {
      // Cleanup listener
    };
  },
};