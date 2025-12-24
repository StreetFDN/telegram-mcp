"""
Vercel serverless function entry point for Telegram MCP Server.
This allows the MCP server to be deployed as a serverless function on Vercel.
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Verbose logging function
def log(message: str, level: str = "INFO"):
    """Print log message with timestamp for Vercel logs."""
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] [{level}] {message}", flush=True)

try:
    log("=== STARTING IMPORT PROCESS ===")
    log(f"Python version: {sys.version}")
    log(f"Current working directory: {os.getcwd()}")
    log(f"Python path: {sys.path}")
    
    log("Attempting to import TelegramUserClient...")
    from telegram_client import TelegramUserClient
    log("✓ Successfully imported TelegramUserClient")
    
    log("Attempting to import Telethon modules...")
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import (
        ApiIdInvalidError, 
        PhoneNumberInvalidError, 
        FloodWaitError,
        SessionPasswordNeededError,
        PhoneCodeInvalidError,
        PhoneCodeExpiredError,
        PasswordHashInvalidError
    )
    log("✓ Successfully imported Telethon modules")
    
except Exception as e:
    log(f"✗ IMPORT ERROR: {str(e)}", "ERROR")
    log(f"Error type: {type(e).__name__}", "ERROR")
    import traceback
    log(f"Traceback:\n{traceback.format_exc()}", "ERROR")


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send a JSON response."""
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
        except Exception as e:
            log(f"Error sending response: {str(e)}", "ERROR")
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for MCP protocol and authentication."""
        log("=== RECEIVED POST REQUEST ===")
        
        try:
            # Get request body
            log("Reading request body...")
            content_length = int(self.headers.get('Content-Length', 0))
            log(f"Content-Length: {content_length}")
            
            body = self.rfile.read(content_length).decode('utf-8')
            log(f"Raw body received: {body[:200]}..." if len(body) > 200 else f"Raw body: {body}")
            
            # Parse JSON-RPC request
            log("Parsing JSON request...")
            request_data = json.loads(body)
            log(f"Parsed request data: {json.dumps(request_data, indent=2)}")
            
            method = request_data.get('method', '')
            log(f"Request method: {method}")
            
            # Handle MCP server initialization
            if method == 'initialize':
                log("Handling MCP initialize request")
                response = {
                    'jsonrpc': '2.0',
                    'id': request_data.get('id'),
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'serverInfo': {
                            'name': 'telegram-mcp',
                            'version': '2.0.0'
                        },
                        'capabilities': {
                            'tools': {}
                        }
                    }
                }
                log("✓ Sending initialize response")
                self._send_json_response(200, response)
                return
            
            # Handle authentication request
            if method == 'authenticate':
                log("=== HANDLING AUTHENTICATION REQUEST ===")
                arguments = request_data.get('arguments', {})
                
                phone = arguments.get('phone')
                code = arguments.get('code')
                password = arguments.get('password')
                
                log(f"Auth parameters - Phone: {phone}, Code: {'*' * len(code) if code else None}, Password: {'*****' if password else None}")
                
                # Run async authentication
                result = asyncio.run(self._authenticate_async(phone, code, password))
                
                log(f"Authentication result status: {result.get('status')}")
                self._send_json_response(200, result)
                return
            
            # For other requests, return a message
            log("Handling generic request")
            response = {
                'status': 'ok',
                'message': 'Telegram MCP Server (Python/Telethon)',
                'note': 'For full MCP functionality, run locally with: python main.py',
                'endpoints': {
                    'POST /api': 'MCP JSON-RPC endpoint',
                    'POST /api with method=authenticate': 'Direct authentication testing'
                }
            }
            self._send_json_response(200, response)
            
        except json.JSONDecodeError as e:
            log(f"✗ JSON Parse Error: {str(e)}", "ERROR")
            self._send_json_response(400, {
                'error': 'Invalid JSON',
                'details': str(e)
            })
        except Exception as e:
            log(f"✗ POST Handler Error: {str(e)}", "ERROR")
            import traceback
            log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
            self._send_json_response(500, {
                'error': str(e),
                'type': type(e).__name__
            })
    
    async def _authenticate_async(self, phone: str = None, code: str = None, password: str = None):
        """
        Async authentication handler with comprehensive logging.
        """
        log("=== STARTING ASYNC AUTHENTICATION ===")
        
        try:
            # Get environment variables
            log("Reading environment variables...")
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            session_string = os.getenv('TELEGRAM_SESSION', '')
            
            log(f"API_ID present: {bool(api_id)}")
            log(f"API_HASH present: {bool(api_hash)}")
            log(f"SESSION_STRING present: {bool(session_string)}")
            log(f"SESSION_STRING length: {len(session_string) if session_string else 0}")
            
            if not api_id or not api_hash:
                log("✗ Missing API credentials", "ERROR")
                return {
                    'status': 'error',
                    'message': 'TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables are required'
                }
            
            try:
                api_id = int(api_id)
                log(f"✓ API_ID parsed: {api_id}")
            except ValueError as e:
                log(f"✗ Invalid API_ID format: {str(e)}", "ERROR")
                return {
                    'status': 'error',
                    'message': 'TELEGRAM_API_ID must be a valid integer'
                }
            
            # Create Telegram client
            log("Creating TelegramUserClient instance...")
            try:
                client = TelegramUserClient(
                    api_id=api_id,
                    api_hash=api_hash,
                    session_string=session_string
                )
                log("✓ TelegramUserClient created successfully")
            except ApiIdInvalidError as e:
                log(f"✗ ApiIdInvalidError: {str(e)}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Invalid Telegram API ID: {str(e)}',
                    'error_type': 'ApiIdInvalidError'
                }
            except Exception as e:
                log(f"✗ Client creation error: {str(e)}", "ERROR")
                log(f"Error type: {type(e).__name__}", "ERROR")
                import traceback
                log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Failed to create client: {str(e)}',
                    'error_type': type(e).__name__
                }
            
            # Attempt authentication
            log("Attempting to start authentication...")
            log(f"Auth mode: {'existing session' if session_string else 'new authentication'}")
            
            try:
                result = await client.start(phone=phone, code=code, password=password)
                log(f"✓ Authentication completed with status: {result.get('status')}")
                log(f"Full result: {json.dumps({k: v if k != 'user' else '...' for k, v in result.items()}, indent=2)}")
                
                # If authenticated successfully, include session string
                if result.get('status') == 'authenticated':
                    session = client.get_session_string()
                    log(f"✓ Session string generated (length: {len(session)})")
                    result['session_string'] = session
                    result['instruction'] = 'Save this session string as TELEGRAM_SESSION environment variable'
                
                return result
                
            except ApiIdInvalidError as e:
                log(f"✗ ApiIdInvalidError during auth: {str(e)}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Invalid Telegram API credentials: {str(e)}',
                    'error_type': 'ApiIdInvalidError',
                    'hint': 'Check your TELEGRAM_API_ID and TELEGRAM_API_HASH'
                }
            
            except PhoneNumberInvalidError as e:
                log(f"✗ PhoneNumberInvalidError: {str(e)}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Invalid phone number format: {str(e)}',
                    'error_type': 'PhoneNumberInvalidError',
                    'hint': 'Use international format: +1234567890'
                }
            
            except PhoneCodeInvalidError as e:
                log(f"✗ PhoneCodeInvalidError: {str(e)}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Invalid verification code: {str(e)}',
                    'error_type': 'PhoneCodeInvalidError',
                    'hint': 'Check the code sent to your phone'
                }
            
            except PhoneCodeExpiredError as e:
                log(f"✗ PhoneCodeExpiredError: {str(e)}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Verification code expired: {str(e)}',
                    'error_type': 'PhoneCodeExpiredError',
                    'hint': 'Request a new code'
                }
            
            except PasswordHashInvalidError as e:
                log(f"✗ PasswordHashInvalidError: {str(e)}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Invalid 2FA password: {str(e)}',
                    'error_type': 'PasswordHashInvalidError',
                    'hint': 'Check your two-factor authentication password'
                }
            
            except FloodWaitError as e:
                log(f"✗ FloodWaitError: {str(e)}", "ERROR")
                wait_seconds = e.seconds if hasattr(e, 'seconds') else 'unknown'
                return {
                    'status': 'error',
                    'message': f'Rate limited by Telegram. Please wait {wait_seconds} seconds.',
                    'error_type': 'FloodWaitError',
                    'wait_seconds': wait_seconds
                }
            
            except SessionPasswordNeededError as e:
                log(f"SessionPasswordNeededError: {str(e)}")
                return {
                    'status': 'needs_password',
                    'message': 'Two-factor authentication is enabled. Please provide your password.',
                    'error_type': 'SessionPasswordNeededError'
                }
            
            except Exception as e:
                log(f"✗ Unexpected authentication error: {str(e)}", "ERROR")
                log(f"Error type: {type(e).__name__}", "ERROR")
                import traceback
                log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
                return {
                    'status': 'error',
                    'message': f'Authentication error: {str(e)}',
                    'error_type': type(e).__name__
                }
            
            finally:
                # Clean up
                log("Cleaning up client connection...")
                try:
                    await client.disconnect()
                    log("✓ Client disconnected")
                except Exception as e:
                    log(f"Error during disconnect: {str(e)}", "WARNING")
        
        except Exception as e:
            log(f"✗ CRITICAL ERROR in _authenticate_async: {str(e)}", "ERROR")
            import traceback
            log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
            return {
                'status': 'error',
                'message': f'Critical error: {str(e)}',
                'error_type': type(e).__name__
            }
    
    def do_GET(self):
        """Handle GET requests - return server info."""
        log("=== RECEIVED GET REQUEST ===")
        log(f"Path: {self.path}")
        log(f"Headers: {dict(self.headers)}")
        
        try:
            # Check environment
            env_status = {
                'TELEGRAM_API_ID': bool(os.getenv('TELEGRAM_API_ID')),
                'TELEGRAM_API_HASH': bool(os.getenv('TELEGRAM_API_HASH')),
                'TELEGRAM_SESSION': bool(os.getenv('TELEGRAM_SESSION'))
            }
            
            log(f"Environment check: {env_status}")
            
            response = {
                'name': 'Telegram MCP Server',
                'version': '2.0.0',
                'runtime': 'Python/Telethon',
                'status': 'running',
                'description': 'Model Context Protocol server for Telegram with user authentication',
                'documentation': 'https://github.com/StreetFDN/telegram-mcp',
                'environment': env_status,
                'endpoints': {
                    'GET /api': 'Server info and health check',
                    'POST /api': 'MCP JSON-RPC endpoint',
                    'POST /api with method=authenticate': 'Authentication endpoint for testing'
                },
                'test_instructions': {
                    'step_1': 'Set environment variables: TELEGRAM_API_ID, TELEGRAM_API_HASH',
                    'step_2': 'POST to /api with: {"method": "authenticate", "arguments": {"phone": "+1234567890"}}',
                    'step_3': 'POST with code: {"method": "authenticate", "arguments": {"phone": "+1234567890", "code": "12345"}}',
                    'step_4': 'If 2FA: {"method": "authenticate", "arguments": {"phone": "+...", "code": "...", "password": "..."}}'
                }
            }
            
            log("✓ Sending GET response")
            self._send_json_response(200, response)
            
        except Exception as e:
            log(f"✗ GET Handler Error: {str(e)}", "ERROR")
            import traceback
            log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
            self._send_json_response(500, {
                'error': str(e),
                'type': type(e).__name__
            })


log("=== API INDEX MODULE LOADED SUCCESSFULLY ===")
