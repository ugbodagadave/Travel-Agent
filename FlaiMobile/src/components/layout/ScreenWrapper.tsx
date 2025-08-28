import React from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../theme/ThemeContext';
import { SCREEN_PADDING } from '../../constants';

interface ScreenWrapperProps {
  children: React.ReactNode;
  padding?: boolean;
  keyboardAvoidingView?: boolean;
  backgroundColor?: string;
  statusBarStyle?: 'auto' | 'inverted' | 'light' | 'dark';
  style?: any;
}

export const ScreenWrapper: React.FC<ScreenWrapperProps> = ({
  children,
  padding = true,
  keyboardAvoidingView = false,
  backgroundColor,
  statusBarStyle = 'auto',
  style,
}) => {
  const { colors, theme } = useTheme();

  const getStatusBarStyle = () => {
    if (statusBarStyle === 'auto') {
      return theme === 'dark' ? 'light-content' : 'dark-content';
    }
    if (statusBarStyle === 'inverted') {
      return theme === 'dark' ? 'dark-content' : 'light-content';
    }
    return statusBarStyle === 'light' ? 'light-content' : 'dark-content';
  };

  const containerStyle = {
    backgroundColor: backgroundColor || colors.background,
  };

  const contentStyle = padding ? { padding: SCREEN_PADDING } : {};

  const content = (
    <SafeAreaView style={[styles.container, containerStyle, style]}>
      <StatusBar
        barStyle={getStatusBarStyle()}
        backgroundColor={backgroundColor || colors.background}
        translucent={false}
      />
      <View style={[styles.content, contentStyle]}>
        {children}
      </View>
    </SafeAreaView>
  );

  if (keyboardAvoidingView) {
    return (
      <KeyboardAvoidingView
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {content}
      </KeyboardAvoidingView>
    );
  }

  return content;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
});

export default ScreenWrapper;