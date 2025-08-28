import React from 'react';
import { Text, StyleSheet } from 'react-native';
import { TypographyProps } from '../../types';
import { useTheme } from '../theme/ThemeContext';
import { FONT_SIZES, FONTS, COLORS } from '../../constants';

export const Typography: React.FC<TypographyProps> = ({
  children,
  variant = 'body',
  color,
  align = 'left',
  numberOfLines,
  style,
}) => {
  // Safe theme hook usage with fallback
  let colors;
  try {
    const theme = useTheme();
    colors = theme.colors;
  } catch (error) {
    // Fallback colors when theme context is not available
    colors = {
      text: COLORS.gray900,
      textSecondary: COLORS.gray600,
    };
  }

  // Get text styles based on variant
  const getTextStyles = () => {
    const variantStyles = {
      h1: {
        fontSize: FONT_SIZES['4xl'],
        fontWeight: 'bold' as const,
        lineHeight: FONT_SIZES['4xl'] * 1.2,
        marginBottom: 8,
      },
      h2: {
        fontSize: FONT_SIZES['3xl'],
        fontWeight: 'bold' as const,
        lineHeight: FONT_SIZES['3xl'] * 1.2,
        marginBottom: 6,
      },
      h3: {
        fontSize: FONT_SIZES['2xl'],
        fontWeight: '600' as const,
        lineHeight: FONT_SIZES['2xl'] * 1.3,
        marginBottom: 4,
      },
      body: {
        fontSize: FONT_SIZES.base,
        fontWeight: 'normal' as const,
        lineHeight: FONT_SIZES.base * 1.4,
      },
      caption: {
        fontSize: FONT_SIZES.sm,
        fontWeight: 'normal' as const,
        lineHeight: FONT_SIZES.sm * 1.4,
        color: colors.textSecondary,
      },
      label: {
        fontSize: FONT_SIZES.sm,
        fontWeight: '600' as const,
        lineHeight: FONT_SIZES.sm * 1.3,
        textTransform: 'uppercase' as const,
        letterSpacing: 0.5,
      },
    };

    return variantStyles[variant];
  };

  const textStyles = getTextStyles();
  const textColor = color || (textStyles as any).color || colors.text;

  return (
    <Text
      style={[
        styles.base,
        textStyles,
        {
          color: textColor,
          textAlign: align,
          fontFamily: FONTS.regular,
        },
        style,
      ]}
      numberOfLines={numberOfLines}
      accessibilityRole="text"
    >
      {children}
    </Text>
  );
};

const styles = StyleSheet.create({
  base: {
    includeFontPadding: false,
  },
});

// Export convenience components
export const Heading1: React.FC<Omit<TypographyProps, 'variant'>> = (props) => (
  <Typography {...props} variant="h1" />
);

export const Heading2: React.FC<Omit<TypographyProps, 'variant'>> = (props) => (
  <Typography {...props} variant="h2" />
);

export const Heading3: React.FC<Omit<TypographyProps, 'variant'>> = (props) => (
  <Typography {...props} variant="h3" />
);

export const Body: React.FC<Omit<TypographyProps, 'variant'>> = (props) => (
  <Typography {...props} variant="body" />
);

export const Caption: React.FC<Omit<TypographyProps, 'variant'>> = (props) => (
  <Typography {...props} variant="caption" />
);

export const Label: React.FC<Omit<TypographyProps, 'variant'>> = (props) => (
  <Typography {...props} variant="label" />
);

export default Typography;