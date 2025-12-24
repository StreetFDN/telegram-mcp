# Telegram MCP Server (User Session)

A Model Context Protocol (MCP) server that provides Telegram User Session API integration using MTProto, enabling AI assistants and applications to interact with Telegram as a regular user account through a standardized interface.

## 🎯 What's New in v2.0

**User Session Authentication** replaces Bot API! This means:
- ✅ Access **ALL** your personal messages across any chat
- ✅ Read message history from **any chat** where you're a member
- ✅ No need to add a bot or configure admin permissions
- ✅ Full access to private chats, groups, channels, and supergroups
- ✅ Direct MTProto connection for better performance and reliability

## Features

- 📨 **List Messages**: Retrieve recent messages from ANY Telegram chat you have access to
- 📜 **Chat History**: Get complete message history with pagination support
- ✉️ **Send Messages**: Send messages as your user account with formatting support
- 💬 **Reply to Messages**: Reply to specific messages in conversations
- 📋 **Get Dialogs**: List all your chats, groups, and channels
- ℹ️ **Chat Info**: Get detailed information about any chat
- 🔒 **Type-safe**: Built with TypeScript for robust type checking
- 🔐 **Secure**: Session-based authentication with persistent storage

## Prerequisites

- Node.js 18 or higher
- A Telegram account (your personal account, not a bot)
- npm or yarn

## Setup Instructions

### 1. Get Telegram API Credentials

To use the Telegram MTProto API, you need to obtain API credentials:

