import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { AuthStackParamList } from '../../types';
import { 
  Typography, 
  Button, 
  Container,
  Card,
  Input 
} from '../../components/ui';
import { ScreenWrapper, Header } from '../../components/layout';
import { useTheme } from '../../components/theme';
import { useAuthStore, useNavigationStore } from '../../stores';
import { SPACING, STORAGE_KEYS } from '../../constants';
import { AccessibilityUtils, StorageService } from '../../utils';
import { Ionicons } from '@expo/vector-icons';

type AuthScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'AuthChoice'>;
type AuthScreenRouteProp = RouteProp<AuthStackParamList, 'AuthChoice'>;

interface Props {
  navigation: AuthScreenNavigationProp;
  route: AuthScreenRouteProp;
}

type AuthMode = 'choice' | 'email' | 'phone' | 'guest';

export default function AuthScreen({ navigation }: Props) {
  const { colors } = useTheme();
  const { login, register, isLoading, error, clearError } = useAuthStore();
  const { setHasCompletedOnboarding } = useNavigationStore();
  
  const [authMode, setAuthMode] = useState<AuthMode>('choice');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [emailError, setEmailError] = useState('');
  const [phoneError, setPhoneError] = useState('');

  // Clear errors when auth mode changes
  React.useEffect(() => {
    clearError();
    setEmailError('');
    setPhoneError('');
  }, [authMode, clearError]);

  const handleCompleteOnboarding = async () => {
    try {
      await StorageService.setItem(STORAGE_KEYS.onboardingCompleted, 'true');
      setHasCompletedOnboarding(true);
      // Navigation will automatically switch to main app due to navigation logic
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
    }
  };

  const handleEmailAuth = async () => {
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    try {
      clearError();
      await login(email);
      await handleCompleteOnboarding();
    } catch (error) {
      console.error('Email authentication failed:', error);
      // Error is handled by the store, but we can show additional feedback
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage) {
        Alert.alert(
          'Sign In Error',
          errorMessage || 'There was an issue signing in. Please check your email and try again.',
          [{ text: 'OK' }]
        );
      }
    }
  };

  const handlePhoneAuth = async () => {
    if (!validatePhone(phone)) {
      setPhoneError('Please enter a valid phone number');
      return;
    }

    try {
      clearError();
      await login(undefined, phone);
      await handleCompleteOnboarding();
    } catch (error) {
      console.error('Phone authentication failed:', error);
      // Error is handled by the store, but we can show additional feedback
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage) {
        Alert.alert(
          'Sign In Error',
          errorMessage || 'There was an issue signing in. Please check your phone number and try again.',
          [{ text: 'OK' }]
        );
      }
    }
  };

  const handleGuestMode = async () => {
    try {
      clearError();
      console.log('Starting guest registration...');
      await register(); // Register as guest
      await handleCompleteOnboarding();
    } catch (error) {
      console.error('Guest registration failed:', error);
      // Error is handled by the store, but we can show additional feedback
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      Alert.alert(
        'Setup Error',
        `There was an issue setting up guest mode: ${errorMessage}. Please try again.`,
        [{ text: 'OK' }]
      );
    }
  };

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePhone = (phone: string): boolean => {
    const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone);
  };

  const renderAuthChoice = () => (
    <Container style={styles.content}>
      {/* Icon */}
      <View style={[styles.iconContainer, { backgroundColor: colors.primaryLight }]}>
        <Ionicons
          name="person-add"
          size={64}
          color={colors.primary}
          accessibilityLabel="Get started icon"
          accessibilityRole="image"
        />
      </View>

      {/* Title */}
      <Typography
        variant="h2"
        style={[styles.title, { color: colors.text }]}
        align="center"
      >
        Almost There!
      </Typography>

      {/* Description */}
      <Typography
        variant="body"
        style={[styles.description, { color: colors.textSecondary }]}
        align="center"
      >
        Choose how you'd like to use Flai. You can always change this later in Settings.
      </Typography>

      {/* Auth Options */}
      <View style={styles.optionsContainer}>
        <Card 
          variant="outlined" 
          style={styles.optionCard}
          onPress={() => setAuthMode('email')}
        >
          <View style={styles.optionContent}>
            <Ionicons
              name="mail"
              size={24}
              color={colors.primary}
              accessibilityLabel="Email sign-in"
              accessibilityRole="image"
            />
            <View style={styles.optionText}>
              <Typography
                variant="label"
                style={[styles.optionTitle, { color: colors.text }]}
              >
                Sign in with Email
              </Typography>
              <Typography
                variant="caption"
                style={[styles.optionDescription, { color: colors.textSecondary }]}
              >
                Save your preferences and booking history
              </Typography>
            </View>
            <Ionicons
              name="chevron-forward"
              size={20}
              color={colors.textSecondary}
              accessibilityLabel="Navigate to email sign-in"
              accessibilityRole="image"
            />
          </View>
        </Card>

        <Card 
          variant="outlined" 
          style={styles.optionCard}
          onPress={() => setAuthMode('phone')}
        >
          <View style={styles.optionContent}>
            <Ionicons
              name="call"
              size={24}
              color={colors.primary}
              accessibilityLabel="Phone sign-in"
              accessibilityRole="image"
            />
            <View style={styles.optionText}>
              <Typography
                variant="label"
                style={[styles.optionTitle, { color: colors.text }]}
              >
                Sign in with Phone
              </Typography>
              <Typography
                variant="caption"
                style={[styles.optionDescription, { color: colors.textSecondary }]}
              >
                Quick SMS verification and easy booking updates
              </Typography>
            </View>
            <Ionicons
              name="chevron-forward"
              size={20}
              color={colors.textSecondary}
              accessibilityLabel="Navigate to phone sign-in"
              accessibilityRole="image"
            />
          </View>
        </Card>

        <Card 
          variant="outlined" 
          style={styles.optionCard}
          onPress={() => setAuthMode('guest')}
        >
          <View style={styles.optionContent}>
            <Ionicons
              name="person"
              size={24}
              color={colors.primary}
              accessibilityLabel="Guest mode"
              accessibilityRole="image"
            />
            <View style={styles.optionText}>
              <Typography
                variant="label"
                style={[styles.optionTitle, { color: colors.text }]}
              >
                Continue as Guest
              </Typography>
              <Typography
                variant="caption"
                style={[styles.optionDescription, { color: colors.textSecondary }]}
              >
                Start booking immediately, no account required
              </Typography>
            </View>
            <Ionicons
              name="chevron-forward"
              size={20}
              color={colors.textSecondary}
              accessibilityLabel="Navigate to guest mode"
              accessibilityRole="image"
            />
          </View>
        </Card>
      </View>
    </Container>
  );

  const renderEmailAuth = () => (
    <Container style={styles.content}>
      <Typography
        variant="h3"
        style={[styles.formTitle, { color: colors.text }]}
        align="center"
      >
        Sign in with Email
      </Typography>

      <Typography
        variant="body"
        style={[styles.formDescription, { color: colors.textSecondary }]}
        align="center"
      >
        Enter your email address to create an account or sign in.
      </Typography>

      <View style={styles.formContainer}>
        <Input
          value={email}
          onChangeText={(text) => {
            setEmail(text);
            setEmailError('');
          }}
          placeholder="Enter your email address"
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          error={emailError}
          leftIcon="mail"
          style={styles.input}
          accessibilityLabel="Email address input"
        />

        <Button
          title="Continue"
          onPress={handleEmailAuth}
          variant="primary"
          size="large"
          loading={isLoading}
          disabled={!email.trim()}
          style={styles.authButton}
          accessibilityLabel="Sign in with email"
        />

        <Button
          title="Back"
          onPress={() => setAuthMode('choice')}
          variant="text"
          size="medium"
          style={styles.backButton}
          accessibilityLabel="Go back to sign-in options"
        />
      </View>
    </Container>
  );

  const renderPhoneAuth = () => (
    <Container style={styles.content}>
      <Typography
        variant="h3"
        style={[styles.formTitle, { color: colors.text }]}
        align="center"
      >
        Sign in with Phone
      </Typography>

      <Typography
        variant="body"
        style={[styles.formDescription, { color: colors.textSecondary }]}
        align="center"
      >
        Enter your phone number to create an account or sign in.
      </Typography>

      <View style={styles.formContainer}>
        <Input
          value={phone}
          onChangeText={(text) => {
            setPhone(text);
            setPhoneError('');
          }}
          placeholder="Enter your phone number"
          keyboardType="phone-pad"
          autoCapitalize="none"
          autoCorrect={false}
          error={phoneError}
          leftIcon="call"
          style={styles.input}
          accessibilityLabel="Phone number input"
        />

        <Button
          title="Continue"
          onPress={handlePhoneAuth}
          variant="primary"
          size="large"
          loading={isLoading}
          disabled={!phone.trim()}
          style={styles.authButton}
          accessibilityLabel="Sign in with phone number"
        />

        <Button
          title="Back"
          onPress={() => setAuthMode('choice')}
          variant="text"
          size="medium"
          style={styles.backButton}
          accessibilityLabel="Go back to sign-in options"
        />
      </View>
    </Container>
  );

  const renderGuestMode = () => (
    <Container style={styles.content}>
      <Typography
        variant="h3"
        style={[styles.formTitle, { color: colors.text }]}
        align="center"
      >
        Continue as Guest
      </Typography>

      <Typography
        variant="body"
        style={[styles.formDescription, { color: colors.textSecondary }]}
        align="center"
      >
        You can start booking flights immediately. You can always create an account later to save your preferences.
      </Typography>

      <View style={styles.formContainer}>
        <View style={styles.guestInfoContainer}>
          <Typography
            variant="caption"
            style={[styles.guestInfo, { color: colors.textSecondary }]}
          >
            • Book flights instantly
          </Typography>
          <Typography
            variant="caption"
            style={[styles.guestInfo, { color: colors.textSecondary }]}
          >
            • No personal information required
          </Typography>
          <Typography
            variant="caption"
            style={[styles.guestInfo, { color: colors.textSecondary }]}
          >
            • Upgrade to full account anytime
          </Typography>
        </View>

        <Button
          title="Start Booking"
          onPress={handleGuestMode}
          variant="primary"
          size="large"
          loading={isLoading}
          style={styles.authButton}
          accessibilityLabel="Continue as guest user"
        />

        <Button
          title="Back"
          onPress={() => setAuthMode('choice')}
          variant="text"
          size="medium"
          style={styles.backButton}
          accessibilityLabel="Go back to sign-in options"
        />
      </View>
    </Container>
  );

  const renderContent = () => {
    switch (authMode) {
      case 'email':
        return renderEmailAuth();
      case 'phone':
        return renderPhoneAuth();
      case 'guest':
        return renderGuestMode();
      default:
        return renderAuthChoice();
    }
  };

  const renderError = () => {
    if (!error) return null;
    
    return (
      <View style={[styles.errorContainer, { backgroundColor: colors.error + '20', borderColor: colors.error }]}>
        <Ionicons
          name="alert-circle"
          size={20}
          color={colors.error}
          style={styles.errorIcon}
        />
        <Typography
          variant="caption"
          style={[styles.errorText, { color: colors.error }]}
        >
          {error}
        </Typography>
      </View>
    );
  };

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <Header
          title="Get Started"
          showBackButton={authMode !== 'choice'}
          onBackPress={() => {
            if (authMode === 'choice') {
              navigation.goBack();
            } else {
              setAuthMode('choice');
            }
          }}
        />
        
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          accessibilityLabel="Authentication options"
        >
          {renderError()}
          {renderContent()}
        </ScrollView>
      </SafeAreaView>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: SPACING.xl,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: SPACING.lg,
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
    marginBottom: SPACING.xl,
    paddingHorizontal: SPACING.md,
    lineHeight: 22,
  },
  optionsContainer: {
    width: '100%',
    maxWidth: 400,
  },
  optionCard: {
    marginBottom: SPACING.md,
    padding: SPACING.lg,
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionText: {
    flex: 1,
    marginLeft: SPACING.md,
  },
  optionTitle: {
    fontWeight: '600',
    marginBottom: SPACING.xs,
  },
  optionDescription: {
    lineHeight: 16,
  },
  formTitle: {
    marginBottom: SPACING.sm,
  },
  formDescription: {
    marginBottom: SPACING.xl,
    paddingHorizontal: SPACING.md,
    lineHeight: 22,
  },
  formContainer: {
    width: '100%',
    maxWidth: 400,
  },
  input: {
    marginBottom: SPACING.lg,
  },
  authButton: {
    marginBottom: SPACING.md,
  },
  backButton: {
    alignSelf: 'center',
  },
  guestInfoContainer: {
    marginBottom: SPACING.xl,
    paddingHorizontal: SPACING.md,
  },
  guestInfo: {
    marginBottom: SPACING.sm,
    lineHeight: 18,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: SPACING.md,
    padding: SPACING.md,
    borderRadius: 8,
    borderWidth: 1,
  },
  errorIcon: {
    marginRight: SPACING.sm,
  },
  errorText: {
    flex: 1,
    lineHeight: 18,
  },
});