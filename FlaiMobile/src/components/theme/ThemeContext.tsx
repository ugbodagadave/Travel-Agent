import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Theme, ThemeContextType, ThemeColors } from '../../types';
import { themes } from '../../themes';
import { STORAGE_KEYS } from '../../constants';

// Create Theme Context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Theme Provider Props
interface ThemeProviderProps {
  children: ReactNode;
}

// Theme Provider Component
export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>('light');
  const [colors, setColors] = useState<ThemeColors>(themes.light);
  const [isLoading, setIsLoading] = useState(true);

  // Load saved theme on mount
  useEffect(() => {
    loadSavedTheme();
  }, []);

  // Update colors when theme changes
  useEffect(() => {
    setColors(themes[theme]);
  }, [theme]);

  // Load theme from storage
  const loadSavedTheme = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem(STORAGE_KEYS.theme);
      if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
        setThemeState(savedTheme as Theme);
      }
    } catch (error) {
      console.warn('Failed to load saved theme:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Save theme to storage
  const saveTheme = async (newTheme: Theme) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.theme, newTheme);
    } catch (error) {
      console.warn('Failed to save theme:', error);
    }
  };

  // Set theme
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    saveTheme(newTheme);
  };

  // Toggle between light and dark theme
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  // Context value
  const contextValue: ThemeContextType = {
    theme,
    colors,
    toggleTheme,
    setTheme,
    isLoading,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Custom hook to use theme
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeContext;