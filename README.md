# Telegram MCP Server

A Model Context Protocol (MCP) server that provides Telegram Bot API integration, enabling AI assistants and applications to interact with Telegram chats through a standardized interface.

## Features

- 📨 **List Messages**: Retrieve recent messages from any Telegram chat
- 📜 **Chat History**: Get message history with pagination support
- ✉️ **Send Messages**: Send new messages to chats with formatting support
- 💬 **Reply to Messages**: Reply to specific messages in conversations
- 🔒 **Type-safe**: Built with TypeScript for robust type checking
- 🚀 **Easy Deployment**: Ready for Vercel deployment

## Prerequisites

- Node.js 18 or higher
- A Telegram account
- npm or yarn

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat and send `/newbot`
3. Follow the instructions to choose a name and username for your bot
4. Save the **Bot Token** provided by BotFather (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Configure Bot Privacy Settings

**Important**: By default, Telegram bots can only see messages that are directly sent to them. To allow your bot to read all messages in a chat:

1. In your chat with @BotFather, send `/mybots`
2. Select your bot
3. Go to **Bot Settings** → **Group Privacy**
4. Click **Turn off** (Disable Privacy Mode)

This allows the bot to receive all messages in group chats where it's added.

### 3. Add Bot to Chats

For the bot to access messages in a chat:

#### For Group Chats:
1. Add your bot to the group chat
2. **Make the bot an admin** (required for full message access):
   - Go to chat settings → Administrators
   - Add your bot as an administrator
   - You can disable all admin permissions except "Remain Anonymous" if needed

#### For Private Chats:
- Simply start a chat with your bot by clicking the link BotFather provides or searching for your bot's username

#### For Channels:
1. Add your bot to the channel
2. Make it an administrator with at least "Post Messages" permission

### 4. Get Chat IDs

To interact with a chat, you need its Chat ID:

- **Private chats**: The Chat ID is your user ID (you'll see it when you send a message to the bot)
- **Groups**: You can get the ID by:
  1. Adding the bot to the group
  2. Sending a message in the group
  3. Visiting: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
  4. Look for the `"chat":{"id":...}` field
- **Channels**: Use the channel username (e.g., `@channelname`) or get the numeric ID using the same method

### 5. Installation

```bash
# Clone the repository
git clone https://github.com/StreetFDN/telegram-mcp.git
cd telegram-mcp

# Install dependencies
npm install

# Build the project
npm run build
```

### 6. Configuration

Set the required environment variable:

```bash
export BOT_TOKEN="your_bot_token_here"
```

Or create a `.env` file (not tracked in git):

```env
BOT_TOKEN=your_bot_token_here
```

### 7. Running the Server

```bash
# Start the MCP server
npm start
```

The server will run on stdio and communicate via the Model Context Protocol.

## Vercel Deployment

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

4. Set environment variable in Vercel:
   ```bash
   vercel env add BOT_TOKEN
   ```
   Enter your bot token when prompted.

5. Redeploy to apply environment variables:
   ```bash
   vercel --prod
   ```

## MCP Tools

### `list_messages`

Get recent messages from a Telegram chat.

**Parameters:**
- `chat_id` (string | number): Chat ID or username (e.g., @channelname)
- `limit` (number, optional): Number of messages to retrieve (1-100, default: 10)

**Example:**
```json
{
  "chat_id": "@mychannel",
  "limit": 20
}
```

### `get_chat_history`

Get message history with pagination support.

**Parameters:**
- `chat_id` (string | number): Chat ID or username
- `limit` (number, optional): Number of messages (1-100, default: 20)
- `offset` (number, optional): Offset for pagination (default: 0)

**Example:**
```json
{
  "chat_id": -1001234567890,
  "limit": 50,
  "offset": 0
}
```

### `send_message`

Send a new message to a chat.

**Parameters:**
- `chat_id` (string | number): Chat ID or username
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
- `chat_id` (string | number): Chat ID or username
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

## Usage with MCP Clients

Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "node",
      "args": ["/path/to/telegram-mcp/dist/index.js"],
      "env": {
        "BOT_TOKEN": "your_bot_token_here"
      }
    }
  }
}
```

## Limitations & Important Notes

1. **Message History**: The Telegram Bot API has limitations on retrieving historical messages. The bot can only see:
   - Messages sent after the bot was added to the chat
   - Messages when privacy mode is disabled
   - Messages in chats where the bot is an admin

2. **Rate Limits**: Telegram has rate limits on API calls. Be mindful of:
   - 30 messages per second to the same chat
   - 20 messages per minute to different chats

3. **Message Retrieval**: For best message retrieval results:
   - Disable privacy mode
   - Make the bot an admin
   - Messages are cached as they arrive

4. **Webhooks vs Polling**: This implementation uses polling for message retrieval. For production use with high message volumes, consider implementing webhook support.

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

### Bot Can't See Messages
- Ensure privacy mode is disabled in @BotFather
- Make sure the bot is an admin in group chats
- Verify the bot was added after privacy mode was disabled (remove and re-add if needed)

### Invalid Token Error
- Double-check your BOT_TOKEN
- Ensure there are no extra spaces or characters
- Verify the token is active (check with @BotFather)

### Chat Not Found
- Verify the chat_id is correct
- For groups, use the numeric ID (negative number)
- For channels, use @username or numeric ID
- Ensure the bot is a member of the chat

## Security Notes

- Never commit your BOT_TOKEN to version control
- Use environment variables or secret management services
- In production, use Vercel's encrypted environment variables
- Regularly rotate your bot token if exposed

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT

## About MCP

The Model Context Protocol (MCP) is an open standard that enables seamless integration between AI applications and external data sources. Learn more at [modelcontextprotocol.io](https://modelcontextprotocol.io).

## Credits

Built by [Street Foundation](https://github.com/StreetFDN)
