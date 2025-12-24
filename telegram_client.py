"""
Telethon client for user authentication and message handling.
Handles user session authentication and Telegram API interactions.
"""

import os
import asyncio
from typing import Optional, List, Dict, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message, User, Chat, Channel
from telethon.errors import SessionPasswordNeededError
import logging

logger = logging.getLogger(__name__)


class TelegramUserClient:
    """
    Telethon client wrapper for user authentication and Telegram operations.
    Supports session persistence and first-time phone verification.
    """
    
    def __init__(self, api_id: int, api_hash: str, session_string: Optional[str] = None):
        """
        Initialize Telegram client.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            session_string: Optional session string for authentication persistence
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string or os.getenv('TELEGRAM_SESSION', '')
        
        # Create client with string session for easy persistence
        self.client = TelegramClient(
            StringSession(self.session_string),
            self.api_id,
            self.api_hash
        )
        self._is_authenticated = False
    
    async def start(self, phone: Optional[str] = None, code: Optional[str] = None, 
                   password: Optional[str] = None) -> Dict[str, Any]:
        """
        Start the client and authenticate.
        
        Args:
            phone: Phone number for first-time authentication
            code: Verification code sent to phone
            password: 2FA password if enabled
            
        Returns:
            Dict with authentication status and session info
        """
        try:
            if self.session_string:
                # Try to connect with existing session
                await self.client.connect()
                if await self.client.is_user_authorized():
                    self._is_authenticated = True
                    me = await self.client.get_me()
                    return {
                        'status': 'authenticated',
                        'user': {
                            'id': me.id,
                            'first_name': me.first_name,
                            'last_name': me.last_name,
                            'username': me.username,
                            'phone': me.phone
                        },
                        'session': self.client.session.save()
                    }
            
            # Need to authenticate
            if not phone:
                return {
                    'status': 'needs_phone',
                    'message': 'Phone number required for first-time setup'
                }
            
            await self.client.connect()
            
            # Send code request
            if not code:
                await self.client.send_code_request(phone)
                return {
                    'status': 'needs_code',
                    'message': 'Verification code sent to your phone. Please provide the code.'
                }
            
            # Sign in with code
            try:
                await self.client.sign_in(phone, code)
                self._is_authenticated = True
                me = await self.client.get_me()
                return {
                    'status': 'authenticated',
                    'user': {
                        'id': me.id,
                        'first_name': me.first_name,
                        'last_name': me.last_name,
                        'username': me.username,
                        'phone': me.phone
                    },
                    'session': self.client.session.save()
                }
            except SessionPasswordNeededError:
                # 2FA enabled
                if not password:
                    return {
                        'status': 'needs_password',
                        'message': 'Two-factor authentication enabled. Please provide your password.'
                    }
                await self.client.sign_in(password=password)
                self._is_authenticated = True
                me = await self.client.get_me()
                return {
                    'status': 'authenticated',
                    'user': {
                        'id': me.id,
                        'first_name': me.first_name,
                        'last_name': me.last_name,
                        'username': me.username,
                        'phone': me.phone
                    },
                    'session': self.client.session.save()
                }
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def ensure_connected(self):
        """Ensure client is connected and authenticated."""
        if not self.client.is_connected():
            await self.client.connect()
        
        if not self._is_authenticated:
            if not await self.client.is_user_authorized():
                raise Exception("Not authenticated. Please authenticate first.")
            self._is_authenticated = True
    
    async def get_chats(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get list of user's chats/dialogs.
        
        Args:
            limit: Maximum number of chats to retrieve
            
        Returns:
            List of chat information dictionaries
        """
        await self.ensure_connected()
        
        chats = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            chat_info = {
                'id': dialog.id,
                'name': dialog.name,
                'type': 'user' if dialog.is_user else ('group' if dialog.is_group else 'channel'),
                'unread_count': dialog.unread_count,
                'last_message': None
            }
            
            if dialog.message:
                chat_info['last_message'] = {
                    'id': dialog.message.id,
                    'text': dialog.message.text or '',
                    'date': dialog.message.date.isoformat(),
                    'from_id': dialog.message.from_id.user_id if hasattr(dialog.message.from_id, 'user_id') else None
                }
            
            chats.append(chat_info)
        
        return chats
    
    async def get_messages(self, chat_id: int, limit: int = 10, 
                          offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages from a specific chat.
        
        Args:
            chat_id: Chat/Channel/User ID
            limit: Number of messages to retrieve
            offset: Offset for pagination
            
        Returns:
            List of message dictionaries
        """
        await self.ensure_connected()
        
        messages = []
        async for message in self.client.iter_messages(
            chat_id, 
            limit=limit,
            offset_id=offset
        ):
            msg_dict = {
                'id': message.id,
                'text': message.text or '',
                'date': message.date.isoformat(),
                'from_id': None,
                'from_name': None,
                'reply_to': message.reply_to_msg_id if message.reply_to else None,
                'media': None
            }
            
            # Get sender info
            if message.sender:
                sender = message.sender
                if isinstance(sender, User):
                    msg_dict['from_id'] = sender.id
                    msg_dict['from_name'] = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                    if sender.username:
                        msg_dict['from_username'] = sender.username
            
            # Check for media
            if message.media:
                msg_dict['media'] = {
                    'type': type(message.media).__name__,
                    'has_media': True
                }
            
            messages.append(msg_dict)
        
        return messages
    
    async def send_message(self, chat_id: int, text: str, 
                          reply_to: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a message to a chat.
        
        Args:
            chat_id: Chat/Channel/User ID
            text: Message text
            reply_to: Optional message ID to reply to
            
        Returns:
            Sent message information
        """
        await self.ensure_connected()
        
        message = await self.client.send_message(
            chat_id,
            text,
            reply_to=reply_to
        )
        
        return {
            'id': message.id,
            'text': message.text,
            'date': message.date.isoformat(),
            'chat_id': chat_id
        }
    
    async def disconnect(self):
        """Disconnect the client."""
        if self.client.is_connected():
            await self.client.disconnect()
    
    def get_session_string(self) -> str:
        """Get the current session string for persistence."""
        return self.client.session.save()
