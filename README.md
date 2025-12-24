# Telegram MCP Server (Python/Telethon)

A Model Context Protocol (MCP) server that provides **user-level** Telegram integration using Telethon, enabling AI assistants and applications to interact with Telegram chats through user authentication (not bot tokens).

## 🔥 Key Differences from Bot API

This implementation uses **Telethon** with **user authentication** instead of the Bot API. This means:

- ✅ Full access to all your chats, groups, and channels
- ✅ Read complete message history (not just messages after bot was added)
- ✅ No need to make bots administrators
- ✅ Access to user-only features (reactions, stories, etc.)
- ✅ Acts as your Telegram account, not a separate bot

## Features

- 🔐 **User Authentication**: Login with your phone number (one-time setup)
- 💬 **List Chats**: Get all your conversations, groups, and channels
- 📨 **Get Messages**: Retrieve message history from any chat
- ✉️ **Send Messages**: Send messages and replies as yourself
- 🔄 **Session Persistence**: Save session for future use (no repeated logins)
- 🐍 **Python/Telethon**: Built with modern Python and Telethon library
- 🚀 **MCP Protocol**: Standard Model Context Protocol interface

## Prerequisites

- Python 3.8 or higher
- A Telegram account
- Telegram API credentials (API ID and API Hash)

## Setup Instructions

### 1. Get Telegram API Credentials

