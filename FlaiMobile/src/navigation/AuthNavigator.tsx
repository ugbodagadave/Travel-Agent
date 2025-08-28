import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { AuthStackParamList } from '../types';
import { useTheme } from '../components/theme';
import { Header } from '../components/layout';

// Import onboarding screens
import {
  WelcomeScreen,
  TermsScreen,
  AuthScreen
} from '../screens/onboarding';

const Stack = createStackNavigator<AuthStackParamList>();

export default function AuthNavigator() {
  const { colors } = useTheme();

  return (
    <Stack.Navigator
      initialRouteName="Welcome"
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
      <Stack.Screen
        name="Welcome"
        component={WelcomeScreen}
        options={{
          headerShown: false,
        }}
      />
      
      <Stack.Screen
        name="Terms"
        component={TermsScreen}
        options={{
          title: 'Terms & Privacy',
        }}
      />
      
      <Stack.Screen
        name="AuthChoice"
        component={AuthScreen}
        options={{
          title: 'Get Started',
        }}
      />
    </Stack.Navigator>
  );
}