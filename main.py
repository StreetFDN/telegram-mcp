"""
Telegram MCP Server using Telethon for user authentication.
Provides tools for listing chats, getting messages, and sending messages.
Supports both stdio (MCP) and SSE (HTTP) interfaces.
"""

import os
import sys
import asyncio
import logging
from typing import Any, Dict, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, EmbeddedResource
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    FloodWaitError
)
from telegram_client import TelegramUserClient

# Import for SSE server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate and load Telegram API credentials with proper error handling
def get_api_credentials():
    """Load and validate Telegram API credentials from environment variables."""
    api_id_str = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    # Check for missing environment variables
    if not api_id_str:
        print("❌ Environment Variable Missing: TELEGRAM_API_ID is not set")
        print("Please set TELEGRAM_API_ID environment variable with your Telegram API ID")
        print("Get your credentials at: https://my.telegram.org/apps")
        sys.exit(1)
    
    if not api_hash:
        print("❌ Environment Variable Missing: TELEGRAM_API_HASH is not set")
        print("Please set TELEGRAM_API_HASH environment variable with your Telegram API Hash")
        print("Get your credentials at: https://my.telegram.org/apps")
        sys.exit(1)
    
    # Validate API ID is a valid integer
    try:
        api_id = int(api_id_str)
    except ValueError:
        print(f"❌ Invalid TELEGRAM_API_ID: '{api_id_str}' is not a valid integer")
        print("TELEGRAM_API_ID must be a numeric value")
        sys.exit(1)
    
    return api_id, api_hash

# Load credentials
API_ID, API_HASH = get_api_credentials()
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


# Create MCP server
app = Server("telegram-mcp")


