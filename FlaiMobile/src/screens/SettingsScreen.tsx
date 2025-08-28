import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert, Share } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { 
  Typography, 
  Button, 
  Container,
  Card 
} from '../components/ui';
import { ScreenWrapper, Header } from '../components/layout';
import { useTheme } from '../components/theme';
import { useAuthStore, useChatStore, useNavigationStore } from '../stores';
import { SPACING, APP_INFO } from '../constants';
import { AccessibilityUtils, StorageService } from '../utils';
import { Ionicons } from '@expo/vector-icons';

export default function SettingsScreen() {
  const { colors, theme, toggleTheme } = useTheme();
  const { user, logout, isAuthenticated } = useAuthStore();
  const { clearChat } = useChatStore();
  const { setHasCompletedOnboarding } = useNavigationStore();
  
  const [isLoading, setIsLoading] = useState(false);

  const handleThemeToggle = () => {
    toggleTheme();
  };

  const handleClearChat = () => {
    Alert.alert(
      'Clear Chat History',
      'This will delete all your chat messages. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clear', 
          style: 'destructive',
          onPress: () => {
            clearChat();
            Alert.alert('Success', 'Chat history has been cleared.');
          }
        },
      ]
    );
  };

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out? Your chat history will be saved.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Sign Out', 
          style: 'destructive',
          onPress: async () => {
            setIsLoading(true);
            try {
              await logout();
            } catch (error) {
              Alert.alert('Error', 'Failed to sign out. Please try again.');
            } finally {
              setIsLoading(false);
            }
          }
        },
      ]
    );
  };

  const handleResetOnboarding = () => {
    Alert.alert(
      'Reset Onboarding',
      'This will show the welcome screens again next time you open the app.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Reset', 
          onPress: async () => {
            try {
              await StorageService.removeItem('onboardingCompleted');
              setHasCompletedOnboarding(false);
              Alert.alert('Success', 'Onboarding has been reset.');
            } catch (error) {
              Alert.alert('Error', 'Failed to reset onboarding.');
            }
          }
        },
      ]
    );
  };

  const handleShareApp = async () => {
    try {
      await Share.share({
        message: `Check out ${APP_INFO.name} - ${APP_INFO.description}! Book flights with AI assistance and flexible payment options.`,
        title: APP_INFO.name,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const handleContactSupport = () => {
    Alert.alert(
      'Contact Support',
      'Need help? You can reach our support team through the chat or send us an email.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Chat Support', onPress: () => {
          // Navigate to chat with support intent
          Alert.alert('Info', 'Just type "I need help" in the chat to reach our support team.');
        }},
      ]
    );
  };

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <Header title="Settings" />
        
        <ScrollView 
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          accessibilityLabel="Settings options"
        >
          <Container style={styles.content}>
            {/* User Profile Section */}
            {isAuthenticated && (
              <View style={styles.section}>
                <Typography
                  variant="label"
                  style={[styles.sectionTitle, { color: colors.text }]}
                >
                  Account
                </Typography>
                
                <Card variant="outlined" style={styles.profileCard}>
                  <View style={styles.profileInfo}>
                    <View style={[styles.profileAvatar, { backgroundColor: colors.primaryLight }]}>
                      <Ionicons
                        name="person"
                        size={24}
                        color={colors.primary}
                        accessibilityLabel="User profile"
                        accessibilityRole="image"
                      />
                    </View>
                    
                    <View style={styles.profileDetails}>
                      <Typography
                        variant="label"
                        style={[styles.profileName, { color: colors.text }]}
                      >
                        {user?.email || user?.phone || 'Guest User'}
                      </Typography>
                      
                      <Typography
                        variant="caption"
                        style={[styles.profileType, { color: colors.textSecondary }]}
                      >
                        {user?.email ? 'Email Account' : user?.phone ? 'Phone Account' : 'Guest Account'}
                      </Typography>
                    </View>
                  </View>
                </Card>
              </View>
            )}

            {/* Appearance Section */}
            <View style={styles.section}>
              <Typography
                variant="label"
                style={[styles.sectionTitle, { color: colors.text }]}
              >
                Appearance
              </Typography>
              
              <SettingItem
                icon="contrast"
                title="Dark Mode"
                description={`Currently using ${theme} theme`}
                rightElement={
                  <Button
                    title={theme === 'dark' ? 'On' : 'Off'}
                    onPress={handleThemeToggle}
                    variant={theme === 'dark' ? 'primary' : 'outline'}
                    size="small"
                    accessibilityLabel={`Toggle dark mode, currently ${theme === 'dark' ? 'enabled' : 'disabled'}`}
                  />
                }
                onPress={handleThemeToggle}
                colors={colors}
              />
            </View>

            {/* Data Section */}
            <View style={styles.section}>
              <Typography
                variant="label"
                style={[styles.sectionTitle, { color: colors.text }]}
              >
                Data & Privacy
              </Typography>
              
              <SettingItem
                icon="trash"
                title="Clear Chat History"
                description="Delete all chat messages"
                onPress={handleClearChat}
                colors={colors}
              />
            </View>

            {/* Support Section */}
            <View style={styles.section}>
              <Typography
                variant="label"
                style={[styles.sectionTitle, { color: colors.text }]}
              >
                Support
              </Typography>
              
              <SettingItem
                icon="help-circle"
                title="Contact Support"
                description="Get help with your account or bookings"
                onPress={handleContactSupport}
                colors={colors}
              />
              
              <SettingItem
                icon="share"
                title="Share App"
                description="Tell friends about Flai"
                onPress={handleShareApp}
                colors={colors}
              />
            </View>

            {/* Advanced Section */}
            <View style={styles.section}>
              <Typography
                variant="label"
                style={[styles.sectionTitle, { color: colors.text }]}
              >
                Advanced
              </Typography>
              
              <SettingItem
                icon="refresh"
                title="Reset Onboarding"
                description="Show welcome screens again"
                onPress={handleResetOnboarding}
                colors={colors}
              />
            </View>

            {/* App Information */}
            <View style={styles.section}>
              <Typography
                variant="label"
                style={[styles.sectionTitle, { color: colors.text }]}
              >
                About
              </Typography>
              
              <Card variant="flat" style={[styles.infoCard, { backgroundColor: colors.surface }]}>
                <Typography
                  variant="body"
                  style={[styles.appName, { color: colors.text }]}
                >
                  {APP_INFO.name}
                </Typography>
                
                <Typography
                  variant="caption"
                  style={[styles.appVersion, { color: colors.textSecondary }]}
                >
                  Version {APP_INFO.version}
                </Typography>
                
                <Typography
                  variant="caption"
                  style={[styles.appDescription, { color: colors.textSecondary }]}
                  numberOfLines={2}
                >
                  {APP_INFO.description}
                </Typography>
              </Card>
            </View>

            {/* Sign Out */}
            {isAuthenticated && (
              <View style={styles.signOutSection}>
                <Button
                  title="Sign Out"
                  onPress={handleLogout}
                  variant="outline"
                  size="large"
                  loading={isLoading}
                  style={[styles.signOutButton, { borderColor: colors.error }]}
                  accessibilityLabel="Sign out of your account"
                />
              </View>
            )}
          </Container>
        </ScrollView>
      </SafeAreaView>
    </ScreenWrapper>
  );
}

