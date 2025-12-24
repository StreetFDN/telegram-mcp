import type { VercelRequest, VercelResponse } from '@vercel/node';
import { TelegramClient } from '../telegram.js';
import { z } from 'zod';

const BOT_TOKEN = process.env.BOT_TOKEN;

if (!BOT_TOKEN) {
  throw new Error('BOT_TOKEN environment variable is required');
}

const telegramClient = new TelegramClient(BOT_TOKEN);

// Tool input schemas
const ListMessagesSchema = z.object({
  chat_id: z.union([z.string(), z.number()]),
  limit: z.number().min(1).max(100).default(10).optional(),
});

const SendMessageSchema = z.object({
  chat_id: z.union([z.string(), z.number()]),
  text: z.string().min(1),
  parse_mode: z.enum(['Markdown', 'MarkdownV2', 'HTML']).optional(),
  disable_notification: z.boolean().optional(),
});

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { action, params } = req.body;

    if (!action) {
      return res.status(400).json({ error: 'Action is required' });
    }

    let result;

    switch (action) {
      case 'list_messages': {
        const input = ListMessagesSchema.parse(params);
        result = await telegramClient.listMessages(
          input.chat_id,
          input.limit || 10
        );
        break;
      }

      case 'send_message': {
        const input = SendMessageSchema.parse(params);
        result = await telegramClient.sendMessage(
          input.chat_id,
          input.text,
          {
            parse_mode: input.parse_mode,
            disable_notification: input.disable_notification,
          }
        );
        break;
      }

      default:
        return res.status(400).json({ error: `Unknown action: ${action}` });
    }

    res.status(200).json({ success: true, data: result });
  } catch (error) {
    console.error('MCP Proxy error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        error: 'Validation error',
        details: error.errors,
      });
    }

    res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : String(error),
    });
  }
}
