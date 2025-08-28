import React from 'react';
import { View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../types';
import { Typography, Container, Button } from '../components/ui';
import { ScreenWrapper, Header } from '../components/layout';
import { useTheme } from '../components/theme';
import { SPACING, PAYMENT_METHODS } from '../constants';
import { AccessibilityUtils } from '../utils';
import { Ionicons } from '@expo/vector-icons';

type PaymentScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Payment'>;
type PaymentScreenRouteProp = RouteProp<RootStackParamList, 'Payment'>;

interface Props {
  navigation: PaymentScreenNavigationProp;
  route: PaymentScreenRouteProp;
}

export default function PaymentScreen({ navigation, route }: Props) {
  const { colors } = useTheme();
  const { method } = route.params;
  
  const paymentMethod = PAYMENT_METHODS.find(pm => pm.id === method);
  const iconName = paymentMethod?.icon as keyof typeof Ionicons.glyphMap || 'card';

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <Header
          title="Payment"
          showBackButton
          onBackPress={() => navigation.goBack()}
        />
        
        <Container style={styles.content}>
          <View style={styles.placeholderContainer}>
            <View style={[styles.iconContainer, { backgroundColor: colors.primaryLight }]}>
              <Ionicons
                name={iconName}
                size={64}
                color={colors.primary}
                accessibilityLabel="Payment method"
                accessibilityRole="image"
              />
            </View>
            
            <Typography
              variant="h3"
              style={[styles.title, { color: colors.text }]}
              align="center"
            >
              {paymentMethod?.name || 'Payment'}
            </Typography>
            
            <Typography
              variant="body"
              style={[styles.description, { color: colors.textSecondary }]}
              align="center"
            >
              {paymentMethod?.description || `Payment processing for ${method} will be implemented here.`}
            </Typography>

            <Typography
              variant="caption"
              style={[styles.methodInfo, { color: colors.textSecondary }]}
              align="center"
            >
              Payment Method: {method}
            </Typography>

            <Button
              title="Back to Flight"
              onPress={() => navigation.goBack()}
              variant="primary"
              size="medium"
              style={styles.backButton}
              accessibilityLabel="Return to flight selection"
            />
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
    marginBottom: SPACING.md,
  },
  methodInfo: {
    marginBottom: SPACING.xl,
  },
  backButton: {
    marginTop: SPACING.md,
  },
});