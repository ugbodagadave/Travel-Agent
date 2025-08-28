import React from 'react';
import { View, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { CardProps } from '../../types';
import { useTheme } from '../theme/ThemeContext';
import { SPACING } from '../../constants';

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'elevated',
  padding = 'medium',
  onPress,
  style,
}) => {
  const { colors } = useTheme();

  // Get card styles based on variant
  const getCardStyles = () => {
    const baseStyle = {
      borderRadius: 12,
      backgroundColor: colors.card,
    };

    // Padding styles
    const paddingStyles = {
      none: {},
      small: { padding: SPACING.sm },
      medium: { padding: SPACING.md },
      large: { padding: SPACING.lg },
    };

    // Variant styles
    const variantStyles = {
      elevated: {
        ...Platform.select({
          ios: {
            shadowColor: colors.text,
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.1,
            shadowRadius: 8,
          },
          android: {
            elevation: 4,
          },
        }),
      },
      outlined: {
        borderWidth: 1,
        borderColor: colors.border,
      },
      flat: {
        backgroundColor: colors.surface,
      },
    };

    return {
      ...baseStyle,
      ...paddingStyles[padding],
      ...variantStyles[variant],
    };
  };

  const cardStyles = getCardStyles();

  // If onPress is provided, render as TouchableOpacity
  if (onPress) {
    return (
      <TouchableOpacity
        style={[cardStyles, style]}
        onPress={onPress}
        accessibilityRole="button"
        activeOpacity={0.8}
      >
        {children}
      </TouchableOpacity>
    );
  }

  // Otherwise, render as View
  return (
    <View style={[cardStyles, style]}>
      {children}
    </View>
  );
};

export default Card;