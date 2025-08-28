import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Dimensions, Platform } from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { SPACING, FONT_SIZES, ANIMATION_DURATION } from '../../constants';

const { width: screenWidth } = Dimensions.get('window');

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  visible: boolean;
  message: string;
  type?: ToastType;
  duration?: number;
  onHide?: () => void;
  position?: 'top' | 'bottom';
}

export const Toast: React.FC<ToastProps> = ({
  visible,
  message,
  type = 'info',
  duration = 3000,
  onHide,
  position = 'top',
}) => {
  const { colors } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const translateAnim = useRef(new Animated.Value(position === 'top' ? -100 : 100)).current;

  useEffect(() => {
    if (visible) {
      // Show animation
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: ANIMATION_DURATION.fast,
          useNativeDriver: true,
        }),
        Animated.timing(translateAnim, {
          toValue: 0,
          duration: ANIMATION_DURATION.fast,
          useNativeDriver: true,
        }),
      ]).start();

      // Auto hide after duration
      const timer = setTimeout(() => {
        hideToast();
      }, duration);

      return () => clearTimeout(timer);
    } else {
      hideToast();
    }
  }, [visible]);

  const hideToast = () => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: ANIMATION_DURATION.fast,
        useNativeDriver: true,
      }),
      Animated.timing(translateAnim, {
        toValue: position === 'top' ? -100 : 100,
        duration: ANIMATION_DURATION.fast,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onHide?.();
    });
  };

  const getToastColors = () => {
    switch (type) {
      case 'success':
        return {
          backgroundColor: colors.success,
          textColor: colors.textOnPrimary,
        };
      case 'error':
        return {
          backgroundColor: colors.error,
          textColor: colors.textOnPrimary,
        };
      case 'warning':
        return {
          backgroundColor: colors.warning,
          textColor: colors.textOnPrimary,
        };
      case 'info':
      default:
        return {
          backgroundColor: colors.info,
          textColor: colors.textOnPrimary,
        };
    }
  };

  const toastColors = getToastColors();

  const containerStyle = [
    styles.container,
    position === 'top' ? styles.topContainer : styles.bottomContainer,
  ];

  return (
    <Animated.View
      style={[
        containerStyle,
        {
          opacity: fadeAnim,
          transform: [{ translateY: translateAnim }],
        },
      ]}
      pointerEvents={visible ? 'auto' : 'none'}
    >
      <View
        style={[
          styles.toast,
          {
            backgroundColor: toastColors.backgroundColor,
          },
        ]}
      >
        <Text
          style={[
            styles.message,
            {
              color: toastColors.textColor,
            },
          ]}
          numberOfLines={3}
        >
          {message}
        </Text>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: SPACING.md,
    right: SPACING.md,
    zIndex: 9999,
  },
  topContainer: {
    top: Platform.OS === 'ios' ? 60 : 40,
  },
  bottomContainer: {
    bottom: Platform.OS === 'ios' ? 40 : 20,
  },
  toast: {
    borderRadius: 12,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    maxWidth: screenWidth - (SPACING.md * 2),
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  message: {
    fontSize: FONT_SIZES.base,
    fontWeight: '500',
    textAlign: 'center',
    lineHeight: FONT_SIZES.base * 1.4,
  },
});

export default Toast;