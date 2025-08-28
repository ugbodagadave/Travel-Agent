import React, { useEffect } from 'react';
import { NavigationContainer, DefaultTheme, DarkTheme } from '@react-navigation/native';
import { LinkingOptions } from '@react-navigation/native';
import { View, ActivityIndicator } from 'react-native';
import { linking } from './linking';
import { useTheme } from '../components/theme';
import { useNavigationStore } from '../stores';
import StackNavigator from './StackNavigator';
import { RootStackParamList } from '../types';

export default function Navigation() {
  const { theme, colors, isLoading } = useTheme();
  const { initializeNavigation } = useNavigationStore();

  useEffect(() => {
    initializeNavigation();
  }, [initializeNavigation]);

  // Show loading screen while theme is initializing
  if (isLoading) {
    return (
      <View style={{ 
        flex: 1, 
        justifyContent: 'center', 
        alignItems: 'center',
        backgroundColor: '#FFFFFF' // fallback background
      }}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  // Create custom navigation theme based on app theme
  const navigationTheme = {
    ...(theme === 'dark' ? DarkTheme : DefaultTheme),
    colors: {
      ...(theme === 'dark' ? DarkTheme.colors : DefaultTheme.colors),
      primary: colors.primary,
      background: colors.background,
      card: colors.surface,
      text: colors.text,
      border: colors.border,
      notification: colors.primary,
    },
  };

  const onStateChange = (state: any) => {
    // Track navigation state changes for analytics
    if (state) {
      const currentRoute = getCurrentRouteName(state);
      if (currentRoute) {
        // Log navigation events
        console.log('Navigation state changed to:', currentRoute);
      }
    }
  };

  return (
    <NavigationContainer
      theme={navigationTheme}
      linking={linking}
      onStateChange={onStateChange}
      onReady={() => {
        console.log('Navigation container ready');
      }}
    >
      <StackNavigator />
    </NavigationContainer>
  );
}

// Helper function to get current route name
function getCurrentRouteName(state: any): string | undefined {
  if (!state || typeof state.index !== 'number') {
    return undefined;
  }

  const route = state.routes[state.index];

  if (route.state) {
    return getCurrentRouteName(route.state);
  }

  return route.name;
}

export { getCurrentRouteName };