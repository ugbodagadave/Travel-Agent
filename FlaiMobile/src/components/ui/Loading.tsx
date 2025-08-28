import React from 'react';
import { View, ActivityIndicator, StyleSheet, Modal, Dimensions } from 'react-native';
import { LoadingProps } from '../../types';
import { useTheme } from '../theme/ThemeContext';
import { SPACING } from '../../constants';
import Typography from './Typography';

const { width: screenWidth } = Dimensions.get('window');

// Basic Loading Spinner
export const LoadingSpinner: React.FC<LoadingProps> = ({
  size = 'medium',
  color,
  style,
}) => {
  const { colors } = useTheme();

  const getSizeValue = () => {
    switch (size) {
      case 'small':
        return 'small' as const;
      case 'medium':
        return 'large' as const;
      case 'large':
        return 'large' as const;
      default:
        return 'large' as const;
    }
  };

  return (
    <ActivityIndicator
      size={getSizeValue()}
      color={color || colors.primary}
      style={style}
      accessibilityLabel="Loading"
    />
  );
};

// Full Screen Loading Overlay
interface LoadingOverlayProps {
  visible: boolean;
  message?: string;
  transparent?: boolean;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  visible,
  message = 'Loading...',
  transparent = true,
}) => {
  const { colors } = useTheme();

  return (
    <Modal
      visible={visible}
      transparent={transparent}
      animationType="fade"
      statusBarTranslucent
    >
      <View style={[styles.overlay, { backgroundColor: 'rgba(0, 0, 0, 0.5)' }]}>
        <View style={[styles.loadingContainer, { backgroundColor: colors.card }]}>
          <LoadingSpinner size="large" />
          {message ? (
            <Typography style={styles.loadingMessage}>
              {message}
            </Typography>
          ) : null}
        </View>
      </View>
    </Modal>
  );
};

// Skeleton Loading for lists and cards
interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: any;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 20,
  borderRadius = 4,
  style,
}) => {
  const { colors } = useTheme();

  return (
    <View
      style={[
        {
          width,
          height,
          backgroundColor: colors.divider,
          borderRadius,
        },
        style,
      ]}
      accessibilityLabel="Loading content"
    />
  );
};

// Skeleton for Chat Message
export const MessageSkeleton: React.FC = () => {
  const { colors } = useTheme();

  return (
    <View style={styles.messageSkeleton}>
      <View style={[styles.skeletonAvatar, { backgroundColor: colors.divider }]} />
      <View style={styles.skeletonContent}>
        <Skeleton width="60%" height={16} style={{ marginBottom: SPACING.xs }} />
        <Skeleton width="80%" height={14} />
      </View>
    </View>
  );
};

// Skeleton for Flight Card
export const FlightCardSkeleton: React.FC = () => {
  return (
    <View style={styles.flightCardSkeleton}>
      <View style={styles.skeletonHeader}>
        <Skeleton width={40} height={40} borderRadius={8} />
        <View style={styles.skeletonFlightInfo}>
          <Skeleton width="70%" height={18} style={{ marginBottom: SPACING.xs }} />
          <Skeleton width="50%" height={14} />
        </View>
        <Skeleton width={60} height={24} borderRadius={12} />
      </View>
      
      <View style={styles.skeletonFlightDetails}>
        <Skeleton width="30%" height={16} />
        <Skeleton width={40} height={2} style={{ marginTop: SPACING.sm }} />
        <Skeleton width="30%" height={16} />
      </View>
      
      <View style={styles.skeletonFooter}>
        <Skeleton width="40%" height={14} />
        <Skeleton width={80} height={32} borderRadius={16} />
      </View>
    </View>
  );
};

// Loading State for Search
interface SearchLoadingProps {
  message?: string;
}

export const SearchLoading: React.FC<SearchLoadingProps> = ({
  message = 'Searching for flights...',
}) => {
  const { colors } = useTheme();

  return (
    <View style={styles.searchLoading}>
      <LoadingSpinner size="large" />
      <Typography style={[styles.searchMessage, { color: colors.textSecondary }]}>
        {message}
      </Typography>
    </View>
  );
};

// List Loading State
interface ListLoadingProps {
  itemCount?: number;
  renderSkeleton?: () => React.ReactNode;
}

export const ListLoading: React.FC<ListLoadingProps> = ({
  itemCount = 5,
  renderSkeleton = () => <MessageSkeleton />,
}) => {
  return (
    <View>
      {Array.from({ length: itemCount }).map((_, index) => (
        <View key={index} style={{ marginBottom: SPACING.md }}>
          {renderSkeleton()}
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContainer: {
    padding: SPACING.xl,
    borderRadius: 16,
    alignItems: 'center',
    minWidth: 120,
  },
  loadingMessage: {
    marginTop: SPACING.md,
    textAlign: 'center',
  },
  messageSkeleton: {
    flexDirection: 'row',
    padding: SPACING.md,
    alignItems: 'flex-start',
  },
  skeletonAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: SPACING.sm,
  },
  skeletonContent: {
    flex: 1,
  },
  flightCardSkeleton: {
    padding: SPACING.md,
    backgroundColor: 'transparent',
  },
  skeletonHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  skeletonFlightInfo: {
    flex: 1,
    marginLeft: SPACING.sm,
  },
  skeletonFlightDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  skeletonFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  searchLoading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SPACING.xl,
  },
  searchMessage: {
    marginTop: SPACING.md,
    textAlign: 'center',
  },
});

export default LoadingSpinner;