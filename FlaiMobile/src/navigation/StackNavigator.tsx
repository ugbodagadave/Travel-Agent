import React, { useEffect } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { View, ActivityIndicator } from 'react-native';
import { RootStackParamList } from '../types';
import { useTheme } from '../components/theme';
import { useAuthStore, useNavigationStore } from '../stores';
import { Typography } from '../components/ui';

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
  const { isAuthenticated, isLoading, initializeAuth } = useAuthStore();
  const { hasCompletedOnboarding } = useNavigationStore();

  // Initialize authentication state on app start
  useEffect(() => {
    console.log('StackNavigator: Initializing authentication...');
    initializeAuth();
  }, [initializeAuth]);

  // Show loading screen while authentication is being initialized
  if (isLoading) {
    return (
      <View style={{ 
        flex: 1, 
        justifyContent: 'center', 
        alignItems: 'center',
        backgroundColor: colors.background
      }}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Typography
          variant="body"
          style={{ 
            marginTop: 16, 
            color: colors.textSecondary 
          }}
        >
          Initializing...
        </Typography>
      </View>
    );
  }

  // Determine which navigation flow to show
  const showAuthFlow = !hasCompletedOnboarding || !isAuthenticated;
  
  console.log('StackNavigator: Navigation state:', {
    hasCompletedOnboarding,
    isAuthenticated,
    showAuthFlow
  });

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