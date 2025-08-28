import React, { useState } from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import {
  ScreenWrapper,
  Header,
  Container,
  Button,
  Input,
  Card,
  Typography,
  Heading1,
  Heading2,
  Heading3,
  Body,
  Caption,
  Label,
  LoadingSpinner,
  Toast,
  useTheme,
} from '../components';
import { SPACING } from '../constants';

export const DesignSystemDemo: React.FC = () => {
  const { theme, toggleTheme, colors } = useTheme();
  const [inputValue, setInputValue] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleButtonPress = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setShowToast(true);
    }, 2000);
  };

  const handleToastHide = () => {
    setShowToast(false);
  };

  return (
    <ScreenWrapper>
      <Header
        title="Design System Demo"
        rightComponent={
          <Button
            title={theme === 'light' ? '🌙' : '☀️'}
            onPress={toggleTheme}
            variant="text"
            size="small"
          />
        }
      />
      
      <Container scrollable>
        {/* Typography Section */}
        <Card style={styles.section}>
          <Heading2>Typography</Heading2>
          <Heading1>Heading 1</Heading1>
          <Heading2>Heading 2</Heading2>
          <Heading3>Heading 3</Heading3>
          <Body>This is body text with proper line height and spacing.</Body>
          <Caption>This is caption text for additional information.</Caption>
          <Label>Label Text</Label>
        </Card>

        {/* Buttons Section */}
        <Card style={styles.section}>
          <Heading3>Buttons</Heading3>
          <View style={styles.buttonRow}>
            <Button title="Primary" onPress={handleButtonPress} variant="primary" />
            <Button title="Secondary" onPress={handleButtonPress} variant="secondary" />
          </View>
          <View style={styles.buttonRow}>
            <Button title="Outline" onPress={handleButtonPress} variant="outline" />
            <Button title="Text" onPress={handleButtonPress} variant="text" />
          </View>
          <View style={styles.buttonRow}>
            <Button title="Disabled" onPress={() => {}} variant="primary" disabled />
            <Button title="Loading" onPress={() => {}} variant="primary" loading={loading} />
          </View>
          
          {/* Different sizes */}
          <View style={styles.buttonRow}>
            <Button title="Small" onPress={handleButtonPress} variant="primary" size="small" />
            <Button title="Medium" onPress={handleButtonPress} variant="primary" size="medium" />
            <Button title="Large" onPress={handleButtonPress} variant="primary" size="large" />
          </View>
        </Card>

        {/* Inputs Section */}
        <Card style={styles.section}>
          <Heading3>Text Inputs</Heading3>
          <Input
            value={inputValue}
            onChangeText={setInputValue}
            placeholder="Enter your text here"
          />
          <Input
            value=""
            onChangeText={() => {}}
            placeholder="Email address"
            keyboardType="email-address"
            leftIcon="@"
          />
          <Input
            value=""
            onChangeText={() => {}}
            placeholder="Password"
            secureTextEntry
            rightIcon="👁"
            onRightIconPress={() => {}}
          />
          <Input
            value=""
            onChangeText={() => {}}
            placeholder="Input with error"
            error="This field is required"
          />
          <Input
            value=""
            onChangeText={() => {}}
            placeholder="Disabled input"
            disabled
          />
        </Card>

        {/* Cards Section */}
        <Card style={styles.section}>
          <Heading3>Cards</Heading3>
          
          <Card variant="elevated" style={styles.demoCard}>
            <Body>Elevated Card</Body>
            <Caption>This card has shadow/elevation</Caption>
          </Card>
          
          <Card variant="outlined" style={styles.demoCard}>
            <Body>Outlined Card</Body>
            <Caption>This card has a border</Caption>
          </Card>
          
          <Card variant="flat" style={styles.demoCard}>
            <Body>Flat Card</Body>
            <Caption>This card has no elevation</Caption>
          </Card>
          
          <Card
            variant="elevated"
            onPress={() => console.log('Card pressed')}
            style={styles.demoCard}
          >
            <Body>Pressable Card</Body>
            <Caption>Tap me!</Caption>
          </Card>
        </Card>

        {/* Loading Section */}
        <Card style={styles.section}>
          <Heading3>Loading States</Heading3>
          <View style={styles.loadingRow}>
            <LoadingSpinner size="small" />
            <LoadingSpinner size="medium" />
            <LoadingSpinner size="large" />
          </View>
          <Body style={{ textAlign: 'center', marginTop: SPACING.md }}>
            Different loading spinner sizes
          </Body>
        </Card>

        {/* Color Palette */}
        <Card style={styles.section}>
          <Heading3>Color Palette</Heading3>
          <View style={styles.colorRow}>
            <View style={[styles.colorSwatch, { backgroundColor: colors.primary }]} />
            <View style={[styles.colorSwatch, { backgroundColor: colors.secondary }]} />
            <View style={[styles.colorSwatch, { backgroundColor: colors.success }]} />
            <View style={[styles.colorSwatch, { backgroundColor: colors.warning }]} />
            <View style={[styles.colorSwatch, { backgroundColor: colors.error }]} />
          </View>
          <View style={styles.colorLabels}>
            <Caption>Primary</Caption>
            <Caption>Secondary</Caption>
            <Caption>Success</Caption>
            <Caption>Warning</Caption>
            <Caption>Error</Caption>
          </View>
        </Card>

        {/* Toast Demo */}
        <Card style={styles.section}>
          <Heading3>Toast Notifications</Heading3>
          <Button
            title="Show Success Toast"
            onPress={() => setShowToast(true)}
            variant="outline"
          />
        </Card>
      </Container>

      {/* Toast Component */}
      <Toast
        visible={showToast}
        message="This is a success toast message!"
        type="success"
        onHide={handleToastHide}
      />
    </ScreenWrapper>
  );
};

const styles = StyleSheet.create({
  section: {
    marginBottom: SPACING.lg,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: SPACING.md,
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  demoCard: {
    marginBottom: SPACING.md,
  },
  loadingRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  colorRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: SPACING.sm,
  },
  colorSwatch: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  colorLabels: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
});

export default DesignSystemDemo;