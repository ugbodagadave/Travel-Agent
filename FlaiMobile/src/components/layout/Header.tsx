import React from 'react';
import { View, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { HEADER_HEIGHT, SPACING, FONT_SIZES } from '../../constants';
import Typography from '../ui/Typography';

interface HeaderProps {
  title?: string;
  showBackButton?: boolean;
  onBackPress?: () => void;
  rightComponent?: React.ReactNode;
  leftComponent?: React.ReactNode;
  backgroundColor?: string;
  style?: any;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  showBackButton = false,
  onBackPress,
  rightComponent,
  leftComponent,
  backgroundColor,
  style,
}) => {
  const { colors } = useTheme();

  const containerStyle = {
    backgroundColor: backgroundColor || colors.surface,
    borderBottomColor: colors.border,
  };

  return (
    <View style={[styles.container, containerStyle, style]}>
      {/* Left Section */}
      <View style={styles.leftSection}>
        {showBackButton && onBackPress ? (
          <TouchableOpacity
            style={styles.backButton}
            onPress={onBackPress}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Typography style={[styles.backButtonText, { color: colors.primary }]}>
              ←
            </Typography>
          </TouchableOpacity>
        ) : null}
        {leftComponent}
      </View>

      {/* Center Section - Title */}
      <View style={styles.centerSection}>
        {title ? (
          <Typography
            variant="h3"
            numberOfLines={1}
            style={[styles.title, { color: colors.text }]}
          >
            {title}
          </Typography>
        ) : null}
      </View>

      {/* Right Section */}
      <View style={styles.rightSection}>
        {rightComponent}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: HEADER_HEIGHT,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    borderBottomWidth: Platform.OS === 'ios' ? StyleSheet.hairlineWidth : 0,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  leftSection: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  centerSection: {
    flex: 2,
    alignItems: 'center',
  },
  rightSection: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  backButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButtonText: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  title: {
    textAlign: 'center',
  },
});

export default Header;