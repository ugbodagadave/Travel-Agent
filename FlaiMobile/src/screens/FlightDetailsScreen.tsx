import React from 'react';
import { View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../types';
import { Typography, Container, Button } from '../components/ui';
import { ScreenWrapper, Header } from '../components/layout';
import { useTheme } from '../components/theme';
import { SPACING } from '../constants';
import { AccessibilityUtils } from '../utils';
import { Ionicons } from '@expo/vector-icons';

type FlightDetailsScreenNavigationProp = StackNavigationProp<RootStackParamList, 'FlightDetails'>;
type FlightDetailsScreenRouteProp = RouteProp<RootStackParamList, 'FlightDetails'>;

interface Props {
  navigation: FlightDetailsScreenNavigationProp;
  route: FlightDetailsScreenRouteProp;
}

export default function FlightDetailsScreen({ navigation, route }: Props) {
  const { colors } = useTheme();
  const { flightId } = route.params;

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <Header
          title="Flight Details"
          showBackButton
          onBackPress={() => navigation.goBack()}
        />
        
        <Container style={styles.content}>
          <View style={styles.placeholderContainer}>
            <View style={[styles.iconContainer, { backgroundColor: colors.primaryLight }]}>
              <Ionicons
                name="airplane"
                size={64}
                color={colors.primary}
                accessibilityLabel="Flight details"
                accessibilityRole="image"
              />
            </View>
            
            <Typography
              variant="h3"
              style={[styles.title, { color: colors.text }]}
              align="center"
            >
              Flight Details
            </Typography>
            
            <Typography
              variant="body"
              style={[styles.description, { color: colors.textSecondary }]}
              align="center"
            >
              Detailed flight information will be displayed here for flight ID: {flightId}
            </Typography>

            <Button
              title="Back to Results"
              onPress={() => navigation.goBack()}
              variant="primary"
              size="medium"
              style={styles.backButton}
              accessibilityLabel="Return to flight results"
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
    marginBottom: SPACING.xl,
  },
  backButton: {
    marginTop: SPACING.md,
  },
});