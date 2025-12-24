import type { VercelRequest, VercelResponse } from '@vercel/node';
import { TelegramClient } from '../telegram.js';

const BOT_TOKEN = process.env.BOT_TOKEN;

if (!BOT_TOKEN) {
  throw new Error('BOT_TOKEN environment variable is required');
}

const telegramClient = new TelegramClient(BOT_TOKEN);

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Telegram webhook payload
    const update = req.body;

    // Basic webhook validation
    if (!update || !update.update_id) {
      return res.status(400).json({ error: 'Invalid webhook payload' });
    }

    // Process the update (you can extend this based on your needs)
    console.log('Received Telegram update:', update);

    // Respond to Telegram
    res.status(200).json({ ok: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : String(error)
    });
  }
}
