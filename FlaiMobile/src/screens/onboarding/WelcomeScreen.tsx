import React from 'react';
import { View, StyleSheet, ScrollView, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { AuthStackParamList } from '../../types';
import { 
  Typography, 
  Button
} from '../../components/ui';
import { ScreenWrapper, Container } from '../../components/layout';
import { useTheme } from '../../components/theme';
import { SPACING, APP_INFO } from '../../constants';
import { AccessibilityUtils } from '../../utils';

type WelcomeScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'Welcome'>;
type WelcomeScreenRouteProp = RouteProp<AuthStackParamList, 'Welcome'>;

interface Props {
  navigation: WelcomeScreenNavigationProp;
  route: WelcomeScreenRouteProp;
}

const { width: screenWidth } = Dimensions.get('window');

export default function WelcomeScreen({ navigation }: Props) {
  const { colors } = useTheme();

  const handleGetStarted = () => {
    navigation.navigate('Terms');
  };

  const handleSkip = () => {
    // Navigate directly to auth choice for quick access
    navigation.navigate('AuthChoice');
  };

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          accessibilityLabel="Welcome screen content"
        >
          <Container style={styles.content}>
            {/* App Icon/Logo */}
            <View style={[styles.iconContainer, { backgroundColor: colors.primaryLight }]}>
              <Ionicons
                name="airplane"
                size={64}
                color={colors.primary}
                accessibilityLabel="Flai app logo"
              />
            </View>

            {/* App Title */}
            <Typography
              variant="h1"
              style={[styles.title, { color: colors.text }]}
            >
              Welcome to {APP_INFO.name}
            </Typography>

            {/* App Description */}
            <Typography
              variant="body"
              style={[styles.description, { color: colors.textSecondary }]}
              align="center"
            >
              {APP_INFO.description}. Book flights with natural language conversations, 
              pay with cards, cryptocurrency, or blockchain tokens.
            </Typography>

            {/* Features List */}
            <View style={styles.featuresContainer}>
              <FeatureItem
                icon="chatbubble-ellipses"
                title="Conversational Booking"
                description="Just tell us where you want to go, and we'll handle the rest"
                colors={colors}
              />
              
              <FeatureItem
                icon="card"
                title="Flexible Payments"
                description="Pay with credit cards, USDC, or Circle Layer tokens"
                colors={colors}
              />
              
              <FeatureItem
                icon="shield-checkmark"
                title="Secure & Fast"
                description="Your data is protected with enterprise-grade security"
                colors={colors}
              />
            </View>
          </Container>

          {/* Action Buttons */}
          <View style={[styles.buttonContainer, { backgroundColor: colors.background }]}>
            <Button
              title="Get Started"
              onPress={handleGetStarted}
              variant="primary"
              size="large"
              style={styles.primaryButton}
              accessibilityLabel="Get started with onboarding"
            />
            
            <Button
              title="Skip"
              onPress={handleSkip}
              variant="text"
              size="medium"
              style={styles.skipButton}
              accessibilityLabel="Skip onboarding"
            />
          </View>
        </ScrollView>
      </SafeAreaView>
    </ScreenWrapper>
  );
}

interface FeatureItemProps {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  description: string;
  colors: any;
}

function FeatureItem({ icon, title, description, colors }: FeatureItemProps) {
  return (
    <View 
      style={styles.featureItem}
      accessibilityLabel={`Feature: ${title}`}
    >
      <View style={[styles.featureIcon, { backgroundColor: colors.surface }]}>
        <Ionicons
          name={icon}
          size={24}
          color={colors.primary}
          accessibilityLabel={`${title} icon`}
        />
      </View>
      
      <View style={styles.featureContent}>
        <Typography
          variant="label"
          style={[styles.featureTitle, { color: colors.text }]}
        >
          {title}
        </Typography>
        
        <Typography
          variant="caption"
          style={[styles.featureDescription, { color: colors.textSecondary }]}
        >
          {description}
        </Typography>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.xl,
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
    textAlign: 'center',
    marginBottom: SPACING.md,
    paddingHorizontal: SPACING.md,
  },
  description: {
    textAlign: 'center',
    marginBottom: SPACING.xl,
    paddingHorizontal: SPACING.lg,
    lineHeight: 24,
  },
  featuresContainer: {
    width: '100%',
    maxWidth: 400,
    paddingHorizontal: SPACING.md,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SPACING.lg,
    paddingHorizontal: SPACING.sm,
  },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.md,
  },
  featureContent: {
    flex: 1,
    paddingTop: 2,
  },
  featureTitle: {
    fontWeight: '600',
    marginBottom: SPACING.xs,
  },
  featureDescription: {
    lineHeight: 18,
  },
  buttonContainer: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
    paddingBottom: SPACING.xl,
  },
  primaryButton: {
    marginBottom: SPACING.md,
  },
  skipButton: {
    alignSelf: 'center',
  },
});