#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { TelegramUserClient } from './telegram.js';
import fs from 'fs';
import path from 'path';

// Validate environment variables
const API_ID = process.env.API_ID;
const API_HASH = process.env.API_HASH;
const SESSION_FILE = process.env.SESSION_FILE || '.telegram-session';

if (!API_ID || !API_HASH) {
  throw new Error('API_ID and API_HASH environment variables are required');
}

// Load session string from file if it exists
let sessionString = '';
try {
  if (fs.existsSync(SESSION_FILE)) {
    sessionString = fs.readFileSync(SESSION_FILE, 'utf-8').trim();
    console.error('Loaded existing session from file');
  }
} catch (error) {
  console.error('Could not load session file:', error);
}

// Initialize Telegram client
const telegramClient = new TelegramUserClient(
  parseInt(API_ID),
  API_HASH,
  sessionString
);

// Connect and authenticate
const initPromise = (async () => {
  try {
    const newSession = await telegramClient.connect();
    
    // Save session string to file for future use
    if (newSession && newSession !== sessionString) {
      fs.writeFileSync(SESSION_FILE, newSession, 'utf-8');
      console.error('Session saved to file for future use');
    }
    
    const userInfo = await telegramClient.getUserInfo();
    console.error(`Connected as: ${userInfo.first_name} (@${userInfo.username || 'no username'})`);
  } catch (error) {
    console.error('Failed to initialize Telegram client:', error);
    throw error;
  }
})();

// Tool input schemas
const ListMessagesSchema = z.object({
  chat_id: z.union([z.string(), z.number()]).describe('Chat ID or username (e.g., @channelname)'),
  limit: z.number().min(1).max(100).default(10).optional().describe('Number of messages to retrieve (1-100)'),
});

const GetChatHistorySchema = z.object({
  chat_id: z.union([z.string(), z.number()]).describe('Chat ID or username'),
  limit: z.number().min(1).max(100).default(20).optional().describe('Number of messages to retrieve'),
  offset_id: z.number().min(0).default(0).optional().describe('Message ID to start from (for pagination)'),
});

const SendMessageSchema = z.object({
  chat_id: z.union([z.string(), z.number()]).describe('Chat ID or username'),
  text: z.string().min(1).describe('Message text to send'),
  parse_mode: z.enum(['Markdown', 'MarkdownV2', 'HTML']).optional().describe('Message formatting mode'),
  disable_notification: z.boolean().optional().describe('Send message silently'),
});

const ReplyToMessageSchema = z.object({
  chat_id: z.union([z.string(), z.number()]).describe('Chat ID or username'),
  message_id: z.number().describe('ID of the message to reply to'),
  text: z.string().min(1).describe('Reply text'),
  parse_mode: z.enum(['Markdown', 'MarkdownV2', 'HTML']).optional().describe('Message formatting mode'),
});

const GetDialogsSchema = z.object({
  limit: z.number().min(1).max(200).default(100).optional().describe('Number of dialogs to retrieve (1-200)'),
});

const GetChatInfoSchema = z.object({
  chat_id: z.union([z.string(), z.number()]).describe('Chat ID or username'),
});

