"""
Vercel serverless function entry point for Telegram MCP Server.
This allows the MCP server to be deployed as a serverless function on Vercel.
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app, initialize_telegram_client
from mcp.types import JSONRPCRequest, JSONRPCNotification


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def do_POST(self):
        """Handle POST requests for MCP protocol."""
        try:
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON-RPC request
            request_data = json.loads(body)
            
            # Handle MCP server initialization
            if request_data.get('method') == 'initialize':
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
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # For other requests, return a message
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'message': 'Telegram MCP Server (Python/Telethon)',
                'note': 'For full MCP functionality, run locally with: python main.py'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests - return server info."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            'name': 'Telegram MCP Server',
            'version': '2.0.0',
            'runtime': 'Python/Telethon',
            'status': 'running',
            'description': 'Model Context Protocol server for Telegram with user authentication',
            'documentation': 'https://github.com/StreetFDN/telegram-mcp'
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
