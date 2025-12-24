# Local Development Guide

This guide helps you develop and test the Telegram MCP Server locally, including testing Vercel serverless functions.

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/StreetFDN/telegram-mcp.git
cd telegram-mcp
npm install
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your Telegram bot token:

```env
BOT_TOKEN=your_actual_bot_token_here
NODE_ENV=development
```

## Development Modes

### Mode 1: MCP Server (stdio)

For local MCP protocol development:

```bash
# Build TypeScript
npm run build:app

# Run the server
npm start
```

This starts the MCP server listening on stdio. You can connect to it from MCP clients like Claude Desktop.

### Mode 2: Vercel Serverless Functions (Local)

For testing API endpoints locally with Vercel:

```bash
# Install Vercel CLI globally
npm install -g vercel

# Build everything
npm run build

# Run Vercel dev server
vercel dev
```

This starts a local server at `http://localhost:3000` with all API endpoints available:

- `http://localhost:3000/api/health` - Health check
- `http://localhost:3000/api/webhook` - Telegram webhook
- `http://localhost:3000/api/mcp-proxy` - MCP proxy

## Testing API Endpoints Locally

### Health Check

```bash
curl http://localhost:3000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "telegram-mcp-server",
  "version": "1.0.0",
  "timestamp": "2024-12-24T21:00:00.000Z",
  "environment": "development",
  "botConfigured": true
}
```

### MCP Proxy - List Messages

```bash
curl -X POST http://localhost:3000/api/mcp-proxy \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list_messages",
    "params": {
      "chat_id": "YOUR_CHAT_ID",
      "limit": 5
    }
  }'
```

### MCP Proxy - Send Message

```bash
curl -X POST http://localhost:3000/api/mcp-proxy \
  -H "Content-Type: application/json" \
  -d '{
    "action": "send_message",
    "params": {
      "chat_id": "YOUR_CHAT_ID",
      "text": "Hello from local development!"
    }
  }'
```

## Watch Mode

For continuous development with auto-rebuild:

```bash
# Terminal 1: Watch and rebuild TypeScript
npm run dev

# Terminal 2: Run Vercel dev server
vercel dev
```

Changes to `src/api/*.ts` will be automatically recompiled.

## Testing with Real Telegram Webhook

To test webhook locally, you need to expose your local server to the internet. Use one of these tools:

### Option 1: ngrok

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Start ngrok
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Set Telegram webhook
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://abc123.ngrok.io/api/webhook"}'
```

### Option 2: Cloudflare Tunnel

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared  # macOS

# Create tunnel
cloudflared tunnel --url http://localhost:3000
```

### Option 3: VS Code Port Forwarding

If using GitHub Codespaces or VS Code Remote:

1. Open Ports tab
2. Forward port 3000
3. Make it public
4. Use the forwarded URL for webhook

## Debugging

### Enable Debug Logging

Add to your `.env`:

```env
DEBUG=*
LOG_LEVEL=debug
```

### Inspect Telegram Updates

To see raw webhook updates:

```bash
# Check webhook info
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo

# Get updates manually (if webhook not set)
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

### TypeScript Errors

Check TypeScript compilation:

```bash
npx tsc --noEmit
```

### Test Build Process

Test the full build as Vercel would run it:

```bash
# Clean previous builds
rm -rf dist/ api/

# Run Vercel build
npm run vercel-build

# Verify outputs
ls -la dist/
ls -la api/
```

## Common Development Tasks

### Add a New API Endpoint

1. Create file in `src/api/`:
   ```typescript
   // src/api/my-endpoint.ts
   import type { VercelRequest, VercelResponse } from '@vercel/node';
   
   export default async function handler(
     req: VercelRequest,
     res: VercelResponse
   ) {
     res.status(200).json({ message: 'Hello!' });
   }
   ```

2. Build:
   ```bash
   npm run build:api
   ```

3. Test:
   ```bash
   curl http://localhost:3000/api/my-endpoint
   ```

### Add a New MCP Tool

1. Edit `src/index.ts`:
   - Add tool to `ListToolsRequestSchema` handler
   - Add case in `CallToolRequestSchema` handler

2. Rebuild and test:
   ```bash
   npm run build:app
   npm start
   ```

### Update Dependencies

```bash
# Check for updates
npm outdated

# Update specific package
npm update package-name

# Update all
npm update

# Rebuild
npm run build
```

## Troubleshooting

### "Cannot find module" errors

Ensure imports use `.js` extension for ES modules:

```typescript
import { TelegramClient } from './telegram.js'; // ✓ Correct
import { TelegramClient } from './telegram';    // ✗ Wrong
```

### Port already in use

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>
```

### Vercel CLI issues

```bash
# Reinstall Vercel CLI
npm uninstall -g vercel
npm install -g vercel

# Clear Vercel cache
vercel --debug
```

### TypeScript path issues

Ensure `tsconfig.json` and `tsconfig.api.json` have correct paths:

```json
{
  "compilerOptions": {
    "rootDir": "./src",
    "outDir": "./dist"
  }
}
```

## Project Structure

```
telegram-mcp/
├── src/
│   ├── index.ts          # MCP server (stdio)
│   ├── telegram.ts       # Telegram client library
│   └── api/              # Serverless functions
│       ├── health.ts     # GET /api/health
│       ├── webhook.ts    # POST /api/webhook
│       └── mcp-proxy.ts  # POST /api/mcp-proxy
├── dist/                 # Built MCP server
├── api/                  # Built serverless functions
├── .env                  # Local environment variables (gitignored)
├── .env.example          # Environment template
├── vercel.json           # Vercel configuration
├── tsconfig.json         # Main TypeScript config
└── tsconfig.api.json     # API TypeScript config
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | - | Telegram bot token |
| `NODE_ENV` | No | `development` | Environment |
| `DEBUG` | No | - | Debug logging |
| `LOG_LEVEL` | No | `info` | Logging level |

## Useful Commands

```bash
# Clean build
npm run build

# Clean everything
rm -rf dist/ api/ node_modules/
npm install
npm run build

# Check types
npx tsc --noEmit

# Run tests (if added)
npm test

# Format code (if prettier configured)
npm run format

# Lint code (if eslint configured)
npm run lint
```

## Next Steps

- Set up tests with Jest or Vitest
- Add more MCP tools
- Implement webhook authentication
- Add rate limiting
- Set up error tracking (e.g., Sentry)
- Add logging service (e.g., Datadog, LogRocket)

## Resources

- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [MCP SDK Documentation](https://modelcontextprotocol.io/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)

## Getting Help

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Check [BUILD.md](BUILD.md) for build issues
- Review Vercel logs: `vercel logs`
- Enable debug mode: `DEBUG=* vercel dev`

---

Happy coding! 🚀
