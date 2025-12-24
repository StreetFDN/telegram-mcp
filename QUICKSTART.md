# Quick Start Guide

Get your Telegram MCP Server running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- A Telegram account
- Terminal/Command Line access

## Step 1: Installation (1 minute)

```bash
# Clone the repository
git clone https://github.com/StreetFDN/telegram-mcp.git
cd telegram-mcp

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure (30 seconds)

Copy the example environment file:

```bash
cp .env.example .env
```

The default credentials are already set:
- API_ID: 33109274
- API_HASH: 6ca27c49a99e2eb1e63ae2d2be770ba8

## Step 3: First Run & Authentication (2 minutes)

Start the server:

```bash
python main.py
```

### Authenticate via MCP Tool

When you use the MCP server with your client, call the `authenticate` tool:

**Step 1 - Request verification code:**
```json
{
  "name": "authenticate",
  "arguments": {
    "phone": "+1234567890"
  }
}
```

You'll receive: "📱 Verification code sent to your phone"

**Step 2 - Submit the code:**
```json
{
  "name": "authenticate",
  "arguments": {
    "phone": "+1234567890",
    "code": "12345"
  }
}
```

Success! You'll get a session string.

**Step 3 - Save session (optional but recommended):**

Copy the session string from the response and add it to your `.env` file:

```env
TELEGRAM_SESSION=your_session_string_here
```

This way you won't need to authenticate again!

## Step 4: Use the Tools (1 minute)

### List Your Chats

```json
{
  "name": "list_chats",
  "arguments": {
    "limit": 10
  }
}
```

### Get Messages from a Chat

```json
{
  "name": "get_messages",
  "arguments": {
    "chat_id": -1001234567890,
    "limit": 20
  }
}
```

### Send a Message

```json
{
  "name": "send_message",
  "arguments": {
    "chat_id": -1001234567890,
    "text": "Hello from MCP!"
  }
}
```

## That's It! 🎉

You now have a fully functional Telegram MCP Server with user authentication.

## MCP Client Configuration

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python",
      "args": ["/absolute/path/to/telegram-mcp/main.py"],
      "env": {
        "TELEGRAM_API_ID": "33109274",
        "TELEGRAM_API_HASH": "6ca27c49a99e2eb1e63ae2d2be770ba8",
        "TELEGRAM_SESSION": "your_session_string_here"
      }
    }
  }
}
```

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Authentication fails
- Check phone number format: +1234567890 (with country code)
- Make sure you entered the correct verification code
- Request a new code if it expired

### Can't access certain chats
- Ensure you're a member of that chat
- The chat_id must be correct (get it from list_chats)

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Check out the [Telethon docs](https://docs.telethon.dev/) for advanced usage
- Learn about [MCP Protocol](https://modelcontextprotocol.io)

## Need Help?

- Open an issue on GitHub
- Check existing issues for solutions
- Read the troubleshooting section in README.md

Happy messaging! 📱✨
