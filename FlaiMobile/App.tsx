import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { ThemeProvider } from './src/components/theme';
import { ErrorBoundary } from './src/components/feedback';
import Navigation from './src/navigation';

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <Navigation />
        <StatusBar style="auto" />
      </ThemeProvider>
    </ErrorBoundary>
  );
}
