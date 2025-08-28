import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { AuthStackParamList } from '../../types';
import { 
  Typography, 
  Button,
  Card
} from '../../components/ui';
import { ScreenWrapper, Header, Container } from '../../components/layout';
import { useTheme } from '../../components/theme';
import { SPACING } from '../../constants';
import { AccessibilityUtils } from '../../utils';
import { Ionicons } from '@expo/vector-icons';

type TermsScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'Terms'>;
type TermsScreenRouteProp = RouteProp<AuthStackParamList, 'Terms'>;

interface Props {
  navigation: TermsScreenNavigationProp;
  route: TermsScreenRouteProp;
}

export default function TermsScreen({ navigation }: Props) {
  const { colors } = useTheme();
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);

  const canContinue = termsAccepted && privacyAccepted;

  const handleContinue = () => {
    if (canContinue) {
      navigation.navigate('AuthChoice');
    }
  };

  const handleAcceptAll = () => {
    setTermsAccepted(true);
    setPrivacyAccepted(true);
  };

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <Header
          title="Terms & Privacy"
          showBackButton
          onBackPress={() => navigation.goBack()}
        />
        
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          accessibilityLabel="Terms and privacy content"
        >
          <Container style={styles.content}>
            {/* Introduction */}
            <Typography
              variant="h2"
              style={[styles.title, { color: colors.text }]}
            >
              Legal Agreements
            </Typography>

            <Typography
              variant="body"
              style={[styles.description, { color: colors.textSecondary }]}
            >
              Please review and accept our terms of service and privacy policy to continue using Flai.
            </Typography>

            {/* Terms of Service */}
            <Card variant="outlined" style={styles.documentCard}>
              <View style={styles.documentHeader}>
                <Ionicons
                  name="document-text"
                  size={24}
                  color={colors.primary}
                  accessibilityLabel="Terms of service document"
                />
                <Typography
                  variant="label"
                  style={[styles.documentTitle, { color: colors.text }]}
                >
                  Terms of Service
                </Typography>
              </View>
              
              <Typography
                variant="caption"
                style={[styles.documentSummary, { color: colors.textSecondary }]}
                numberOfLines={3}
              >
                Our terms outline your rights and responsibilities when using Flai, 
                including booking flights, payment processing, and account management.
              </Typography>

              <Button
                title={termsAccepted ? "✓ Accepted" : "Review & Accept"}
                onPress={() => setTermsAccepted(true)}
                variant={termsAccepted ? "outline" : "primary"}
                size="medium"
                style={styles.acceptButton}
                accessibilityLabel={`${termsAccepted ? 'Already accepted' : 'Review and accept'} terms of service`}
              />
            </Card>

            {/* Privacy Policy */}
            <Card variant="outlined" style={styles.documentCard}>
              <View style={styles.documentHeader}>
                <Ionicons
                  name="shield-checkmark"
                  size={24}
                  color={colors.primary}
                  accessibilityLabel="Privacy policy document"
                />
                <Typography
                  variant="label"
                  style={[styles.documentTitle, { color: colors.text }]}
                >
                  Privacy Policy
                </Typography>
              </View>
              
              <Typography
                variant="caption"
                style={[styles.documentSummary, { color: colors.textSecondary }]}
                numberOfLines={3}
              >
                We protect your data with enterprise-grade security and never share 
                personal information without your explicit consent.
              </Typography>

              <Button
                title={privacyAccepted ? "✓ Accepted" : "Review & Accept"}
                onPress={() => setPrivacyAccepted(true)}
                variant={privacyAccepted ? "outline" : "primary"}
                size="medium"
                style={styles.acceptButton}
                accessibilityLabel={`${privacyAccepted ? 'Already accepted' : 'Review and accept'} privacy policy`}
              />
            </Card>

            {/* Quick Accept */}
            {!canContinue && (
              <View style={styles.quickAcceptContainer}>
                <Typography
                  variant="caption"
                  style={[styles.quickAcceptText, { color: colors.textSecondary }]}
                  align="center"
                >
                  Or accept both at once:
                </Typography>
                
                <Button
                  title="Accept All"
                  onPress={handleAcceptAll}
                  variant="text"
                  size="medium"
                  style={styles.acceptAllButton}
                  accessibilityLabel="Accept both terms of service and privacy policy"
                />
              </View>
            )}
          </Container>
        </ScrollView>

        {/* Continue Button */}
        <View style={[styles.buttonContainer, { backgroundColor: colors.background }]}>
          <Button
            title="Continue"
            onPress={handleContinue}
            variant="primary"
            size="large"
            disabled={!canContinue}
            style={styles.continueButton}
            accessibilityLabel={canContinue ? "Continue to notification permissions" : "Accept terms and privacy policy to continue"}
          />
          
          {!canContinue && (
            <Typography
              variant="caption"
              style={[styles.continueHint, { color: colors.textSecondary }]}
              align="center"
            >
              Please accept both agreements to continue
            </Typography>
          )}
        </View>
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
    paddingVertical: SPACING.lg,
  },
  title: {
    marginBottom: SPACING.sm,
  },
  description: {
    marginBottom: SPACING.xl,
    lineHeight: 22,
  },
  documentCard: {
    marginBottom: SPACING.lg,
    padding: SPACING.lg,
  },
  documentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  documentTitle: {
    marginLeft: SPACING.sm,
    fontWeight: '600',
  },
  documentSummary: {
    marginBottom: SPACING.md,
    lineHeight: 18,
  },
  acceptButton: {
    alignSelf: 'flex-start',
  },
  quickAcceptContainer: {
    alignItems: 'center',
    marginTop: SPACING.md,
  },
  quickAcceptText: {
    marginBottom: SPACING.sm,
  },
  acceptAllButton: {
    alignSelf: 'center',
  },
  buttonContainer: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  continueButton: {
    marginBottom: SPACING.sm,
  },
  continueHint: {
    marginTop: SPACING.xs,
  },
});