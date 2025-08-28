import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StyleSheet } from 'react-native';
import { TabParamList } from '../types';
import { useTheme } from '../components/theme';
import { Typography } from '../components/ui';
import { SPACING, TAB_BAR_HEIGHT } from '../constants';
import { Ionicons } from '@expo/vector-icons';

// Import main app screens
import ChatScreen from '../screens/ChatScreen';
import SettingsScreen from '../screens/SettingsScreen';
import TicketsScreen from '../screens/TicketsScreen'; // Placeholder for now

const Tab = createBottomTabNavigator<TabParamList>();

interface TabIconProps {
  name: keyof typeof Ionicons.glyphMap;
  focused: boolean;
  color: string;
  size: number;
}

function TabIcon({ name, focused, color, size }: TabIconProps) {
  return (
    <Ionicons 
      name={name} 
      size={size} 
      color={color}
      style={{
        marginBottom: -3,
      }}
    />
  );
}

interface TabLabelProps {
  children: string;
  focused: boolean;
  color: string;
}

function TabLabel({ children, focused, color }: TabLabelProps) {
  return (
    <Typography
      variant="caption"
      style={[
        styles.tabLabel,
        { 
          color,
          fontWeight: focused ? '600' : '400',
        },
      ]}
    >
      {children}
    </Typography>
  );
}

export default function TabNavigator() {
  const { colors } = useTheme();

  return (
    <Tab.Navigator
      initialRouteName="Chat"
      screenOptions={{
        headerShown: false,
        tabBarStyle: [
          styles.tabBar,
          {
            backgroundColor: colors.surface,
            borderTopColor: colors.border,
            height: TAB_BAR_HEIGHT,
          },
        ],
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarLabelStyle: styles.tabLabelStyle,
        tabBarIconStyle: styles.tabIconStyle,
        tabBarItemStyle: styles.tabItemStyle,
        tabBarAccessibilityLabel: 'Main navigation tabs',
      }}
    >
      <Tab.Screen
        name="Chat"
        component={ChatScreen}
        options={{
          tabBarLabel: ({ focused, color }) => (
            <TabLabel focused={focused} color={color}>
              Chat
            </TabLabel>
          ),
          tabBarIcon: ({ focused, color, size }) => (
            <TabIcon
              name={focused ? 'chatbubble' : 'chatbubble-outline'}
              focused={focused}
              color={color}
              size={size}
            />
          ),
          tabBarAccessibilityLabel: 'Chat with AI travel agent',
        }}
      />
      
      <Tab.Screen
        name="Tickets"
        component={TicketsScreen}
        options={{
          tabBarLabel: ({ focused, color }) => (
            <TabLabel focused={focused} color={color}>
              Tickets
            </TabLabel>
          ),
          tabBarIcon: ({ focused, color, size }) => (
            <TabIcon
              name={focused ? 'airplane' : 'airplane-outline'}
              focused={focused}
              color={color}
              size={size}
            />
          ),
          tabBarAccessibilityLabel: 'View your flight tickets',
        }}
      />
      
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarLabel: ({ focused, color }) => (
            <TabLabel focused={focused} color={color}>
              Settings
            </TabLabel>
          ),
          tabBarIcon: ({ focused, color, size }) => (
            <TabIcon
              name={focused ? 'settings' : 'settings-outline'}
              focused={focused}
              color={color}
              size={size}
            />
          ),
          tabBarAccessibilityLabel: 'App settings and preferences',
        }}
      />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    borderTopWidth: 1,
    paddingTop: SPACING.sm,
    paddingBottom: SPACING.md,
    paddingHorizontal: SPACING.sm,
  },
  tabLabelStyle: {
    fontSize: 12,
    marginTop: 4,
  },
  tabIconStyle: {
    marginBottom: 0,
  },
  tabItemStyle: {
    paddingVertical: SPACING.xs,
  },
  tabLabel: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 2,
  },
});