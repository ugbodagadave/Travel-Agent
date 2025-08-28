import AsyncStorage from '@react-native-async-storage/async-storage';

// Simple utility to clear corrupted chat data
export const clearCorruptedChatData = async () => {
  try {
    console.log('Clearing corrupted chat data...');
    await AsyncStorage.removeItem('chat-storage');
    console.log('Successfully cleared chat storage');
    return true;
  } catch (error) {
    console.error('Failed to clear chat storage:', error);
    return false;
  }
};

// Clear all AsyncStorage (nuclear option)
export const clearAllStorage = async () => {
  try {
    console.log('Clearing all AsyncStorage...');
    await AsyncStorage.clear();
    console.log('Successfully cleared all storage');
    return true;
  } catch (error) {
    console.error('Failed to clear all storage:', error);
    return false;
  }
};

export default { clearCorruptedChatData, clearAllStorage };