async def authenticate(
    phone_number: Optional[str] = None,
    verification_code: Optional[str] = None,
    two_factor_password: Optional[str] = None
) -> str:
    """
    Authenticate with Telegram using phone number and verification code.
    
    This is a multi-step authentication process:
    1. Call with phone_number only to receive a verification code
    2. Call with phone_number and verification_code to sign in
    3. If 2FA is enabled, call with all three parameters including two_factor_password
    
    Args:
        phone_number: Phone number in international format (e.g., +1234567890)
        verification_code: Verification code received via SMS/Telegram (optional)
        two_factor_password: Two-factor authentication password if enabled (optional)
    
    Returns:
        Authentication status message with next steps or session information
    """
    global telegram_client
    
    logger.info(f"🔐 [AUTHENTICATE] Starting authentication process")
    logger.info(f"📱 [AUTHENTICATE] Phone provided: {bool(phone_number)}")
    logger.info(f"🔢 [AUTHENTICATE] Code provided: {bool(verification_code)}")
    logger.info(f"🔑 [AUTHENTICATE] Password provided: {bool(two_factor_password)}")
    
    try:
        # Initialize client if not already done
        if telegram_client is None:
            logger.info(f"📲 [AUTHENTICATE] Initializing new Telegram client")
            logger.info(f"📲 [AUTHENTICATE] API ID: {API_ID}")
            logger.info(f"📲 [AUTHENTICATE] API Hash: {'*' * len(API_HASH) if API_HASH else 'NOT SET'}")
            
            telegram_client = TelegramUserClient(
                api_id=API_ID,
                api_hash=API_HASH
            )
        
        # Step 1: Only phone_number provided - send verification code
        if phone_number and not verification_code:
            logger.info(f"📤 [AUTHENTICATE] Step 1: Sending verification code to {phone_number}")
            
            try:
                await telegram_client.client.connect()
                logger.info(f"✅ [AUTHENTICATE] Connected to Telegram servers")
                
                await telegram_client.client.send_code_request(phone_number)
                logger.info(f"✅ [AUTHENTICATE] Code sent successfully to {phone_number}")
                
                return (
                    f"✅ **Code Sent Successfully**\\n\\n"
                    f"📱 A verification code has been sent to **{phone_number}**\\n\\n"
                    f"**Next Step:**\\n"
                    f"Call authenticate again with both phone_number and verification_code:\\n"
                    f'```\\n{{\"phone_number\": \"{phone_number}\", \"verification_code\": \"YOUR_CODE\"}}\\n```\\n\\n'
                    f"💡 The code is usually 5 digits and arrives within seconds."
                )
                
            except ApiIdInvalidError as e:
                logger.error(f"❌ [AUTHENTICATE] Invalid API credentials: {e}")
                return (
                    f"❌ **Invalid API Credentials**\\n\\n"
                    f"The TELEGRAM_API_ID or TELEGRAM_API_HASH environment variables are invalid.\\n"
                    f"Please check your Telegram API credentials at https://my.telegram.org/apps\\n\\n"
                    f"Error: {str(e)}"
                )
                
            except PhoneNumberInvalidError as e:
                logger.error(f"❌ [AUTHENTICATE] Invalid phone number: {e}")
                return (
                    f"❌ **Invalid Phone Number**\\n\\n"
                    f"The phone number **{phone_number}** is not valid.\\n"
                    f"Please use international format (e.g., +1234567890)\\n\\n"
                    f"Error: {str(e)}"
                )
                
            except FloodWaitError as e:
                logger.error(f"❌ [AUTHENTICATE] Rate limited: {e}")
                return (
                    f"❌ **Rate Limited**\\n\\n"
                    f"Too many attempts. Please wait {e.seconds} seconds before trying again.\\n\\n"
                    f"Error: {str(e)}"
                )
        
        # Step 2: Phone and code provided - attempt sign in
        elif phone_number and verification_code:
            logger.info(f"🔐 [AUTHENTICATE] Step 2: Attempting sign in with code")
            
            try:
                await telegram_client.client.connect()
                logger.info(f"✅ [AUTHENTICATE] Connected to Telegram servers")
                
                # Try to sign in with the code
                try:
                    logger.info(f"🔑 [AUTHENTICATE] Signing in with verification code")
                    await telegram_client.client.sign_in(phone_number, verification_code)
                    logger.info(f"✅ [AUTHENTICATE] Sign in successful!")
                    
                    # Get user info
                    me = await telegram_client.client.get_me()
                    telegram_client._is_authenticated = True
                    
                    # Get session string
                    session_string = telegram_client.get_session_string()
                    
                    logger.info(f"✅ [AUTHENTICATE] Authenticated as: {me.first_name} (@{me.username})")
                    logger.info(f"💾 [AUTHENTICATE] Session string generated (length: {len(session_string)})")
                    
                    return (
                        f"✅ **Authentication Successful!**\\n\\n"
                        f"👤 **User Information:**\\n"
                        f"   • Name: {me.first_name} {me.last_name or ''}\\n"
                        f"   • Username: @{me.username or 'N/A'}\\n"
                        f"   • Phone: {me.phone or 'N/A'}\\n"
                        f"   • User ID: {me.id}\\n\\n"
                        f"🎉 You can now use other Telegram tools!\\n\\n"
                        f"💾 **Save this session string** to avoid re-authenticating:\\n"
                        f"```\\n"
                        f"TELEGRAM_SESSION={session_string}\\n"
                        f"```\\n\\n"
                        f"Add this to your environment variables for persistent authentication."
                    )
                    
                except SessionPasswordNeededError:
                    logger.warning(f"🔐 [AUTHENTICATE] Two-factor authentication required")
                    
                    # Step 3: 2FA is enabled, need password
                    if not two_factor_password:
                        logger.info(f"⚠️ [AUTHENTICATE] Password not provided, requesting from user")
                        return (
                            f"🔐 **Two-Factor Authentication Required**\\n\\n"
                            f"Your account has 2FA enabled. Please provide your password.\\n\\n"
                            f"**Next Step:**\\n"
                            f"Call authenticate again with all three parameters:\\n"
                            f'```\\n{{\"phone_number\": \"{phone_number}\", \"verification_code\": \"{verification_code}\", \"two_factor_password\": \"YOUR_PASSWORD\"}}\\n```\\n\\n'
                            f"💡 This is the password you set in Telegram Settings > Privacy and Security > Two-Step Verification"
                        )
                    
                    # Try to sign in with password
                    logger.info(f"🔑 [AUTHENTICATE] Attempting 2FA sign in")
                    try:
                        await telegram_client.client.sign_in(password=two_factor_password)
                        logger.info(f"✅ [AUTHENTICATE] 2FA sign in successful!")
                        
                        # Get user info
                        me = await telegram_client.client.get_me()
                        telegram_client._is_authenticated = True
                        
                        # Get session string
                        session_string = telegram_client.get_session_string()
                        
                        logger.info(f"✅ [AUTHENTICATE] Authenticated as: {me.first_name} (@{me.username})")
                        logger.info(f"💾 [AUTHENTICATE] Session string generated (length: {len(session_string)})")
                        
                        return (
                            f"✅ **Authentication Successful! (2FA)**\\n\\n"
                            f"👤 **User Information:**\\n"
                            f"   • Name: {me.first_name} {me.last_name or ''}\\n"
                            f"   • Username: @{me.username or 'N/A'}\\n"
                            f"   • Phone: {me.phone or 'N/A'}\\n"
                            f"   • User ID: {me.id}\\n\\n"
                            f"🎉 You can now use other Telegram tools!\\n\\n"
                            f"💾 **Save this session string** to avoid re-authenticating:\\n"
                            f"```\\n"
                            f"TELEGRAM_SESSION={session_string}\\n"
                            f"```\\n\\n"
                            f"Add this to your environment variables for persistent authentication."
                        )
                        
                    except PasswordHashInvalidError as e:
                        logger.error(f"❌ [AUTHENTICATE] Invalid 2FA password: {e}")
                        return (
                            f"❌ **Invalid Password**\\n\\n"
                            f"The two-factor authentication password is incorrect.\\n"
                            f"Please try again with the correct password.\\n\\n"
                            f"Error: {str(e)}"
                        )
                
            except PhoneCodeInvalidError as e:
                logger.error(f"❌ [AUTHENTICATE] Invalid verification code: {e}")
                return (
                    f"❌ **Invalid Verification Code**\\n\\n"
                    f"The code **{verification_code}** is incorrect.\\n"
                    f"Please check the code and try again.\\n\\n"
                    f"Error: {str(e)}"
                )
                
            except PhoneCodeExpiredError as e:
                logger.error(f"❌ [AUTHENTICATE] Verification code expired: {e}")
                return (
                    f"❌ **Verification Code Expired**\\n\\n"
                    f"The code has expired. Please request a new code by calling authenticate with just your phone_number.\\n\\n"
                    f"Error: {str(e)}"
                )
                
            except FloodWaitError as e:
                logger.error(f"❌ [AUTHENTICATE] Rate limited: {e}")
                return (
                    f"❌ **Rate Limited**\\n\\n"
                    f"Too many attempts. Please wait {e.seconds} seconds before trying again.\\n\\n"
                    f"Error: {str(e)}"
                )
        
        else:
            logger.warning(f"⚠️ [AUTHENTICATE] Invalid parameters provided")
            return (
                f"⚠️ **Invalid Parameters**\\n\\n"
                f"Please provide at least a phone_number to start authentication.\\n\\n"
                f"**Usage:**\\n"
                f"1. Send code: `{{\\\"phone_number\\\": \\\"+1234567890\\\"}}`\\n"
                f"2. Verify: `{{\\\"phone_number\\\": \\\"+1234567890\\\", \\\"verification_code\\\": \\\"12345\\\"}}`\\n"
                f"3. 2FA (if needed): `{{\\\"phone_number\\\": \\\"+1234567890\\\", \\\"verification_code\\\": \\\"12345\\\", \\\"two_factor_password\\\": \\\"password\\\"}}`"
            )
    
    except Exception as e:
        logger.error(f"❌ [AUTHENTICATE] Unexpected error: {e}", exc_info=True)
        return (
            f"❌ **Authentication Error**\\n\\n"
            f"An unexpected error occurred during authentication:\\n"
            f"```\\n{str(e)}\\n```\\n\\n"
            f"Please check the logs for more details."
        )


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
                    "phone_number": {
                        "type": "string",
                        "description": "Phone number in international format (e.g., +1234567890). Required for first-time setup."
                    },
                    "verification_code": {
                        "type": "string",
                        "description": "Verification code sent to your phone (e.g., 12345)"
                    },
                    "two_factor_password": {
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
            # Call the authenticate function directly
            phone = arguments.get("phone_number") or arguments.get("phone")
            code = arguments.get("verification_code") or arguments.get("code")
            password = arguments.get("two_factor_password") or arguments.get("password")
            
            result = await authenticate(
                phone_number=phone,
                verification_code=code,
                two_factor_password=password
            )
            
            return [TextContent(type="text", text=result)]
        
        # Ensure client is initialized for other tools
        client = await initialize_telegram_client()
        
        if name == "list_chats":
            limit = arguments.get("limit", 20)
            chats = await client.get_chats(limit=min(limit, 100))
            
            response = f"📱 Found {len(chats)} chats:\\n\\n"
            for chat in chats:
                response += f"• {chat['name']} (ID: {chat['id']})\\n"
                response += f"  Type: {chat['type']}, Unread: {chat['unread_count']}\\n"
                if chat['last_message']:
                    msg = chat['last_message']
                    text_preview = msg['text'][:50] + "..." if len(msg['text']) > 50 else msg['text']
                    response += f"  Last: {text_preview}\\n"
                response += "\\n"
            
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
            
            response = f"💬 Retrieved {len(messages)} messages from chat {chat_id}:\\n\\n"
            for msg in messages:
                from_name = msg.get('from_name', 'Unknown')
                response += f"[{msg['date']}] {from_name}:\\n"
                response += f"{msg['text']}\\n"
                if msg.get('media'):
                    response += f"📎 Media: {msg['media']['type']}\\n"
                response += "\\n"
            
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
                f"✅ Message sent successfully!\\n\\n"
                f"Message ID: {result['id']}\\n"
                f"Chat ID: {result['chat_id']}\\n"
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


# =============================================================================
# MCP SSE Server Setup with Proper ASGI Pattern
# =============================================================================

# Health check endpoint
async def health_check(request):
    """Health check endpoint that returns server status."""
    global telegram_client
    
    is_authenticated = False
    if telegram_client is not None:
        try:
            is_authenticated = telegram_client._is_authenticated
        except:
            pass
    
    return Response(
        content=f'{{"status":"healthy","server":"telegram-mcp","version":"1.0.0","authenticated":{str(is_authenticated).lower()}}}',
        media_type="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Create SSE transport
sse = SseServerTransport("/messages")


# SSE endpoint handlers using proper ASGI pattern
async def handle_sse(scope, receive, send):
    """
    Handle SSE requests as a raw ASGI application.
    Let SseServerTransport handle the entire ASGI conversation directly.
    """
    method = scope["method"]
    logger.info(f"🔵 [SSE {method}] Received {method} request to /sse endpoint")
    logger.info(f"🔵 [SSE {method}] Request path: {scope['path']}")
    
    if method == "OPTIONS":
        # Handle CORS preflight
        logger.info(f"🟣 [OPTIONS] Handling CORS preflight")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"access-control-allow-origin", b"*"],
                [b"access-control-allow-methods", b"GET, POST, OPTIONS"],
                [b"access-control-allow-headers", b"*"],
                [b"access-control-max-age", b"86400"],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })
        return
    
    if method == "GET":
        # Handle SSE connection - let the transport control the entire response
        logger.info(f"📡 [SSE GET] Setting up SSE connection")
        
        try:
            logger.info(f"✅ [SSE GET] Delegating to SseServerTransport")
            # Let SseServerTransport handle the entire ASGI conversation
            async with sse.connect_sse(scope, receive, send) as (read, write):
                logger.info(f"✅ [SSE GET] SSE connection established, running MCP app")
                await app.run(read, write, app.create_initialization_options())
            logger.info(f"✅ [SSE GET] MCP app finished, connection closed")
        except Exception as e:
            logger.error(f"❌ [SSE GET] Error in SSE connection: {e}", exc_info=True)
            # Don't try to send a response - the transport already handled it or the connection is broken
    
    elif method == "POST":
        # Handle POST messages through the SSE transport
        logger.info(f"🟢 [SSE POST] Handling POST request")
        
        try:
            # Let the transport handle the MCP message processing
            async with sse.connect_sse(scope, receive, send) as (read, write):
                logger.info(f"✅ [SSE POST] Processing MCP message")
                await app.run(read, write, app.create_initialization_options())
            
            # After MCP processing is complete, send a simple success response
            logger.info(f"✅ [SSE POST] POST handled successfully, sending response")
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"access-control-allow-origin", b"*"],
                    [b"access-control-allow-methods", b"GET, POST, OPTIONS"],
                    [b"access-control-allow-headers", b"*"],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"status":"ok"}',
            })
        except Exception as e:
            logger.error(f"❌ [SSE POST] Error handling POST: {e}", exc_info=True)
            # Send error response
            try:
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"access-control-allow-origin", b"*"],
                        [b"access-control-allow-methods", b"GET, POST, OPTIONS"],
                        [b"access-control-allow-headers", b"*"],
                    ],
                })
                error_body = f'{{"status":"error","message":"{str(e)}"}}'.encode()
                await send({
                    "type": "http.response.body",
                    "body": error_body,
                })
            except:
                # Connection might already be broken
                logger.error(f"❌ [SSE POST] Could not send error response")


