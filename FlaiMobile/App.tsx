import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { ThemeProvider } from './src/components/theme';
import { ErrorBoundary } from './src/components/feedback';
import Navigation from './src/navigation';
import { clearCorruptedChatData } from './src/utils/clearStorage';

export default function App() {
  // Temporary: Clear corrupted chat data on startup
  useEffect(() => {
    const clearData = async () => {
      const cleared = await clearCorruptedChatData();
      if (cleared) {
        console.log('App startup: Cleared corrupted chat data');
      }
    };
    clearData();
  }, []);

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <Navigation />
        <StatusBar style="auto" />
      </ThemeProvider>
    </ErrorBoundary>
  );
}
