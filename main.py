"""
Telegram MCP Server using Telethon for user authentication.
Provides tools for listing chats, getting messages, and sending messages.
"""

import os
import asyncio
import logging
from typing import Any, Dict, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, EmbeddedResource
from telegram_client import TelegramUserClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = int(os.getenv('TELEGRAM_API_ID', '33109274'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '6ca27c49a99e2eb1e63ae2d2be770ba8')
TELEGRAM_SESSION = os.getenv('TELEGRAM_SESSION', '')

# Global Telegram client
telegram_client: Optional[TelegramUserClient] = None


async def initialize_telegram_client() -> TelegramUserClient:
    """Initialize and return the Telegram client."""
    global telegram_client
    
    if telegram_client is None:
        telegram_client = TelegramUserClient(
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=TELEGRAM_SESSION
        )
        
        # Try to authenticate with existing session
        result = await telegram_client.start()
        
        if result['status'] == 'authenticated':
            logger.info(f"Authenticated as: {result['user'].get('first_name', 'User')}")
            # Save session for future use
            if not TELEGRAM_SESSION:
                session = telegram_client.get_session_string()
                logger.info(f"Save this session string to TELEGRAM_SESSION environment variable:")
                logger.info(f"TELEGRAM_SESSION={session}")
        else:
            logger.warning(f"Authentication status: {result['status']}")
            logger.warning(f"Message: {result.get('message', 'Unknown')}")
    
    return telegram_client


async def authenticate_user(phone: Optional[str] = None, 
                           code: Optional[str] = None,
                           password: Optional[str] = None) -> Dict[str, Any]:
    """
    Authenticate user with phone number and verification code.
    
    Args:
        phone: Phone number (international format, e.g., +1234567890)
        code: Verification code sent to phone
        password: 2FA password if enabled
        
    Returns:
        Authentication result dictionary
    """
    global telegram_client
    
    if telegram_client is None:
        telegram_client = TelegramUserClient(
            api_id=API_ID,
            api_hash=API_HASH
        )
    
    result = await telegram_client.start(phone=phone, code=code, password=password)
    
    if result['status'] == 'authenticated':
        session = telegram_client.get_session_string()
        logger.info(f"Authentication successful! Save this session:")
        logger.info(f"TELEGRAM_SESSION={session}")
        result['session_string'] = session
    
    return result


# Create MCP server
app = Server("telegram-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="authenticate",
            description="Authenticate with Telegram using phone number. Multi-step process: 1) Provide phone to receive code, 2) Provide code to authenticate, 3) Optionally provide password if 2FA enabled.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number in international format (e.g., +1234567890). Required for first-time setup."
                    },
                    "code": {
                        "type": "string",
                        "description": "Verification code sent to your phone (e.g., 12345)"
                    },
                    "password": {
                        "type": "string",
                        "description": "Two-factor authentication password (if enabled)"
                    }
                }
            }
        ),
        Tool(
            name="list_chats",
            description="Get a list of user's chats, groups, and channels with recent message information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of chats to retrieve (default: 20, max: 100)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="get_messages",
            description="Get messages from a specific chat, group, or channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "number",
                        "description": "Chat ID (can be obtained from list_chats)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of messages to retrieve (default: 10, max: 100)",
                        "default": 10
                    },
                    "offset": {
                        "type": "number",
                        "description": "Message offset for pagination (default: 0)",
                        "default": 0
                    }
                },
                "required": ["chat_id"]
            }
        ),
        Tool(
            name="send_message",
            description="Send a message to a specific chat, group, or channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "number",
                        "description": "Chat ID where to send the message"
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text to send"
                    },
                    "reply_to": {
                        "type": "number",
                        "description": "Optional: Message ID to reply to"
                    }
                },
                "required": ["chat_id", "text"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "authenticate":
            # Handle authentication
            phone = arguments.get("phone")
            code = arguments.get("code")
            password = arguments.get("password")
            
            result = await authenticate_user(phone=phone, code=code, password=password)
            
            if result['status'] == 'authenticated':
                user = result['user']
                response = (
                    f"✅ Successfully authenticated!\n\n"
                    f"User: {user['first_name']} {user.get('last_name', '')}\n"
                    f"Username: @{user.get('username', 'N/A')}\n"
                    f"Phone: {user.get('phone', 'N/A')}\n\n"
                    f"Session saved. You can now use other tools.\n\n"
                    f"💡 Save this session string to avoid re-authenticating:\n"
                    f"TELEGRAM_SESSION={result.get('session_string', 'N/A')}"
                )
            elif result['status'] == 'needs_code':
                response = (
                    f"📱 Verification code sent to your phone.\n\n"
                    f"Please call this tool again with the code:\n"
                    f'{{"phone": "{phone}", "code": "YOUR_CODE"}}'
                )
            elif result['status'] == 'needs_password':
                response = (
                    f"🔐 Two-factor authentication enabled.\n\n"
                    f"Please call this tool again with your 2FA password:\n"
                    f'{{"phone": "{phone}", "code": "{code}", "password": "YOUR_PASSWORD"}}'
                )
            else:
                response = f"❌ Authentication failed: {result.get('message', 'Unknown error')}"
            
            return [TextContent(type="text", text=response)]
        
        # Ensure client is initialized for other tools
        client = await initialize_telegram_client()
        
        if name == "list_chats":
            limit = arguments.get("limit", 20)
            chats = await client.get_chats(limit=min(limit, 100))
            
            response = f"📱 Found {len(chats)} chats:\n\n"
            for chat in chats:
                response += f"• {chat['name']} (ID: {chat['id']})\n"
                response += f"  Type: {chat['type']}, Unread: {chat['unread_count']}\n"
                if chat['last_message']:
                    msg = chat['last_message']
                    text_preview = msg['text'][:50] + "..." if len(msg['text']) > 50 else msg['text']
                    response += f"  Last: {text_preview}\n"
                response += "\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "get_messages":
            chat_id = arguments["chat_id"]
            limit = arguments.get("limit", 10)
            offset = arguments.get("offset", 0)
            
            messages = await client.get_messages(
                chat_id=chat_id,
                limit=min(limit, 100),
                offset=offset
            )
            
            response = f"💬 Retrieved {len(messages)} messages from chat {chat_id}:\n\n"
            for msg in messages:
                from_name = msg.get('from_name', 'Unknown')
                response += f"[{msg['date']}] {from_name}:\n"
                response += f"{msg['text']}\n"
                if msg.get('media'):
                    response += f"📎 Media: {msg['media']['type']}\n"
                response += "\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "send_message":
            chat_id = arguments["chat_id"]
            text = arguments["text"]
            reply_to = arguments.get("reply_to")
            
            result = await client.send_message(
                chat_id=chat_id,
                text=text,
                reply_to=reply_to
            )
            
            response = (
                f"✅ Message sent successfully!\n\n"
                f"Message ID: {result['id']}\n"
                f"Chat ID: {result['chat_id']}\n"
                f"Date: {result['date']}"
            )
            
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Telegram MCP Server with Telethon...")
    logger.info(f"API ID: {API_ID}")
    logger.info(f"Session available: {bool(TELEGRAM_SESSION)}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