# Create Starlette app with proper SSE routes and CORS middleware
starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Mount("/sse", app=handle_sse),  # Mount as raw ASGI app
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
)


async def run_stdio_server():
    """Run the MCP stdio server."""
    logger.info("Starting Telegram MCP Server with stdio interface...")
    logger.info(f"API ID: {API_ID}")
    logger.info(f"Session available: {bool(TELEGRAM_SESSION)}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run_sse_server():
    """Run the MCP SSE server."""
    logger.info("Starting Telegram MCP Server with SSE interface...")
    logger.info(f"API ID: {API_ID}")
    logger.info(f"Session available: {bool(TELEGRAM_SESSION)}")
    logger.info("🌐 Server will be available at http://0.0.0.0:8080")
    logger.info("🔌 MCP SSE endpoint: http://0.0.0.0:8080/sse")
    logger.info("❤️ Health check: http://0.0.0.0:8080/health")
    logger.info("✅ Server configured with proper CORS headers and ASGI pattern")
    
    uvicorn.run(
        starlette_app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    # Check if we should run in SSE mode or stdio mode
    # Default to SSE mode when run directly
    mode = os.getenv("MCP_MODE", "sse").lower()
    
    if mode == "stdio":
        # Run stdio server for MCP protocol
        asyncio.run(run_stdio_server())
    else:
        # Run SSE server (default)
        run_sse_server()
