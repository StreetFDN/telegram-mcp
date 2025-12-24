import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  const healthStatus = {
    status: 'healthy',
    service: 'telegram-mcp-server',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    botConfigured: !!process.env.BOT_TOKEN,
  };

  res.status(200).json(healthStatus);
}
