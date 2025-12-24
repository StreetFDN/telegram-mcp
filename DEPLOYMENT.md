# Vercel Deployment Guide

This guide explains how to deploy the Telegram MCP Server to Vercel.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. A Telegram Bot Token (get from @BotFather on Telegram)
3. Vercel CLI installed (optional): `npm i -g vercel`

## Deployment Steps

### Option 1: Deploy via Vercel Dashboard

1. **Connect Repository**
   - Go to https://vercel.com/new
   - Import your `telegram-mcp` repository
   - Select the repository and click "Import"

2. **Configure Environment Variables**
   - In the deployment settings, add the following environment variable:
     - `BOT_TOKEN`: Your Telegram bot token
   - Click "Add" for each variable

3. **Configure Build Settings**
   - Framework Preset: Other
   - Build Command: `npm run vercel-build`
   - Output Directory: Leave empty (uses default)
   - Install Command: `npm install`

4. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete
   - Your API will be available at `https://your-project.vercel.app`

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Set Environment Variables**
   ```bash
   vercel env add BOT_TOKEN
   ```
   Enter your bot token when prompted.

4. **Deploy**
   ```bash
   vercel --prod
   ```

## Available Endpoints

Once deployed, your server will have the following endpoints:

### Health Check
```
GET https://your-project.vercel.app/api/health
```

Returns server status and configuration information.

### Webhook (for Telegram)
```
POST https://your-project.vercel.app/api/webhook
```

Receives webhook updates from Telegram.

### MCP Proxy
```
POST https://your-project.vercel.app/api/mcp-proxy
```

Proxy endpoint for MCP tool calls.

**Request Body:**
```json
{
  "action": "list_messages",
  "params": {
    "chat_id": "@channelname",
    "limit": 10
  }
}
```

## Setting Up Telegram Webhook

After deployment, configure your Telegram bot to use the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-project.vercel.app/api/webhook"}'
```

Replace:
- `<YOUR_BOT_TOKEN>` with your actual bot token
- `your-project.vercel.app` with your Vercel deployment URL

## Verifying Deployment

1. **Check Health Endpoint**
   ```bash
   curl https://your-project.vercel.app/api/health
   ```

2. **Check Logs**
   - Go to your Vercel dashboard
   - Select your project
   - Click on "Logs" tab

## Troubleshooting

### Build Failures

- Check that all dependencies are listed in `package.json`
- Verify TypeScript compilation succeeds locally
- Review build logs in Vercel dashboard

### Runtime Errors

- Verify `BOT_TOKEN` environment variable is set correctly
- Check function logs in Vercel dashboard
- Ensure bot token is valid

### Function Timeouts

- Default timeout is 30 seconds
- Increase timeout in `vercel.json` if needed:
  ```json
  "functions": {
    "api/**/*.js": {
      "maxDuration": 60
    }
  }
  ```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `NODE_ENV` | No | Environment (production/development) |

## Local Development

For local development with Vercel:

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Create `.env` file**
   ```bash
   cp .env.example .env
   ```
   Add your `BOT_TOKEN`

3. **Run Vercel dev server**
   ```bash
   vercel dev
   ```

## Production Considerations

1. **Security**
   - Never commit `.env` files
   - Use Vercel environment variables for secrets
   - Validate webhook signatures from Telegram

2. **Monitoring**
   - Enable Vercel Analytics
   - Set up alerts for function errors
   - Monitor function execution times

3. **Scaling**
   - Vercel automatically scales serverless functions
   - Monitor usage in Vercel dashboard
   - Consider upgrading plan if needed

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [MCP Documentation](https://modelcontextprotocol.io/)

## Support

For issues or questions:
- Check Vercel logs and error messages
- Review this deployment guide
- Contact Street Foundation
