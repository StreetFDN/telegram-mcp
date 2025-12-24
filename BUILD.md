# Build Configuration

This document explains the build setup for the Telegram MCP Server.

## Build Process

The project uses TypeScript and has two separate build targets:

### 1. Application Build (`build:app`)

Builds the main MCP server for local/stdio usage:
- **Input**: `src/index.ts`, `src/telegram.ts`
- **Output**: `dist/` directory
- **Config**: `tsconfig.json`
- **Usage**: Local MCP server via stdio transport

### 2. API Build (`build:api`)

Builds serverless functions for Vercel:
- **Input**: `src/api/*.ts`
- **Output**: `api/` directory
- **Config**: `tsconfig.api.json`
- **Usage**: Vercel serverless functions

## Build Scripts

```bash
# Build everything
npm run build

# Build only the main application
npm run build:app

# Build only the API functions
npm run build:api

# Development mode with watch
npm run dev

# Vercel build (used by Vercel)
npm run vercel-build
```

## TypeScript Configuration

### Main Config (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "outDir": "./dist",
    "rootDir": "./src"
  }
}
```

### API Config (`tsconfig.api.json`)

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./api",
    "rootDir": "./src/api",
    "module": "ES2022"
  }
}
```

## Directory Structure

```
telegram-mcp/
├── src/
│   ├── index.ts          # Main MCP server
│   ├── telegram.ts       # Telegram client
│   └── api/              # Serverless functions
│       ├── health.ts     # Health check endpoint
│       ├── webhook.ts    # Telegram webhook handler
│       └── mcp-proxy.ts  # MCP proxy endpoint
├── dist/                 # Built application files
├── api/                  # Built serverless functions
├── tsconfig.json         # Main TS config
├── tsconfig.api.json     # API TS config
└── vercel.json          # Vercel configuration
```

## Build Outputs

### Application Output (`dist/`)

- `dist/index.js` - Main MCP server entry point
- `dist/telegram.js` - Telegram client implementation
- `dist/*.d.ts` - TypeScript declarations
- `dist/*.map` - Source maps

### API Output (`api/`)

- `api/health.js` - Health check function
- `api/webhook.js` - Webhook handler function
- `api/mcp-proxy.js` - MCP proxy function
- `api/*.d.ts` - TypeScript declarations
- `api/*.map` - Source maps

## Vercel Build Process

1. **Install**: `npm install`
2. **Build**: `npm run vercel-build`
   - Runs `build:app` (compiles to `dist/`)
   - Runs `build:api` (compiles to `api/`)
3. **Deploy**: Vercel deploys `api/` directory as serverless functions

## Build Verification

After building, verify outputs:

```bash
# Check application build
ls -la dist/

# Check API build
ls -la api/

# Test application locally
node dist/index.js
```

## Common Build Issues

### Issue: "Cannot find module"

**Solution**: Ensure all imports use `.js` extensions for ES modules:
```typescript
import { TelegramClient } from './telegram.js'; // ✓ Correct
import { TelegramClient } from './telegram';    // ✗ Wrong
```

### Issue: "dist directory not found"

**Solution**: Run the build command:
```bash
npm run build
```

### Issue: Vercel build fails

**Solutions**:
1. Check that `vercel.json` has correct `buildCommand`
2. Verify all dependencies are in `dependencies` (not `devDependencies`)
3. Review Vercel build logs for specific errors

## Clean Build

To perform a clean build:

```bash
# Remove build outputs
rm -rf dist/ api/

# Remove node_modules
rm -rf node_modules/

# Reinstall and rebuild
npm install
npm run build
```

## CI/CD

The project includes GitHub Actions workflow (`.github/workflows/build.yml`) that:

- Runs on push to main branch
- Tests with Node.js 18.x and 20.x
- Validates both builds succeed
- Checks TypeScript compilation

## Dependencies

### Runtime Dependencies

- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `@vercel/node` - Vercel serverless function types
- `node-telegram-bot-api` - Telegram Bot API client
- `zod` - Schema validation

### Development Dependencies

- `typescript` - TypeScript compiler
- `@types/node` - Node.js type definitions
- `@types/node-telegram-bot-api` - Telegram types

## Environment Variables

Required for runtime (not build):
- `BOT_TOKEN` - Telegram bot token
- `NODE_ENV` - Environment identifier

## Further Reading

- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vercel Build Configuration](https://vercel.com/docs/build-step)
- [ES Modules in Node.js](https://nodejs.org/api/esm.html)
