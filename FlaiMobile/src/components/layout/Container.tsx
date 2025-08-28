import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { SPACING } from '../../constants';

interface ContainerProps {
  children: React.ReactNode;
  padding?: 'none' | 'small' | 'medium' | 'large';
  scrollable?: boolean;
  backgroundColor?: string;
  style?: any;
}

export const Container: React.FC<ContainerProps> = ({
  children,
  padding = 'medium',
  scrollable = false,
  backgroundColor,
  style,
}) => {
  const { colors } = useTheme();

  // Get padding styles
  const getPaddingStyles = () => {
    switch (padding) {
      case 'none':
        return {};
      case 'small':
        return { padding: SPACING.sm };
      case 'medium':
        return { padding: SPACING.md };
      case 'large':
        return { padding: SPACING.lg };
      default:
        return { padding: SPACING.md };
    }
  };

  const containerStyle = {
    backgroundColor: backgroundColor || colors.background,
    ...getPaddingStyles(),
  };

  if (scrollable) {
    return (
      <ScrollView
        style={[styles.scrollContainer, containerStyle, style]}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {children}
      </ScrollView>
    );
  }

  return (
    <View style={[styles.container, containerStyle, style]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
});

export default Container;