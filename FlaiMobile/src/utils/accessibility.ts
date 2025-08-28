import { AccessibilityInfo, Platform } from 'react-native';

// Accessibility utility functions
export class AccessibilityUtils {
  /**
   * Check if screen reader is enabled
   */
  static async isScreenReaderEnabled(): Promise<boolean> {
    try {
      return await AccessibilityInfo.isScreenReaderEnabled();
    } catch (error) {
      console.warn('Failed to check screen reader status:', error);
      return false;
    }
  }

  /**
   * Check if reduce motion is enabled (iOS only)
   */
  static async isReduceMotionEnabled(): Promise<boolean> {
    if (Platform.OS !== 'ios') {
      return false;
    }
    
    try {
      return await AccessibilityInfo.isReduceMotionEnabled();
    } catch (error) {
      console.warn('Failed to check reduce motion status:', error);
      return false;
    }
  }

  /**
   * Announce text to screen reader
   */
  static announceForAccessibility(text: string): void {
    AccessibilityInfo.announceForAccessibility(text);
  }

  /**
   * Set accessibility focus to an element
   */
  static setAccessibilityFocus(reactTag: number): void {
    AccessibilityInfo.setAccessibilityFocus(reactTag);
  }

  /**
   * Generate accessibility label for buttons
   */
  static getButtonLabel(title: string, disabled?: boolean, loading?: boolean): string {
    let label = title;
    
    if (loading) {
      label += ', loading';
    } else if (disabled) {
      label += ', disabled';
    }
    
    return label;
  }

  /**
   * Generate accessibility hint for interactive elements
   */
  static getInteractionHint(action: string): string {
    return `Double tap to ${action}`;
  }

  /**
   * Get accessibility role for custom components
   */
  static getAccessibilityRole(type: 'button' | 'link' | 'text' | 'image' | 'list' | 'listitem'): string {
    return type;
  }

  /**
   * Create accessibility state object
   */
  static createAccessibilityState(options: {
    disabled?: boolean;
    selected?: boolean;
    checked?: boolean;
    expanded?: boolean;
    busy?: boolean;
  }) {
    const state: any = {};
    
    if (options.disabled !== undefined) state.disabled = options.disabled;
    if (options.selected !== undefined) state.selected = options.selected;
    if (options.checked !== undefined) state.checked = options.checked;
    if (options.expanded !== undefined) state.expanded = options.expanded;
    if (options.busy !== undefined) state.busy = options.busy;
    
    return state;
  }

  /**
   * Format currency for accessibility
   */
  static formatCurrencyForAccessibility(amount: string, currency: string): string {
    return `${amount} ${currency}`;
  }

  /**
   * Format time for accessibility
   */
  static formatTimeForAccessibility(time: string): string {
    // Convert 24-hour format to more natural speech
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours, 10);
    const minute = parseInt(minutes, 10);
    
    let formattedTime = '';
    
    if (hour === 0) {
      formattedTime = '12';
    } else if (hour <= 12) {
      formattedTime = hour.toString();
    } else {
      formattedTime = (hour - 12).toString();
    }
    
    if (minute > 0) {
      formattedTime += ` ${minute}`;
    }
    
    formattedTime += hour < 12 ? ' AM' : ' PM';
    
    return formattedTime;
  }

  /**
   * Format date for accessibility
   */
  static formatDateForAccessibility(date: Date): string {
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    
    return date.toLocaleDateString('en-US', options);
  }

  /**
   * Create semantic description for flight information
   */
  static formatFlightForAccessibility(flight: {
    departure: { city: string; time: string };
    arrival: { city: string; time: string };
    duration: string;
    price: string;
    currency: string;
  }): string {
    const depTime = this.formatTimeForAccessibility(flight.departure.time);
    const arrTime = this.formatTimeForAccessibility(flight.arrival.time);
    const price = this.formatCurrencyForAccessibility(flight.price, flight.currency);
    
    return `Flight from ${flight.departure.city} at ${depTime} to ${flight.arrival.city} at ${arrTime}, duration ${flight.duration}, price ${price}`;
  }
}

// Constants for accessibility
export const ACCESSIBILITY_CONSTANTS = {
  // Minimum touch target size (44pt recommended by Apple/Google)
  MIN_TOUCH_TARGET_SIZE: 44,
  
  // Timeout for accessibility announcements
  ANNOUNCEMENT_DELAY: 100,
  
  // Common accessibility labels
  LABELS: {
    close: 'Close',
    back: 'Go back',
    menu: 'Menu',
    search: 'Search',
    loading: 'Loading',
    error: 'Error',
    success: 'Success',
    warning: 'Warning',
    info: 'Information',
  },
  
  // Common accessibility hints
  HINTS: {
    button: 'Double tap to activate',
    link: 'Double tap to open link',
    textInput: 'Double tap to edit text',
    picker: 'Double tap to open picker',
    slider: 'Swipe up or down to adjust value',
  },
};

export default AccessibilityUtils;