"""Gmail monitoring and email retrieval"""

import base64
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class GmailMonitor:
    """Handles Gmail API operations for monitoring transaction emails"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, credentials: Credentials):
        """Initialize Gmail service with user credentials"""
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)
    
    def get_transaction_emails(self, max_results: int = 20) -> List[Dict]:
        """
        Fetch unread emails that are likely to be financial transactions.
        
        Args:
            max_results: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries with id, subject, body, date
        """
        # This query looks for unread emails containing common financial keywords.
        # It can be customized further for specific bank alert formats.
        today = datetime.utcnow()

        first_day = today.replace(day=1)
        next_month = ''
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)

        after = first_day.strftime("after:%Y/%m/%d")
        before = next_month.strftime("before:%Y/%m/%d")

        query = (
            'is:unread in:inbox '
            '(subject:transaction OR '
            'subject:"Transfer" OR '
            'subject:"credit alert") '
            f'{after} {before}'
        )
        
        try:
            # Use the existing search_messages functionality
            return self.search_messages(query, max_results)
            
        except HttpError as error:
            logger.error(f"Gmail API error during transaction search: {error}")
            raise
    
    def _get_message_details(self, msg_id: str) -> Optional[Dict]:
        """Get full details of a specific message"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }
            
        except HttpError as error:
            logger.error(f"Error fetching message {msg_id}: {error}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'parts' in part:
                    # Recursive for nested parts
                    body = self._extract_body(part)
                    if body:
                        return body
        
        return ""
    
    def mark_as_read(self, msg_id: str) -> bool:
        """Mark a message as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.info(f"Marked message {msg_id} as read")
            return True
        except HttpError as error:
            logger.error(f"Error marking message as read: {error}")
            return False
    
    def search_messages(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search messages with custom query
        
        Args:
            query: Gmail search query (e.g., 'from:bank@example.com subject:transaction')
            max_results: Maximum results to return
            
        Returns:
            List of matching messages
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])

            logger.info(f"MESSAGES _> _> _> {messages}")
            
            detailed_messages = []
            for msg in messages:
                msg_data = self._get_message_details(msg['id'])
                if msg_data:
                    detailed_messages.append(msg_data)
            
            return detailed_messages
            
        except HttpError as error:
            logger.error(f"Error searching messages: {error}")
            return []