1. Visit [https://my.telegram.org/auth](https://my.telegram.org/auth)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application (if you haven't already)
5. Note your **API ID** (numeric) and **API Hash** (string)

**For this implementation, we'll use:**
- API_ID: `33109274`
- API_HASH: `6ca27c49a99e2eb1e63ae2d2be770ba8`

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/StreetFDN/telegram-mcp.git
cd telegram-mcp

# Install Python dependencies
pip install -r requirements.txt
```

### 3. First-Time Authentication

The first time you run the server, you'll need to authenticate with your phone number:

```bash
# Set API credentials
export TELEGRAM_API_ID=33109274
export TELEGRAM_API_HASH="6ca27c49a99e2eb1e63ae2d2be770ba8"

# Run the server
python main.py
```

The server will start and wait for authentication. You'll need to:

1. **Use the `authenticate` tool** with your phone number
2. **Receive a verification code** via Telegram
3. **Submit the code** using the `authenticate` tool again
4. **If 2FA is enabled**, provide your password

#### Authentication Example

```json
// Step 1: Request code
{
  "name": "authenticate",
  "arguments": {
    "phone": "+1234567890"
  }
}

// Response: Code sent to your phone

// Step 2: Submit code
{
  "name": "authenticate",
  "arguments": {
    "phone": "+1234567890",
    "code": "12345"
  }
}

// Response: Success! Session string provided

// Step 3 (if 2FA enabled): Submit password
{
  "name": "authenticate",
  "arguments": {
    "phone": "+1234567890",
    "code": "12345",
    "password": "your_2fa_password"
  }
}
```

### 4. Session Persistence

After successful authentication, the server will provide a **session string**. Save this to avoid re-authenticating:

```bash
export TELEGRAM_SESSION="your_session_string_here"
```

Or add to `.env` file:

```env
TELEGRAM_API_ID=33109274
TELEGRAM_API_HASH=6ca27c49a99e2eb1e63ae2d2be770ba8
TELEGRAM_SESSION=your_session_string_here
```

### 5. Running the Server

Once authenticated:

```bash
# With environment variables set
python main.py

# Or with inline environment variables
TELEGRAM_API_ID=33109274 TELEGRAM_API_HASH="6ca27c49a99e2eb1e63ae2d2be770ba8" TELEGRAM_SESSION="your_session" python main.py
```

The server runs on stdio and communicates via the Model Context Protocol.

## MCP Tools

### `authenticate`

Authenticate with Telegram using your phone number (first-time setup).

**Parameters:**
- `phone` (string, optional): Phone number in international format (e.g., +1234567890)
- `code` (string, optional): Verification code received via Telegram
- `password` (string, optional): 2FA password if enabled

**Example:**
```json
{
  "phone": "+1234567890",
  "code": "12345"
}
```

### `list_chats`

Get a list of all your chats, groups, and channels.

**Parameters:**
- `limit` (number, optional): Maximum number of chats to retrieve (default: 20, max: 100)

**Example:**
```json
{
  "limit": 50
}
```

**Response includes:**
- Chat ID (use this for other operations)
- Chat name
- Chat type (user, group, channel)
- Unread message count
- Last message preview

### `get_messages`

Get messages from a specific chat.

**Parameters:**
- `chat_id` (number, required): Chat ID from `list_chats`
- `limit` (number, optional): Number of messages to retrieve (default: 10, max: 100)
- `offset` (number, optional): Message offset for pagination (default: 0)

**Example:**
```json
{
  "chat_id": -1001234567890,
  "limit": 50,
  "offset": 0
}
```

**Response includes:**
- Message ID
- Message text
- Sender information
- Timestamp
- Media information (if any)
- Reply information

### `send_message`

Send a message to a chat.

**Parameters:**
- `chat_id` (number, required): Chat ID where to send the message
- `text` (string, required): Message text
- `reply_to` (number, optional): Message ID to reply to

**Example:**
```json
{
  "chat_id": -1001234567890,
  "text": "Hello from MCP!",
  "reply_to": 12345
}
```

## Usage with MCP Clients

Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python",
      "args": ["/path/to/telegram-mcp/main.py"],
      "env": {
        "TELEGRAM_API_ID": "33109274",
        "TELEGRAM_API_HASH": "6ca27c49a99e2eb1e63ae2d2be770ba8",
        "TELEGRAM_SESSION": "your_session_string_here"
      }
    }
  }
}
```

## Vercel Deployment

The repository includes Vercel configuration for serverless deployment:

### Deploy to Vercel

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy:
   ```bash
   vercel
   ```

4. Set environment variables in Vercel dashboard:
   - `TELEGRAM_API_ID`: 33109274
   - `TELEGRAM_API_HASH`: 6ca27c49a99e2eb1e63ae2d2be770ba8
   - `TELEGRAM_SESSION`: Your session string

**Note:** Full MCP functionality works best when running locally via stdio. The Vercel deployment provides a basic HTTP interface for status and health checks.

## Security & Privacy

### Important Security Notes

1. **Session String is Sensitive**: Your session string gives full access to your Telegram account. Treat it like a password!
   - Never commit session strings to version control
   - Use environment variables or secret management
   - Rotate sessions if exposed (delete and re-authenticate)

2. **API Credentials**: Keep your API_ID and API_HASH private
   - Don't share in public repositories
   - Use environment variables
   - Consider using different credentials for production

3. **Phone Number Verification**: 
   - You'll receive a verification code via Telegram
   - The code is only valid for a short time
   - Never share your verification code

4. **Two-Factor Authentication (2FA)**:
   - If you have 2FA enabled, you'll need to provide your password
   - The password is only used during authentication
   - Consider using 2FA for additional account security

### Session Management

Sessions persist until:
- You log out manually
- You delete the session from another device
- Telegram invalidates the session (rare)

To revoke sessions:
1. Open Telegram app
2. Settings → Privacy and Security → Active Sessions
3. Terminate the MCP server session

## Limitations & Notes

1. **Rate Limits**: Telegram has rate limits to prevent spam:
   - ~30 messages per second to the same chat
   - Flood wait errors if exceeded (automatic backoff implemented)

2. **Message History**: Unlike Bot API, user accounts have full access to chat history

3. **User Restrictions**: Some operations may be restricted based on:
   - Chat privacy settings
   - User permissions in groups
   - Telegram's spam prevention

4. **Account Safety**: 
   - Use responsibly to avoid account restrictions
   - Don't use for spam or automated mass messaging
   - Follow Telegram's Terms of Service

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development
python main.py

# Test authentication flow
python -c "import asyncio; from telegram_client import TelegramUserClient; asyncio.run(TelegramUserClient(33109274, '6ca27c49a99e2eb1e63ae2d2be770ba8').start())"
```

## Troubleshooting

### Authentication Fails
- Verify API_ID and API_HASH are correct
- Check phone number format (must include country code: +1234567890)
- Ensure you have network connectivity to Telegram servers
- Try requesting a new verification code

### Session Expired
- Delete TELEGRAM_SESSION and re-authenticate
- Check active sessions in Telegram app
- Ensure session string wasn't corrupted

### Can't Access Certain Chats
- Verify you're actually a member of the chat
- Check if the chat has privacy restrictions
- For channels, ensure they're not private

### Import Errors
- Install all requirements: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.8+)
- Try upgrading pip: `pip install --upgrade pip`

### Connection Issues
- Check firewall settings
- Verify internet connectivity
- Telegram may be blocked in some regions (consider VPN)

## File Structure

```
telegram-mcp/
├── main.py                 # MCP server implementation
├── telegram_client.py      # Telethon client wrapper
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel deployment config
├── api/
│   └── index.py           # Vercel serverless function
└── README.md              # This file
```

## Migration from TypeScript Version

If you're migrating from the TypeScript/Bot API version:

**Key Changes:**
1. No more BOT_TOKEN - use user authentication instead
2. Requires phone number verification on first use
3. Session persistence via TELEGRAM_SESSION env variable
4. Full message history access (not limited to post-bot messages)
5. Python instead of Node.js/TypeScript

**Migration Steps:**
1. Get Telegram API credentials from my.telegram.org
2. Install Python dependencies
3. Authenticate with your phone number
4. Save session string to environment
5. Update MCP client configuration to use Python command

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Guidelines
- Follow PEP 8 style guide
- Add type hints to functions
- Include docstrings for public methods
- Test authentication flow before submitting

## License

MIT

## About

### Telethon
[Telethon](https://docs.telethon.dev/) is a modern Python library for interacting with Telegram's API using user accounts.

### Model Context Protocol (MCP)
The Model Context Protocol is an open standard that enables seamless integration between AI applications and external data sources. Learn more at [modelcontextprotocol.io](https://modelcontextprotocol.io).

## Credits

Built by [Street Foundation](https://github.com/StreetFDN)

## Changelog

### v2.0.0 (Python/Telethon Migration)
- 🔄 Migrated from TypeScript/Bot API to Python/Telethon
- 🔐 User authentication with session persistence
- 📱 Phone number verification flow
- 💬 Full message history access
- 🎯 Simplified MCP tools (list_chats, get_messages, send_message)
- 🐍 Modern Python implementation with type hints

### v1.0.0 (Original TypeScript)
- Bot API implementation
- Basic message operations
- TypeScript/Node.js runtime
