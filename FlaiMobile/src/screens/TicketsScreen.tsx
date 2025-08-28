import React from 'react';
import { View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Typography, Container } from '../components/ui';
import { ScreenWrapper, Header } from '../components/layout';
import { useTheme } from '../components/theme';
import { SPACING } from '../constants';
import { AccessibilityUtils } from '../utils';
import { Ionicons } from '@expo/vector-icons';

export default function TicketsScreen() {
  const { colors } = useTheme();

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <Header title="Tickets" />
        
        <Container style={styles.content}>
          <View style={styles.placeholderContainer}>
            <View style={[styles.iconContainer, { backgroundColor: colors.primaryLight }]}>
              <Ionicons
                name="airplane"
                size={64}
                color={colors.primary}
                accessibilityLabel="Tickets placeholder"
                accessibilityRole="image"
              />
            </View>
            
            <Typography
              variant="h3"
              style={[styles.title, { color: colors.text }]}
              align="center"
            >
              Your Tickets
            </Typography>
            
            <Typography
              variant="body"
              style={[styles.description, { color: colors.textSecondary }]}
              align="center"
            >
              Your flight tickets will appear here after you complete a booking. Start by chatting with our AI assistant to find and book flights.
            </Typography>
          </View>
        </Container>
      </SafeAreaView>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderContainer: {
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.xl,
  },
  title: {
    marginBottom: SPACING.md,
  },
  description: {
    lineHeight: 22,
    maxWidth: 300,
  },
});