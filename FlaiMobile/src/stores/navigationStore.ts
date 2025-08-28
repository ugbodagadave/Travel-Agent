import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NavigationStore } from '../types';
import { StorageService } from '../utils';
import { STORAGE_KEYS } from '../constants';

export const useNavigationStore = create<NavigationStore>()(
  persist(
    (set, get) => ({
      // Initial state
      hasCompletedOnboarding: false,
      currentRoute: '',
      isDeepLink: false,
      deepLinkUrl: undefined,

      // Actions
      setHasCompletedOnboarding: (completed: boolean) => {
        set({ hasCompletedOnboarding: completed });
      },

      setCurrentRoute: (route: string) => {
        set({ currentRoute: route });
      },

      setDeepLink: (url: string) => {
        set({ 
          isDeepLink: true, 
          deepLinkUrl: url 
        });
      },

      clearDeepLink: () => {
        set({ 
          isDeepLink: false, 
          deepLinkUrl: undefined 
        });
      },

      initializeNavigation: async () => {
        try {
          const completed = await StorageService.getItem(STORAGE_KEYS.onboardingCompleted);
          if (completed === 'true') {
            set({ hasCompletedOnboarding: true });
          }
        } catch (error) {
          console.error('Failed to initialize navigation state:', error);
        }
      },
    }),
    {
      name: 'navigation-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        hasCompletedOnboarding: state.hasCompletedOnboarding,
      }),
    }
  )
);