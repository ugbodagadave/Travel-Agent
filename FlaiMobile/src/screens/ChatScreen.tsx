import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  StyleSheet, 
  ScrollView, 
  KeyboardAvoidingView, 
  Platform,
  TextInput,
  TouchableOpacity,
  Keyboard
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { 
  Typography, 
  Button, 
  Container,
  Card,
  LoadingSpinner
} from '../components/ui';
import { ScreenWrapper, Header } from '../components/layout';
import { useTheme } from '../components/theme';
import { useChatStore } from '../stores';
import { Message } from '../types';
import { SPACING, HEADER_HEIGHT } from '../constants';
import { AccessibilityUtils, MessageUtils } from '../utils';
import { Ionicons } from '@expo/vector-icons';

export default function ChatScreen() {
  const { colors } = useTheme();
  const { 
    messages, 
    isTyping, 
    isConnected, 
    conversationState,
    addMessage, 
    sendMessage,
    retryMessage
  } = useChatStore();
  
  const [inputText, setInputText] = useState('');
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const inputRef = useRef<TextInput>(null);

  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener('keyboardDidShow', () => {
      setIsKeyboardVisible(true);
      scrollToBottom();
    });
    
    const keyboardDidHideListener = Keyboard.addListener('keyboardDidHide', () => {
      setIsKeyboardVisible(false);
    });

    return () => {
      keyboardDidShowListener?.remove();
      keyboardDidHideListener?.remove();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const messageText = inputText.trim();
    setInputText('');
    inputRef.current?.blur();

    await sendMessage(messageText);
  };

  const handleRetryMessage = async (messageId: string) => {
    await retryMessage(messageId);
  };

  const renderMessage = (message: Message, index: number) => {
    const isLastMessage = index === messages.length - 1;
    
    return (
      <View
        key={message.id}
        style={[
          styles.messageContainer,
          message.isUser ? styles.userMessageContainer : styles.botMessageContainer,
          isLastMessage && styles.lastMessage,
        ]}
        accessibilityLabel={`${message.isUser ? 'Your' : 'AI assistant'} message`}
        accessibilityRole="text"
      >
        <Card
          variant="flat"
          style={[
            styles.messageCard,
            {
              backgroundColor: message.isUser ? colors.userMessage : colors.botMessage,
            },
          ]}
        >
          <Typography
            variant="body"
            style={[
              styles.messageText,
              {
                color: message.isUser ? colors.userMessageText : colors.botMessageText,
              },
            ]}
          >
            {message.text}
          </Typography>
          
          {/* Message Status */}
          <View style={styles.messageFooter}>
            <Typography
              variant="caption"
              style={[
                styles.messageTime,
                {
                  color: message.isUser 
                    ? colors.userMessageText + '80' 
                    : colors.botMessageText + '80',
                },
              ]}
            >
              {MessageUtils.formatMessageTime(message)}
            </Typography>
            
            {message.isUser && message.status && (
              <View style={styles.messageStatus}>
                {message.status === 'sending' && (
                  <LoadingSpinner 
                    size="small" 
                    color={colors.userMessageText + '80'} 
                  />
                )}
                {message.status === 'sent' && (
                  <Ionicons
                    name="checkmark"
                    size={14}
                    color={colors.userMessageText + '80'}
                    accessibilityLabel="Message sent"
                    accessibilityRole="image"
                  />
                )}
                {message.status === 'error' && (
                  <TouchableOpacity
                    onPress={() => handleRetryMessage(message.id)}
                    style={styles.retryButton}
                    accessibilityLabel="Retry sending message"
                    accessibilityRole="button"
                    accessibilityHint="Double tap to retry sending message"
                  >
                    <Ionicons
                      name="refresh"
                      size={14}
                      color={colors.error}
                      accessibilityLabel="Retry message"
                      accessibilityRole="image"
                    />
                  </TouchableOpacity>
                )}
              </View>
            )}
          </View>
        </Card>
      </View>
    );
  };

  const renderTypingIndicator = () => {
    if (!isTyping) return null;

    return (
      <View style={[styles.messageContainer, styles.botMessageContainer]}>
        <Card
          variant="flat"
          style={[styles.messageCard, { backgroundColor: colors.botMessage }]}
        >
          <View style={styles.typingContainer}>
            <LoadingSpinner size="small" color={colors.primary} />
            <Typography
              variant="caption"
              style={[styles.typingText, { color: colors.botMessageText }]}
            >
              AI is typing...
            </Typography>
          </View>
        </Card>
      </View>
    );
  };

  const renderEmptyState = () => {
    if (messages.length > 0) return null;

    return (
      <View style={styles.emptyContainer}>
        <View style={[styles.welcomeIcon, { backgroundColor: colors.primaryLight }]}>
          <Ionicons
            name="chatbubble-ellipses"
            size={48}
            color={colors.primary}
            accessibilityLabel="Start conversation"
            accessibilityRole="image"
          />
        </View>
        
        <Typography
          variant="h3"
          style={[styles.welcomeTitle, { color: colors.text }]}
          align="center"
        >
          Welcome to Flai!
        </Typography>
        
        <Typography
          variant="body"
          style={[styles.welcomeDescription, { color: colors.textSecondary }]}
          align="center"
        >
          I'm your AI travel assistant. Tell me where you'd like to go and I'll help you find the perfect flight!
        </Typography>

        <View style={styles.suggestionContainer}>
          <Typography
            variant="caption"
            style={[styles.suggestionTitle, { color: colors.textSecondary }]}
          >
            Try saying:
          </Typography>
          
          {[
            "I want to fly from New York to London",
            "Find me flights to Tokyo next month",
            "Book a round trip to Paris for 2 people"
          ].map((suggestion, index) => (
            <TouchableOpacity
              key={index}
              style={[styles.suggestionChip, { borderColor: colors.border }]}
              onPress={() => setInputText(suggestion)}
              accessibilityLabel={`Suggestion: ${suggestion}`}
              accessibilityRole="button"
              accessibilityHint="Double tap to use this suggestion"
            >
              <Typography
                variant="caption"
                style={[styles.suggestionText, { color: colors.text }]}
              >
                "{suggestion}"
              </Typography>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  };

  return (
    <ScreenWrapper>
      <SafeAreaView style={styles.container}>
        <Header
          title="Chat"
          rightComponent={
            <View style={styles.connectionStatus}>
              <View
                style={[
                  styles.connectionDot,
                  { backgroundColor: isConnected ? colors.success : colors.error },
                ]}
                accessibilityLabel={isConnected ? 'Connected' : 'Disconnected'}
              />
            </View>
          }
        />
        
        <KeyboardAvoidingView
          style={styles.keyboardAvoidingView}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={HEADER_HEIGHT}
        >
          <ScrollView
            ref={scrollViewRef}
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            accessibilityLabel="Chat messages"
          >
            {renderEmptyState()}
            {messages.map(renderMessage)}
            {renderTypingIndicator()}
          </ScrollView>

          {/* Input Area */}
          <View style={[styles.inputContainer, { backgroundColor: colors.surface }]}>
            <View style={[styles.inputWrapper, { borderColor: colors.border }]}>
              <TextInput
                ref={inputRef}
                style={[
                  styles.textInput,
                  {
                    color: colors.text,
                    backgroundColor: colors.background,
                  },
                ]}
                value={inputText}
                onChangeText={setInputText}
                placeholder="Type your message..."
                placeholderTextColor={colors.textSecondary}
                multiline
                maxLength={1000}
                returnKeyType="send"
                onSubmitEditing={handleSendMessage}
                blurOnSubmit={false}
                accessibilityLabel="Type your travel request"
              />
              
              <TouchableOpacity
                style={[
                  styles.sendButton,
                  {
                    backgroundColor: inputText.trim() ? colors.primary : colors.border,
                  },
                ]}
                onPress={handleSendMessage}
                disabled={!inputText.trim()}
                accessibilityLabel="Send message"
                accessibilityRole="button"
                accessibilityHint="Double tap to send message"
              >
                <Ionicons
                  name="send"
                  size={20}
                  color={inputText.trim() ? colors.textOnPrimary : colors.textSecondary}
                  accessibilityLabel="Send"
                  accessibilityRole="image"
                />
              </TouchableOpacity>
            </View>
            
            {inputText.length > 800 && (
              <Typography
                variant="caption"
                style={[
                  styles.characterCount,
                  { 
                    color: inputText.length > 950 ? colors.error : colors.textSecondary 
                  },
                ]}
              >
                {inputText.length}/1000
              </Typography>
            )}
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    flexGrow: 1,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  messageContainer: {
    marginVertical: SPACING.xs,
  },
  userMessageContainer: {
    alignItems: 'flex-end',
  },
  botMessageContainer: {
    alignItems: 'flex-start',
  },
  lastMessage: {
    marginBottom: SPACING.md,
  },
  messageCard: {
    maxWidth: '85%',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: 16,
  },
  messageText: {
    lineHeight: 20,
  },
  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: SPACING.xs,
  },
  messageTime: {
    fontSize: 11,
  },
  messageStatus: {
    marginLeft: SPACING.xs,
  },
  retryButton: {
    padding: 2,
  },
  typingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingText: {
    marginLeft: SPACING.sm,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
  },
  welcomeIcon: {
    width: 96,
    height: 96,
    borderRadius: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.lg,
  },
  welcomeTitle: {
    marginBottom: SPACING.md,
  },
  welcomeDescription: {
    marginBottom: SPACING.xl,
    lineHeight: 22,
  },
  suggestionContainer: {
    width: '100%',
    maxWidth: 300,
  },
  suggestionTitle: {
    marginBottom: SPACING.sm,
    textAlign: 'center',
  },
  suggestionChip: {
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  suggestionText: {
    textAlign: 'center',
    lineHeight: 16,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  inputContainer: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderWidth: 1,
    borderRadius: 24,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    lineHeight: 20,
    maxHeight: 100,
    marginRight: SPACING.sm,
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  characterCount: {
    textAlign: 'right',
    marginTop: SPACING.xs,
    marginRight: SPACING.sm,
  },
});