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
import { TelegramClient } from './telegram.js';

// Validate environment variables
const BOT_TOKEN = process.env.BOT_TOKEN;
if (!BOT_TOKEN) {
  throw new Error('BOT_TOKEN environment variable is required');
}

// Initialize Telegram client
const telegramClient = new TelegramClient(BOT_TOKEN);

// Tool input schemas
const ListMessagesSchema = z.object({
  chat_id: z.union([z.string(), z.number()]).describe('Chat ID or username (e.g., @channelname)'),
  limit: z.number().min(1).max(100).default(10).optional().describe('Number of messages to retrieve (1-100)'),
});

const GetChatHistorySchema = z.object({
  chat_id: z.union([z.string(), z.number()]).describe('Chat ID or username'),
  limit: z.number().min(1).max(100).default(20).optional().describe('Number of messages to retrieve'),
  offset: z.number().min(0).default(0).optional().describe('Offset for pagination'),
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

// Create MCP server
const server = new Server(
  {
    name: 'telegram-mcp-server',
    version: '1.0.0',
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
          'Get recent messages from a Telegram chat. Returns the most recent messages with sender info, timestamp, and content.',
        inputSchema: {
          type: 'object',
          properties: {
            chat_id: {
              type: ['string', 'number'],
              description: 'Chat ID or username (e.g., @channelname)',
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
          'Get message history from a Telegram chat with pagination support. Allows retrieving older messages using offset.',
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
            offset: {
              type: 'number',
              description: 'Offset for pagination (default: 0)',
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
          'Send a new message to a Telegram chat. Supports Markdown, MarkdownV2, and HTML formatting.',
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
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
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
          input.offset || 0
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
  console.error('Telegram MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
