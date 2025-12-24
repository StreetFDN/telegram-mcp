import { TelegramClient } from 'telegram';
import { StringSession } from 'telegram/sessions/index.js';
import { Api } from 'telegram/tl/index.js';
import input from 'input';

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
  media?: any;
  reply_to_message?: TelegramMessage;
}

export interface SendMessageOptions {
  parse_mode?: 'Markdown' | 'MarkdownV2' | 'HTML';
  disable_notification?: boolean;
  reply_to_message_id?: number;
}

export class TelegramUserClient {
  private client: TelegramClient;
  private apiId: number;
  private apiHash: string;
  private sessionString: string;

  constructor(apiId: number, apiHash: string, sessionString: string = '') {
    this.apiId = apiId;
    this.apiHash = apiHash;
    this.sessionString = sessionString;
    
    const stringSession = new StringSession(sessionString);
    this.client = new TelegramClient(stringSession, apiId, apiHash, {
      connectionRetries: 5,
    });
  }

  /**
   * Initialize and authenticate the client
   */
  async connect(): Promise<string> {
    await this.client.connect();

    if (!await this.client.isUserAuthorized()) {
      console.error('User not authorized. Starting authentication...');
      
      await this.client.start({
        phoneNumber: async () => await input.text('Please enter your phone number: '),
        password: async () => await input.text('Please enter your password: '),
        phoneCode: async () => await input.text('Please enter the code you received: '),
        onError: (err) => console.error('Authentication error:', err),
      });

      console.error('Successfully authenticated!');
    }

    // Save and return the session string for future use
    const session = this.client.session.save() as unknown as string;
    return session;
  }

  /**
   * Convert Telegram API message to our format
   */
  private convertMessage(msg: Api.Message): TelegramMessage | null {
    if (!msg.message && !msg.media) return null;

    const peer = msg.peerId;
    let chatId: number;
    let chatType: string;
    let chatTitle: string | undefined;
    let chatUsername: string | undefined;

    if (peer instanceof Api.PeerUser) {
      chatId = Number(peer.userId);
      chatType = 'private';
    } else if (peer instanceof Api.PeerChat) {
      chatId = -Number(peer.chatId);
      chatType = 'group';
    } else if (peer instanceof Api.PeerChannel) {
      chatId = -1000000000000 - Number(peer.channelId);
      chatType = 'channel';
    } else {
      return null;
    }

    const fromUser = msg.fromId instanceof Api.PeerUser ? {
      id: Number(msg.fromId.userId),
      is_bot: false,
      first_name: '',
      username: undefined,
    } : undefined;

    return {
      message_id: msg.id,
      from: fromUser,
      chat: {
        id: chatId,
        type: chatType,
        title: chatTitle,
        username: chatUsername,
      },
      date: msg.date,
      text: msg.message || undefined,
      caption: msg.message || undefined,
      media: msg.media,
      reply_to_message: undefined, // Can be populated if needed
    };
  }

  /**
   * Resolve entity (chat/user/channel) from various input formats
   */
  private async resolveEntity(chatId: string | number): Promise<Api.TypeInputPeer> {
    if (typeof chatId === 'string' && chatId.startsWith('@')) {
      // Username
      const entity = await this.client.getEntity(chatId);
      return entity as Api.TypeInputPeer;
    } else if (typeof chatId === 'number' || !isNaN(Number(chatId))) {
      // Numeric ID
      const numId = typeof chatId === 'number' ? chatId : Number(chatId);
      
      if (numId < 0) {
        // Group or channel
        if (numId < -1000000000000) {
          // Channel/supergroup
          const channelId = -1000000000000 - numId;
          return new Api.InputPeerChannel({
            channelId: BigInt(channelId),
            accessHash: BigInt(0), // Will be resolved by client
          });
        } else {
          // Regular group
          return new Api.InputPeerChat({
            chatId: BigInt(-numId),
          });
        }
      } else {
        // User
        return new Api.InputPeerUser({
          userId: BigInt(numId),
          accessHash: BigInt(0), // Will be resolved by client
        });
      }
    }

    // Fallback: try to get entity directly
    const entity = await this.client.getEntity(chatId);
    return entity as Api.TypeInputPeer;
  }

