import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatState, Message, ConversationState, FlightOffer } from '../types';
import { StringUtils } from '../utils';
import { STORAGE_KEYS } from '../constants';

interface ChatStore extends ChatState {
  // Additional state
  flightOffers: FlightOffer[];
  selectedOffer: FlightOffer | null;
  
  // Actions
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setTyping: (isTyping: boolean) => void;
  setConnected: (isConnected: boolean) => void;
  setConversationState: (state: ConversationState) => void;
  setFlightOffers: (offers: FlightOffer[]) => void;
  selectOffer: (offer: FlightOffer) => void;
  sendMessage: (text: string) => Promise<void>;
  clearChat: () => void;
  retryMessage: (messageId: string) => Promise<void>;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Initial state
      messages: [],
      isTyping: false,
      isConnected: false,
      conversationState: 'GATHERING_INFO',
      flightOffers: [],
      selectedOffer: null,

      // Actions
      addMessage: (messageData) => {
        const message: Message = {
          ...messageData,
          id: StringUtils.generateId(),
          timestamp: new Date(),
        };
        
        set((state) => ({
          messages: [...state.messages, message],
        }));
      },

      updateMessage: (id, updates) => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg
          ),
        }));
      },

      setTyping: (isTyping) => {
        set({ isTyping });
      },

      setConnected: (isConnected) => {
        set({ isConnected });
      },

      setConversationState: (conversationState) => {
        set({ conversationState });
      },

      setFlightOffers: (flightOffers) => {
        set({ flightOffers });
      },

      selectOffer: (selectedOffer) => {
        set({ selectedOffer });
      },

      sendMessage: async (text) => {
        const { addMessage, updateMessage } = get();
        
        // Add user message immediately (optimistic update)
        const userMessage = {
          text,
          isUser: true,
          status: 'sending' as const,
        };
        
        addMessage(userMessage);
        const messageId = get().messages[get().messages.length - 1].id;

        try {
          // TODO: Implement actual API call
          // const response = await ChatService.sendMessage(text);
          
          // Mock response for development
          await new Promise(resolve => setTimeout(resolve, 1000));
          updateMessage(messageId, { status: 'sent' });
          
          // Mock bot response
          setTimeout(() => {
            addMessage({
              text: "I understand you want to travel. Let me help you find the perfect flight!",
              isUser: false,
            });
          }, 500);

        } catch (error) {
          console.error('Failed to send message:', error);
          updateMessage(messageId, { status: 'error' });
        }
      },

      retryMessage: async (messageId) => {
        const { messages, updateMessage } = get();
        const message = messages.find(m => m.id === messageId);
        
        if (!message) return;

        updateMessage(messageId, { status: 'sending' });
        
        try {
          // TODO: Implement actual retry logic
          await new Promise(resolve => setTimeout(resolve, 1000));
          updateMessage(messageId, { status: 'sent' });
        } catch (error) {
          console.error('Failed to retry message:', error);
          updateMessage(messageId, { status: 'error' });
        }
      },

      clearChat: () => {
        set({
          messages: [],
          conversationState: 'GATHERING_INFO',
          flightOffers: [],
          selectedOffer: null,
        });
      },
    }),
    {
      name: 'chat-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        messages: state.messages,
        conversationState: state.conversationState,
        flightOffers: state.flightOffers,
        selectedOffer: state.selectedOffer,
      }),
    }
  )
);