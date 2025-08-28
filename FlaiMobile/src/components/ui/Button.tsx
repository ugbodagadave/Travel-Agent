import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator, View } from 'react-native';
import { ButtonProps } from '../../types';
import { useTheme } from '../theme/ThemeContext';
import { FONT_SIZES, SPACING, ANIMATION_DURATION, COLORS } from '../../constants';

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  style,
  accessibilityLabel,
}) => {
  // Safe theme hook usage with fallback
  let colors;
  try {
    const theme = useTheme();
    colors = theme.colors;
  } catch (error) {
    // Fallback colors when theme context is not available
    colors = {
      primary: COLORS.primary,
      secondary: COLORS.secondary,
      border: COLORS.gray200,
      textSecondary: COLORS.gray600,
      textOnPrimary: COLORS.white,
    };
  }

  // Create styles based on variant
  const getButtonStyles = () => {
    const baseStyle = {
      borderRadius: 8,
      borderWidth: 1,
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      justifyContent: 'center' as const,
    };

    // Size-specific styles
    const sizeStyles = {
      small: {
        paddingVertical: SPACING.xs,
        paddingHorizontal: SPACING.sm,
        minHeight: 32,
      },
      medium: {
        paddingVertical: SPACING.sm,
        paddingHorizontal: SPACING.md,
        minHeight: 44,
      },
      large: {
        paddingVertical: SPACING.md,
        paddingHorizontal: SPACING.lg,
        minHeight: 52,
      },
    };

    // Variant-specific styles
    const variantStyles = {
      primary: {
        backgroundColor: disabled ? colors.border : colors.primary,
        borderColor: disabled ? colors.border : colors.primary,
      },
      secondary: {
        backgroundColor: disabled ? colors.border : colors.secondary,
        borderColor: disabled ? colors.border : colors.secondary,
      },
      outline: {
        backgroundColor: 'transparent',
        borderColor: disabled ? colors.border : colors.primary,
      },
      text: {
        backgroundColor: 'transparent',
        borderColor: 'transparent',
      },
    };

    return {
      ...baseStyle,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };
  };

  // Get text color based on variant
  const getTextColor = () => {
    if (disabled) {
      return colors.textSecondary;
    }

    switch (variant) {
      case 'primary':
      case 'secondary':
        return colors.textOnPrimary;
      case 'outline':
      case 'text':
        return colors.primary;
      default:
        return colors.textOnPrimary;
    }
  };

  // Get font size based on size
  const getFontSize = () => {
    switch (size) {
      case 'small':
        return FONT_SIZES.sm;
      case 'medium':
        return FONT_SIZES.base;
      case 'large':
        return FONT_SIZES.lg;
      default:
        return FONT_SIZES.base;
    }
  };

  // Handle press
  const handlePress = () => {
    if (!disabled && !loading) {
      onPress();
    }
  };

  const buttonStyles = getButtonStyles();
  const textColor = getTextColor();
  const fontSize = getFontSize();

  return (
    <TouchableOpacity
      style={[buttonStyles, style]}
      onPress={handlePress}
      disabled={disabled || loading}
      accessibilityLabel={accessibilityLabel || title}
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={textColor}
          style={{ marginRight: title ? SPACING.xs : 0 }}
        />
      ) : null}
      
      {title ? (
        <Text
          style={[
            styles.text,
            {
              color: textColor,
              fontSize,
              marginLeft: loading ? SPACING.xs : 0,
            },
          ]}
        >
          {title}
        </Text>
      ) : null}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  text: {
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default Button;