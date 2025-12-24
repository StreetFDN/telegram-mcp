# Quick Deployment Guide

Deploy your Telegram MCP Server to Vercel in minutes.

## Quick Start

### 1. Prerequisites

- GitHub account
- Vercel account (free tier works)
- Telegram bot token from [@BotFather](https://t.me/BotFather)

### 2. One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/StreetFDN/telegram-mcp)

**Or manually:**

1. Fork this repository
2. Go to [Vercel](https://vercel.com/new)
3. Import your forked repository
4. Add environment variable: `BOT_TOKEN`
5. Click Deploy

### 3. Verify Deployment

Once deployed, test your endpoints:

```bash
# Replace YOUR_DEPLOYMENT_URL with your actual Vercel URL
curl https://YOUR_DEPLOYMENT_URL/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "telegram-mcp-server",
  "version": "1.0.0",
  "botConfigured": true
}
```

### 4. Configure Telegram Webhook

Set your bot's webhook to your Vercel deployment:

```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://YOUR_DEPLOYMENT_URL/api/webhook"}'
```

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check and status |
| `/api/webhook` | POST | Telegram webhook handler |
| `/api/mcp-proxy` | POST | MCP tool execution proxy |

## Example Usage

### List Messages

```bash
curl -X POST https://YOUR_DEPLOYMENT_URL/api/mcp-proxy \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list_messages",
    "params": {
      "chat_id": "@channelname",
      "limit": 5
    }
  }'
```

### Send Message

```bash
curl -X POST https://YOUR_DEPLOYMENT_URL/api/mcp-proxy \
  -H "Content-Type: application/json" \
  -d '{
    "action": "send_message",
    "params": {
      "chat_id": "@channelname",
      "text": "Hello from Vercel!"
    }
  }'
```

## Environment Variables

Set these in your Vercel project settings:

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ Yes | Your Telegram bot token |
| `NODE_ENV` | ❌ No | Set to `production` (auto-set by Vercel) |

## Troubleshooting

### Build Fails

- Check Vercel build logs
- Ensure all dependencies are listed in `package.json`
- Verify TypeScript compiles locally: `npm run build`

### Bot Not Responding

- Verify `BOT_TOKEN` is set correctly
- Check webhook is set: `curl https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo`
- Review function logs in Vercel dashboard

### Function Timeout

- Default timeout is 30 seconds (sufficient for most operations)
- Upgrade Vercel plan for longer timeouts if needed

## Next Steps

- 📖 Read full [Deployment Guide](DEPLOYMENT.md)
- 🔧 Learn about [Build Configuration](BUILD.md)
- 🤖 Explore [Telegram Bot API](https://core.telegram.org/bots/api)
- 🔌 Learn about [MCP Protocol](https://modelcontextprotocol.io/)

## Support

For issues:
1. Check the logs in Vercel dashboard
2. Review the [full documentation](DEPLOYMENT.md)
3. Open an issue on GitHub

---

**Note**: This deployment setup is for serverless hosting. For the stdio-based MCP server, use the local installation method in the main README.