1. Visit [https://my.telegram.org/auth](https://my.telegram.org/auth)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application (if you haven't already):
   - **App title**: Choose any name (e.g., "My MCP Server")
   - **Short name**: Choose a short identifier (e.g., "mcp")
   - **Platform**: Select "Desktop"
   - **Description**: Optional description
5. After creating the app, you'll receive:
   - **api_id**: A numeric ID (e.g., 12345678)
   - **api_hash**: A string hash (e.g., "0123456789abcdef0123456789abcdef")

**Important**: Keep these credentials secure! Never share them or commit them to public repositories.

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/StreetFDN/telegram-mcp.git
cd telegram-mcp

# Checkout the user-session-auth branch
git checkout user-session-auth

# Install dependencies
npm install

# Build the project
npm run build
```

### 3. Configuration

Set the required environment variables:

```bash
export API_ID="your_api_id_here"
export API_HASH="your_api_hash_here"
```

Or create a `.env` file (not tracked in git):

```env
API_ID=12345678
API_HASH=0123456789abcdef0123456789abcdef
SESSION_FILE=.telegram-session
```

**Optional**: Set `SESSION_FILE` to customize where the session is stored (defaults to `.telegram-session`)

### 4. First-Time Authentication

On first run, you'll need to authenticate with your Telegram account:

```bash
npm start
```

The server will prompt you for:
1. **Phone number**: Your Telegram phone number (with country code, e.g., +1234567890)
2. **Code**: The verification code sent to your Telegram app
3. **Password**: Your 2FA password (if enabled)

After successful authentication, your session will be saved to `.telegram-session` file. Future runs will use this saved session automatically.

**Security Note**: The session file contains sensitive authentication data. Keep it secure and never share it!

### 5. Running the Server

After initial authentication:

```bash
# Start the MCP server
npm start
```

The server will run on stdio and communicate via the Model Context Protocol.

## MCP Tools

### `list_messages`

Get recent messages from any Telegram chat where you're a member.

**Parameters:**
- `chat_id` (string | number): Chat ID, username (e.g., @channelname), or phone number
- `limit` (number, optional): Number of messages to retrieve (1-100, default: 10)

**Example:**
```json
{
  "chat_id": "@mychannel",
  "limit": 20
}
```

### `get_chat_history`

Get message history with pagination support using offset_id.

**Parameters:**
- `chat_id` (string | number): Chat ID, username, or phone number
- `limit` (number, optional): Number of messages (1-100, default: 20)
- `offset_id` (number, optional): Message ID to start from (default: 0 for most recent)

**Example:**
```json
{
  "chat_id": -1001234567890,
  "limit": 50,
  "offset_id": 12345
}
```

### `send_message`

Send a new message as your user account.

**Parameters:**
- `chat_id` (string | number): Chat ID, username, or phone number
- `text` (string): Message text
- `parse_mode` (string, optional): 'Markdown', 'MarkdownV2', or 'HTML'
- `disable_notification` (boolean, optional): Send silently

**Example:**
```json
{
  "chat_id": "@mychannel",
  "text": "Hello from MCP!",
  "parse_mode": "Markdown"
}
```

### `reply_to_message`

Reply to a specific message.

**Parameters:**
- `chat_id` (string | number): Chat ID, username, or phone number
- `message_id` (number): ID of message to reply to
- `text` (string): Reply text
- `parse_mode` (string, optional): 'Markdown', 'MarkdownV2', or 'HTML'

**Example:**
```json
{
  "chat_id": -1001234567890,
  "message_id": 12345,
  "text": "Thanks for your message!"
}
```

### `get_dialogs`

Get all dialogs (chats) your account has access to.

**Parameters:**
- `limit` (number, optional): Number of dialogs to retrieve (1-200, default: 100)

**Example:**
```json
{
  "limit": 50
}
```

### `get_chat_info`

Get detailed information about a specific chat.

**Parameters:**
- `chat_id` (string | number): Chat ID, username, or phone number

**Example:**
```json
{
  "chat_id": "@mychannel"
}
```

## Usage with MCP Clients

Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "node",
      "args": ["/path/to/telegram-mcp/dist/index.js"],
      "env": {
        "API_ID": "12345678",
        "API_HASH": "0123456789abcdef0123456789abcdef"
      }
    }
  }
}
```

## Finding Chat IDs

### For Private Chats
- Use the username: `@username`
- Or use the phone number: `+1234567890`
- Or get the numeric ID from `get_dialogs` tool

### For Groups and Channels
- Use the username if available: `@channelname` or `@groupname`
- Use the numeric ID from `get_dialogs` tool
- Numeric group IDs are negative numbers (e.g., `-1001234567890`)

### Using get_dialogs
The easiest way to find chat IDs is to use the `get_dialogs` tool, which returns all your chats with their IDs and usernames.

## Advantages Over Bot API

| Feature | Bot API | User Session API |
|---------|---------|------------------|
| Access to personal messages | ❌ No | ✅ Yes |
| Read existing message history | ⚠️ Limited | ✅ Full access |
| No admin permissions needed | ❌ Required | ✅ Not needed |
| Access to all chats | ❌ Only where bot is added | ✅ All your chats |
| Message as yourself | ❌ Messages appear from bot | ✅ Messages appear from you |
| Privacy mode limitations | ⚠️ Yes | ✅ None |

## Development

```bash
# Watch mode for development
npm run dev

# Build
npm run build

# Run built version
npm start
```

## Troubleshooting

### "API_ID and API_HASH environment variables are required"
- Make sure you've set both environment variables correctly
- Check that there are no typos in the variable names
- Verify the values from https://my.telegram.org/auth

### Authentication Fails
- Ensure your phone number includes the country code (e.g., +1234567890)
- Check that you're entering the correct verification code from Telegram
- If you have 2FA enabled, make sure you're entering the correct password
- Try deleting the `.telegram-session` file and re-authenticating

### "Failed to resolve entity"
- Verify the chat ID or username is correct
- Make sure you're a member of the chat
- For usernames, include the @ symbol (e.g., @channelname)
- Try using `get_dialogs` to find the correct chat ID

### Session Expired
- Delete the `.telegram-session` file
- Restart the server and re-authenticate
- The new session will be saved automatically

### Connection Issues
- Check your internet connection
- Verify you're not behind a firewall blocking Telegram
- Try again after a few minutes (might be temporary network issues)

## Security Best Practices

1. **Never commit credentials**: Keep API_ID, API_HASH, and session files out of version control
2. **Use environment variables**: Store credentials in environment variables or secure secret management
3. **Protect session files**: The session file provides full access to your account - keep it secure
4. **Rotate credentials**: If credentials are exposed, revoke them at https://my.telegram.org/auth
5. **Use dedicated account**: Consider using a separate Telegram account for automation
6. **Monitor activity**: Regularly check your Telegram active sessions in Settings → Privacy and Security → Active Sessions

## Session Management

The session file (`.telegram-session`) contains:
- Authentication tokens
- Encryption keys
- Server connection data

**Important Notes:**
- The session file allows full access to your Telegram account
- Never share or expose this file
- The file is encrypted but should still be kept secure
- You can revoke sessions from Telegram settings if needed

To revoke a session:
1. Open Telegram on your phone
2. Go to Settings → Privacy and Security → Active Sessions
3. Find the session (named after your app title)
4. Terminate the session
5. Delete the `.telegram-session` file

## Rate Limits

Telegram's MTProto API has the following limits:
- **Messages**: ~30 messages per second per chat
- **API calls**: Generally more lenient than Bot API
- **Flood wait**: If you hit rate limits, you'll receive a flood wait error with retry time

The client handles most rate limiting automatically with retries.

## Limitations & Notes

1. **Message History**: Unlike Bot API, you have full access to message history in any chat you're a member of
2. **User Account**: Messages sent will appear as if you sent them personally
3. **Permissions**: You have the same permissions as your user account in each chat
4. **2FA**: If you have two-factor authentication enabled, you'll need to enter your password during authentication

## Migration from Bot API

If you're migrating from the Bot API version:

1. **Update dependencies**: The new version uses `telegram` instead of `node-telegram-bot-api`
2. **Get API credentials**: Follow step 1 in setup instructions
3. **Update environment variables**: Replace `BOT_TOKEN` with `API_ID` and `API_HASH`
4. **Re-authenticate**: First run will prompt for your phone number and verification code
5. **Update chat IDs**: User session can access any chat you're a member of

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT

## About MCP

The Model Context Protocol (MCP) is an open standard that enables seamless integration between AI applications and external data sources. Learn more at [modelcontextprotocol.io](https://modelcontextprotocol.io).

## Credits

Built by [Street Foundation](https://github.com/StreetFDN)

### Useful Links

- [Telegram API Documentation](https://core.telegram.org/api)
- [MTProto Protocol](https://core.telegram.org/mtproto)
- [telegram npm package](https://www.npmjs.com/package/telegram)
- [Get API Credentials](https://my.telegram.org/auth)
