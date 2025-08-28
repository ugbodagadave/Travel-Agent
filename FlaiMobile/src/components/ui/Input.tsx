import React, { useState } from 'react';
import { TextInput, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { InputProps } from '../../types';
import { useTheme } from '../theme/ThemeContext';
import { FONT_SIZES, SPACING } from '../../constants';

export const Input: React.FC<InputProps> = ({
  value,
  onChangeText,
  placeholder,
  secureTextEntry = false,
  keyboardType = 'default',
  autoCapitalize = 'sentences',
  autoCorrect = true,
  error,
  helperText,
  disabled = false,
  leftIcon,
  rightIcon,
  onRightIconPress,
  style,
  accessibilityLabel,
}) => {
  const { colors } = useTheme();
  const [isFocused, setIsFocused] = useState(false);

  // Get container styles based on state
  const getContainerStyles = () => {
    const baseStyle = {
      borderWidth: 1,
      borderRadius: 8,
      backgroundColor: colors.surface,
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      paddingHorizontal: SPACING.sm,
      minHeight: 44,
    };

    if (disabled) {
      return {
        ...baseStyle,
        backgroundColor: colors.divider,
        borderColor: colors.border,
        opacity: 0.6,
      };
    }

    if (error) {
      return {
        ...baseStyle,
        borderColor: colors.error,
      };
    }

    if (isFocused) {
      return {
        ...baseStyle,
        borderColor: colors.primary,
        borderWidth: 2,
      };
    }

    return {
      ...baseStyle,
      borderColor: colors.border,
    };
  };

  // Get text color
  const getTextColor = () => {
    if (disabled) {
      return colors.textSecondary;
    }
    return colors.text;
  };

  // Handle focus
  const handleFocus = () => {
    setIsFocused(true);
  };

  // Handle blur
  const handleBlur = () => {
    setIsFocused(false);
  };

  const containerStyles = getContainerStyles();
  const textColor = getTextColor();

  return (
    <View style={[styles.wrapper, style]}>
      <View style={containerStyles}>
        {/* Left Icon */}
        {leftIcon && (
          <View style={styles.iconContainer}>
            {/* Note: In a real app, you'd use an icon library like react-native-vector-icons */}
            <Text style={[styles.icon, { color: colors.textSecondary }]}>{leftIcon}</Text>
          </View>
        )}

        {/* Text Input */}
        <TextInput
          style={[
            styles.input,
            {
              color: textColor,
              fontSize: FONT_SIZES.base,
            },
          ]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.textSecondary}
          secureTextEntry={secureTextEntry}
          keyboardType={keyboardType}
          autoCapitalize={autoCapitalize}
          autoCorrect={autoCorrect}
          editable={!disabled}
          onFocus={handleFocus}
          onBlur={handleBlur}
          accessibilityLabel={accessibilityLabel || placeholder}
          accessibilityState={{ disabled }}
        />

        {/* Right Icon */}
        {rightIcon && (
          <TouchableOpacity
            style={styles.iconContainer}
            onPress={onRightIconPress}
            disabled={!onRightIconPress}
            accessibilityRole="button"
            accessibilityLabel={`${rightIcon} button`}
          >
            <Text style={[styles.icon, { color: colors.textSecondary }]}>{rightIcon}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Helper Text or Error */}
      {(helperText || error) && (
        <Text
          style={[
            styles.helperText,
            {
              color: error ? colors.error : colors.textSecondary,
              fontSize: FONT_SIZES.sm,
            },
          ]}
        >
          {error || helperText}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: SPACING.sm,
  },
  input: {
    flex: 1,
    paddingVertical: SPACING.sm,
    paddingHorizontal: 0,
  },
  iconContainer: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: SPACING.xs,
  },
  icon: {
    fontSize: 18,
  },
  helperText: {
    marginTop: SPACING.xs,
    marginLeft: SPACING.xs,
  },
});

export default Input;