interface SettingItemProps {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  description: string;
  onPress?: () => void;
  rightElement?: React.ReactNode;
  colors: any;
}

function SettingItem({ icon, title, description, onPress, rightElement, colors }: SettingItemProps) {
  return (
    <Card 
      variant="flat" 
      style={[styles.settingCard, { backgroundColor: colors.surface }]}
      onPress={onPress}
    >
      <View style={styles.settingContent}>
        <View style={styles.settingLeft}>
          <View style={[styles.settingIcon, { backgroundColor: colors.background }]}>
            <Ionicons
              name={icon}
              size={20}
              color={colors.primary}
              accessibilityLabel={`${title} icon`}
              accessibilityRole="image"
            />
          </View>
          
          <View style={styles.settingText}>
            <Typography
              variant="body"
              style={[styles.settingTitle, { color: colors.text }]}
            >
              {title}
            </Typography>
            
            <Typography
              variant="caption"
              style={[styles.settingDescription, { color: colors.textSecondary }]}
              numberOfLines={2}
            >
              {description}
            </Typography>
          </View>
        </View>
        
        {rightElement || (
          <Ionicons
            name="chevron-forward"
            size={20}
            color={colors.textSecondary}
            accessibilityLabel="Navigate to setting"
            accessibilityRole="image"
          />
        )}
      </View>
    </Card>
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
  section: {
    marginBottom: SPACING.xl,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: SPACING.md,
    paddingHorizontal: SPACING.sm,
  },
  profileCard: {
    padding: SPACING.lg,
  },
  profileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.md,
  },
  profileDetails: {
    flex: 1,
  },
  profileName: {
    fontWeight: '600',
    marginBottom: SPACING.xs,
  },
  profileType: {
    lineHeight: 16,
  },
  settingCard: {
    marginBottom: SPACING.sm,
    padding: SPACING.lg,
  },
  settingContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SPACING.md,
  },
  settingText: {
    flex: 1,
  },
  settingTitle: {
    fontWeight: '500',
    marginBottom: SPACING.xs,
  },
  settingDescription: {
    lineHeight: 16,
  },
  infoCard: {
    padding: SPACING.lg,
    alignItems: 'center',
  },
  appName: {
    fontWeight: '600',
    marginBottom: SPACING.xs,
  },
  appVersion: {
    marginBottom: SPACING.sm,
  },
  appDescription: {
    textAlign: 'center',
    lineHeight: 16,
  },
  signOutSection: {
    marginTop: SPACING.lg,
    paddingTop: SPACING.lg,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  signOutButton: {
    marginTop: SPACING.md,
  },
});