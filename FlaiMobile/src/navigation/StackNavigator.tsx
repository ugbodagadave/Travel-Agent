import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { RootStackParamList } from '../types';
import { useTheme } from '../components/theme';
import { useAuthStore, useNavigationStore } from '../stores';

// Import navigators
import AuthNavigator from './AuthNavigator';
import TabNavigator from './TabNavigator';

// Import additional screens
import {
  ChatScreen,
  SettingsScreen,
  TicketsScreen,
  FlightResultsScreen,
  FlightDetailsScreen,
  PaymentScreen,
  TicketDetailScreen
} from '../screens';

const Stack = createStackNavigator<RootStackParamList>();

export default function StackNavigator() {
  const { colors } = useTheme();
  const { isAuthenticated } = useAuthStore();
  const { hasCompletedOnboarding } = useNavigationStore();

  const showAuthFlow = !hasCompletedOnboarding;

  return (
    <Stack.Navigator
      initialRouteName={showAuthFlow ? 'Auth' : 'Main'}
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.surface,
          borderBottomColor: colors.border,
          borderBottomWidth: 1,
        },
        headerTintColor: colors.text,
        headerTitleStyle: {
          fontWeight: '600',
          fontSize: 18,
        },
        gestureEnabled: true,
        gestureDirection: 'horizontal',
        transitionSpec: {
          open: {
            animation: 'timing',
            config: {
              duration: 300,
            },
          },
          close: {
            animation: 'timing',
            config: {
              duration: 300,
            },
          },
        },
      }}
    >
      {showAuthFlow ? (
        <Stack.Screen
          name="Auth"
          component={AuthNavigator}
          options={{
            headerShown: false,
          }}
        />
      ) : (
        <>
          <Stack.Screen
            name="Main"
            component={TabNavigator}
            options={{
              headerShown: false,
            }}
          />
          
          <Stack.Screen
            name="Chat"
            component={ChatScreen}
            options={{
              title: 'Chat',
              headerShown: true,
            }}
          />
          
          <Stack.Screen
            name="FlightResults"
            component={FlightResultsScreen}
            options={{
              title: 'Flight Results',
              headerShown: true,
            }}
          />
          
          <Stack.Screen
            name="FlightDetails"
            component={FlightDetailsScreen}
            options={{
              title: 'Flight Details',
              headerShown: true,
            }}
          />
          
          <Stack.Screen
            name="Payment"
            component={PaymentScreen}
            options={{
              title: 'Payment',
              headerShown: true,
            }}
          />
          
          <Stack.Screen
            name="Tickets"
            component={TicketsScreen}
            options={{
              title: 'My Tickets',
              headerShown: true,
            }}
          />
          
          <Stack.Screen
            name="TicketDetail"
            component={TicketDetailScreen}
            options={{
              title: 'Ticket Details',
              headerShown: true,
            }}
          />
          
          <Stack.Screen
            name="Settings"
            component={SettingsScreen}
            options={{
              title: 'Settings',
              headerShown: true,
            }}
          />
        </>
      )}
    </Stack.Navigator>
  );
}