// Create MCP server
const server = new Server(
  {
    name: 'telegram-mcp-server',
    version: '2.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'list_messages',
        description:
          'Get recent messages from a Telegram chat using your user session. Works with any chat where you are a member, including private messages, groups, channels, and supergroups.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: {
              type: ['string', 'number'],
              description: 'Chat ID or username (e.g., @channelname, or numeric ID)',
            },
            limit: {
              type: 'number',
              description: 'Number of messages to retrieve (1-100, default: 10)',
              minimum: 1,
              maximum: 100,
              default: 10,
            },
          },
          required: ['chat_id'],
        },
      },
      {
        name: 'get_chat_history',
        description:
          'Get message history from a Telegram chat with pagination support using offset_id. Access any chat where you are a member.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: {
              type: ['string', 'number'],
              description: 'Chat ID or username',
            },
            limit: {
              type: 'number',
              description: 'Number of messages to retrieve (1-100, default: 20)',
              minimum: 1,
              maximum: 100,
              default: 20,
            },
            offset_id: {
              type: 'number',
              description: 'Message ID to start from for pagination (default: 0 for most recent)',
              minimum: 0,
              default: 0,
            },
          },
          required: ['chat_id'],
        },
      },
      {
        name: 'send_message',
        description:
          'Send a new message to a Telegram chat as your user account. Supports Markdown, MarkdownV2, and HTML formatting.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: {
              type: ['string', 'number'],
              description: 'Chat ID or username',
            },
            text: {
              type: 'string',
              description: 'Message text to send',
            },
            parse_mode: {
              type: 'string',
              enum: ['Markdown', 'MarkdownV2', 'HTML'],
              description: 'Message formatting mode (optional)',
            },
            disable_notification: {
              type: 'boolean',
              description: 'Send message silently (optional)',
            },
          },
          required: ['chat_id', 'text'],
        },
      },
      {
        name: 'reply_to_message',
        description:
          'Reply to a specific message in a Telegram chat. The reply will quote the original message.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: {
              type: ['string', 'number'],
              description: 'Chat ID or username',
            },
            message_id: {
              type: 'number',
              description: 'ID of the message to reply to',
            },
            text: {
              type: 'string',
              description: 'Reply text',
            },
            parse_mode: {
              type: 'string',
              enum: ['Markdown', 'MarkdownV2', 'HTML'],
              description: 'Message formatting mode (optional)',
            },
          },
          required: ['chat_id', 'message_id', 'text'],
        },
      },
      {
        name: 'get_dialogs',
        description:
          'Get all dialogs (chats) that your user account has access to. Includes private chats, groups, channels, and supergroups.',
        inputSchema: {
          type: 'object',
          properties: {
            limit: {
              type: 'number',
              description: 'Number of dialogs to retrieve (1-200, default: 100)',
              minimum: 1,
              maximum: 200,
              default: 100,
            },
          },
        },
      },
      {
        name: 'get_chat_info',
        description:
          'Get detailed information about a specific chat, including title, username, type, and member count.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: {
              type: ['string', 'number'],
              description: 'Chat ID or username',
            },
          },
          required: ['chat_id'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Wait for initialization to complete
  await initPromise;

  try {
    const { name, arguments: args } = request.params;

    switch (name) {
      case 'list_messages': {
        const input = ListMessagesSchema.parse(args);
        const messages = await telegramClient.listMessages(
          input.chat_id,
          input.limit || 10
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(messages, null, 2),
            },
          ],
        };
      }

      case 'get_chat_history': {
        const input = GetChatHistorySchema.parse(args);
        const history = await telegramClient.getChatHistory(
          input.chat_id,
          input.limit || 20,
          input.offset_id || 0
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(history, null, 2),
            },
          ],
        };
      }

      case 'send_message': {
        const input = SendMessageSchema.parse(args);
        const result = await telegramClient.sendMessage(
          input.chat_id,
          input.text,
          {
            parse_mode: input.parse_mode,
            disable_notification: input.disable_notification,
          }
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  success: true,
                  message_id: result.message_id,
                  chat_id: result.chat.id,
                  date: result.date,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'reply_to_message': {
        const input = ReplyToMessageSchema.parse(args);
        const result = await telegramClient.replyToMessage(
          input.chat_id,
          input.message_id,
          input.text,
          {
            parse_mode: input.parse_mode,
          }
        );
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  success: true,
                  message_id: result.message_id,
                  reply_to_message_id: input.message_id,
                  chat_id: result.chat.id,
                  date: result.date,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case 'get_dialogs': {
        const input = GetDialogsSchema.parse(args);
        const dialogs = await telegramClient.getDialogs(input.limit || 100);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(dialogs, null, 2),
            },
          ],
        };
      }

      case 'get_chat_info': {
        const input = GetChatInfoSchema.parse(args);
        const chatInfo = await telegramClient.getChatInfo(input.chat_id);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(chatInfo, null, 2),
            },
          ],
        };
      }

      default:
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${name}`
        );
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Invalid parameters: ${error.errors.map((e) => `${e.path.join('.')}: ${e.message}`).join(', ')}`
      );
    }
    if (error instanceof McpError) {
      throw error;
    }
    throw new McpError(
      ErrorCode.InternalError,
      `Error executing tool: ${error instanceof Error ? error.message : String(error)}`
    );
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Telegram MCP Server (User Session) running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
