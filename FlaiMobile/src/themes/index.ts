import { ThemeColors } from '../types';
import { COLORS } from '../constants';

// Light Theme Colors
export const lightTheme: ThemeColors = {
  // Primary Colors
  primary: COLORS.primary,
  primaryDark: COLORS.primaryDark,
  primaryLight: COLORS.primaryLight,
  
  // Secondary Colors
  secondary: COLORS.secondary,
  secondaryDark: COLORS.secondaryDark,
  secondaryLight: COLORS.secondaryLight,
  
  // Background Colors
  background: COLORS.white,
  surface: COLORS.white,
  card: COLORS.white,
  
  // Text Colors
  text: COLORS.gray900,
  textSecondary: COLORS.gray600,
  textOnPrimary: COLORS.white,
  
  // Border Colors
  border: COLORS.gray200,
  divider: COLORS.gray100,
  
  // State Colors
  success: COLORS.success,
  warning: COLORS.warning,
  error: COLORS.error,
  info: COLORS.info,
  
  // Message Colors
  userMessage: COLORS.userMessage,
  botMessage: COLORS.botMessage,
  userMessageText: COLORS.userMessageText,
  botMessageText: COLORS.botMessageText,
};

// Dark Theme Colors
export const darkTheme: ThemeColors = {
  // Primary Colors
  primary: COLORS.primary,
  primaryDark: COLORS.primaryDark,
  primaryLight: COLORS.primaryLight,
  
  // Secondary Colors
  secondary: COLORS.secondary,
  secondaryDark: COLORS.secondaryDark,
  secondaryLight: COLORS.secondaryLight,
  
  // Background Colors
  background: COLORS.gray900,
  surface: COLORS.gray800,
  card: COLORS.gray800,
  
  // Text Colors
  text: COLORS.white,
  textSecondary: COLORS.gray300,
  textOnPrimary: COLORS.white,
  
  // Border Colors
  border: COLORS.gray700,
  divider: COLORS.gray600,
  
  // State Colors
  success: COLORS.success,
  warning: COLORS.warning,
  error: COLORS.error,
  info: COLORS.info,
  
  // Message Colors
  userMessage: COLORS.userMessage,
  botMessage: COLORS.gray700,
  userMessageText: COLORS.white,
  botMessageText: COLORS.white,
};

// Export themes object
export const themes = {
  light: lightTheme,
  dark: darkTheme,
};