  /**
   * Get recent messages from a chat
   * Using user session allows access to ALL messages in chats where user is a member
   */
  async listMessages(
    chatId: string | number,
    limit: number = 10
  ): Promise<TelegramMessage[]> {
    try {
      const entity = await this.resolveEntity(chatId);
      
      const messages = await this.client.getMessages(entity, {
        limit: limit,
      });

      const convertedMessages: TelegramMessage[] = [];
      for (const msg of messages) {
        if (msg instanceof Api.Message) {
          const converted = this.convertMessage(msg);
          if (converted) {
            convertedMessages.push(converted);
          }
        }
      }

      return convertedMessages;
    } catch (error) {
      throw new Error(
        `Failed to list messages: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get chat history with pagination using offset_id
   */
  async getChatHistory(
    chatId: string | number,
    limit: number = 20,
    offsetId: number = 0
  ): Promise<{
    messages: TelegramMessage[];
    total: number;
    offset_id: number;
    limit: number;
  }> {
    try {
      const entity = await this.resolveEntity(chatId);
      
      const messages = await this.client.getMessages(entity, {
        limit: limit,
        offsetId: offsetId,
      });

      const convertedMessages: TelegramMessage[] = [];
      for (const msg of messages) {
        if (msg instanceof Api.Message) {
          const converted = this.convertMessage(msg);
          if (converted) {
            convertedMessages.push(converted);
          }
        }
      }

      return {
        messages: convertedMessages,
        total: messages.total || convertedMessages.length,
        offset_id: offsetId,
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
      const entity = await this.resolveEntity(chatId);
      
      let parseMode: Api.TypeTextParseMode | undefined;
      if (options?.parse_mode === 'Markdown' || options?.parse_mode === 'MarkdownV2') {
        parseMode = 'md' as any;
      } else if (options?.parse_mode === 'HTML') {
        parseMode = 'html' as any;
      }

      const result = await this.client.sendMessage(entity, {
        message: text,
        parseMode: parseMode,
        silent: options?.disable_notification,
        replyTo: options?.reply_to_message_id,
      });

      if (result instanceof Api.Message) {
        const converted = this.convertMessage(result);
        if (converted) {
          return converted;
        }
      }

      // Fallback if conversion fails
      throw new Error('Failed to convert sent message');
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
    return this.sendMessage(chatId, text, {
      ...options,
      reply_to_message_id: messageId,
    });
  }

  /**
   * Get information about the authenticated user
   */
  async getUserInfo(): Promise<any> {
    try {
      const me = await this.client.getMe();
      return {
        id: Number(me.id),
        is_bot: me.bot || false,
        first_name: me.firstName || '',
        last_name: me.lastName || '',
        username: me.username || '',
        phone: me.phone || '',
      };
    } catch (error) {
      throw new Error(
        `Failed to get user info: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get chat information
   */
  async getChatInfo(chatId: string | number): Promise<any> {
    try {
      const entity = await this.client.getEntity(chatId);
      
      if (entity instanceof Api.User) {
        return {
          id: Number(entity.id),
          type: 'private',
          first_name: entity.firstName || '',
          last_name: entity.lastName || '',
          username: entity.username || '',
        };
      } else if (entity instanceof Api.Chat) {
        return {
          id: -Number(entity.id),
          type: 'group',
          title: entity.title,
        };
      } else if (entity instanceof Api.Channel) {
        return {
          id: -1000000000000 - Number(entity.id),
          type: entity.broadcast ? 'channel' : 'supergroup',
          title: entity.title,
          username: entity.username || '',
        };
      }

      throw new Error('Unknown entity type');
    } catch (error) {
      throw new Error(
        `Failed to get chat info: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get all dialogs (chats) the user has access to
   */
  async getDialogs(limit: number = 100): Promise<any[]> {
    try {
      const dialogs = await this.client.getDialogs({ limit });
      
      return dialogs.map((dialog) => {
        const entity = dialog.entity;
        let chatInfo: any = {};

        if (entity instanceof Api.User) {
          chatInfo = {
            id: Number(entity.id),
            type: 'private',
            first_name: entity.firstName || '',
            last_name: entity.lastName || '',
            username: entity.username || '',
          };
        } else if (entity instanceof Api.Chat) {
          chatInfo = {
            id: -Number(entity.id),
            type: 'group',
            title: entity.title,
          };
        } else if (entity instanceof Api.Channel) {
          chatInfo = {
            id: -1000000000000 - Number(entity.id),
            type: entity.broadcast ? 'channel' : 'supergroup',
            title: entity.title,
            username: entity.username || '',
          };
        }

        return {
          ...chatInfo,
          unread_count: dialog.unreadCount,
          last_message_date: dialog.date,
        };
      });
    } catch (error) {
      throw new Error(
        `Failed to get dialogs: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Disconnect the client
   */
  async disconnect(): Promise<void> {
    await this.client.disconnect();
  }
}
