import TelegramBot from 'node-telegram-bot-api';

export interface TelegramMessage {
  message_id: number;
  from?: {
    id: number;
    is_bot: boolean;
    first_name: string;
    last_name?: string;
    username?: string;
  };
  chat: {
    id: number;
    type: string;
    title?: string;
    username?: string;
    first_name?: string;
    last_name?: string;
  };
  date: number;
  text?: string;
  caption?: string;
  photo?: any[];
  video?: any;
  document?: any;
  audio?: any;
  voice?: any;
  sticker?: any;
  reply_to_message?: TelegramMessage;
}

export interface SendMessageOptions {
  parse_mode?: 'Markdown' | 'MarkdownV2' | 'HTML';
  disable_notification?: boolean;
  reply_to_message_id?: number;
}

export class TelegramClient {
  private bot: TelegramBot;
  private messageCache: Map<string, TelegramMessage[]> = new Map();

  constructor(token: string) {
    // Use polling only in development, not for production
    this.bot = new TelegramBot(token, { polling: false });
    this.setupMessageListener();
  }

  private setupMessageListener(): void {
    // Store incoming messages in cache
    this.bot.on('message', (msg) => {
      const chatId = msg.chat.id.toString();
      const messages = this.messageCache.get(chatId) || [];
      messages.unshift(msg as TelegramMessage);
      
      // Keep only last 1000 messages per chat
      if (messages.length > 1000) {
        messages.pop();
      }
      
      this.messageCache.set(chatId, messages);
    });
  }

  /**
   * Get recent messages from a chat
   * Note: Telegram Bot API has limitations on retrieving historical messages.
   * For best results:
   * 1. Add bot as admin to the chat
   * 2. Disable privacy mode via @BotFather
   * 3. Use getUpdates for recent messages
   */
  async listMessages(
    chatId: string | number,
    limit: number = 10
  ): Promise<TelegramMessage[]> {
    try {
      // Try to get messages from cache first
      const chatIdStr = chatId.toString();
      const cachedMessages = this.messageCache.get(chatIdStr);
      
      if (cachedMessages && cachedMessages.length > 0) {
        return cachedMessages.slice(0, limit);
      }

      // If no cached messages, try to get updates
      const updates = await this.bot.getUpdates({ limit: 100 });
      const chatMessages: TelegramMessage[] = [];

      for (const update of updates) {
        if (update.message && update.message.chat.id.toString() === chatIdStr) {
          chatMessages.push(update.message as TelegramMessage);
        }
      }

      // Sort by date (newest first)
      chatMessages.sort((a, b) => b.date - a.date);
      
      // Update cache
      if (chatMessages.length > 0) {
        this.messageCache.set(chatIdStr, chatMessages);
      }

      return chatMessages.slice(0, limit);
    } catch (error) {
      throw new Error(
        `Failed to list messages: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get chat history with pagination
   */
  async getChatHistory(
    chatId: string | number,
    limit: number = 20,
    offset: number = 0
  ): Promise<{
    messages: TelegramMessage[];
    total: number;
    offset: number;
    limit: number;
  }> {
    try {
      const allMessages = await this.listMessages(chatId, 100);
      const paginatedMessages = allMessages.slice(offset, offset + limit);

      return {
        messages: paginatedMessages,
        total: allMessages.length,
        offset,
        limit,
      };
    } catch (error) {
      throw new Error(
        `Failed to get chat history: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Send a message to a chat
   */
  async sendMessage(
    chatId: string | number,
    text: string,
    options?: SendMessageOptions
  ): Promise<TelegramMessage> {
    try {
      const message = await this.bot.sendMessage(chatId, text, {
        parse_mode: options?.parse_mode,
        disable_notification: options?.disable_notification,
      });

      return message as TelegramMessage;
    } catch (error) {
      throw new Error(
        `Failed to send message: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Reply to a specific message
   */
  async replyToMessage(
    chatId: string | number,
    messageId: number,
    text: string,
    options?: Omit<SendMessageOptions, 'reply_to_message_id'>
  ): Promise<TelegramMessage> {
    try {
      const message = await this.bot.sendMessage(chatId, text, {
        reply_to_message_id: messageId,
        parse_mode: options?.parse_mode,
      });

      return message as TelegramMessage;
    } catch (error) {
      throw new Error(
        `Failed to reply to message: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get information about the bot
   */
  async getBotInfo(): Promise<TelegramBot.User> {
    try {
      return await this.bot.getMe();
    } catch (error) {
      throw new Error(
        `Failed to get bot info: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get chat information
   */
  async getChatInfo(chatId: string | number): Promise<TelegramBot.Chat> {
    try {
      return await this.bot.getChat(chatId);
    } catch (error) {
      throw new Error(
        `Failed to get chat info: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }
}
