"""Telex.im A2A protocol client"""

import httpx
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TelexClient:
    """Handle communication with Telex.im via A2A protocol"""
    
    def __init__(self, api_url: str = "https://api.telex.im"):
        """Initialize Telex client"""
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(self, channel_id: str, message: str, 
                          message_type: str = "text") -> bool:
        """
        Send message to user on Telex
        
        Args:
            channel_id: Telex channel ID
            message: Message text to send
            message_type: Type of message (text, markdown, etc.)
        """
        try:
            payload = {
                "channel_id": channel_id,
                "message": message,
                "type": message_type
            }
            
            response = await self.client.post(
                f"{self.api_url}/messages/send",
                json=payload
            )
            
            response.raise_for_status()
            logger.info(f"Sent message to channel {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Telex message: {e}")
            return False
    
    async def send_oauth_link(self, channel_id: str, auth_url: str) -> bool:
        """Send OAuth authorization link to user"""
        message = f"""🔐 **Connect Your Gmail & Google Drive**

            To start tracking your budget, I need access to:
            - Gmail (to read transaction alerts)
            - Google Drive (to store your budget file)

            Click here to authorize: {auth_url}

            Your data stays in YOUR Google account. I only access what you explicitly grant."""
        
        return await self.send_message(channel_id, message, "markdown")
    
    async def send_transaction_confirmation(self, channel_id: str, 
                                           transaction: Dict, category: str) -> bool:
        """Send transaction processed confirmation"""
        trans_type = "💸 Expense" if transaction['type'] == 'expense' else "💰 Income"
        
        message = f"""{trans_type} Recorded

**Amount:** ₦{transaction['amount']:,.2f}
**Category:** {category}
**Description:** {transaction['description']}
**Date:** {transaction['date']}

✅ Budget tracker updated!"""
        
        return await self.send_message(channel_id, message, "markdown")
    
    async def ask_clarification(self, channel_id: str, transaction: Dict) -> bool:
        """Ask user to clarify transaction category"""
        message = f"""❓ **Need Your Help**

I found this transaction but I'm not sure how to categorize it:

**Amount:** ₦{transaction['amount']:,.2f}
**Description:** {transaction['description']}

What category should this be? (e.g., Transportation, Feeding, Shopping, etc.)"""
        
        return await self.send_message(channel_id, message, "markdown")
    
    async def send_welcome(self, channel_id: str) -> bool:
        """Send welcome message to new user"""
        message = """👋 **Welcome to Budget Tracker!**

I help you track your expenses automatically by monitoring your Gmail for transaction alerts.

**To get started:**
1. Type "connect" to link your Gmail
2. I'll create a budget tracker in your Google Drive
3. I'll automatically log transactions from your bank alerts

**Commands:**
- `connect` - Link your Gmail and Drive
- `status` - Check connection status
- `summary` - Get spending summary
- `help` - Show all commands"""
        
        return await self.send_message(channel_id, message, "markdown")
    
    async def send_summary(self, channel_id: str, summary_data: Dict) -> bool:
        """Send spending summary to user"""
        message = f"""📊 **Your Budget Summary**

**Total Income:** ₦{summary_data.get('total_income', 0):,.2f}
**Total Expenses:** ₦{summary_data.get('total_expenses', 0):,.2f}
**Balance:** ₦{summary_data.get('balance', 0):,.2f}

**Top Categories:**
"""
        
        for category, amount in summary_data.get('top_categories', []):
            message += f"- {category}: ₦{amount:,.2f}\n"
        
        if summary_data.get('file_url'):
            message += f"\n[View Full Budget]({summary_data['file_url']})"
        
        return await self.send_message(channel_id, message, "markdown")
    
    async def send_error(self, channel_id: str, error_msg: str) -> bool:
        """Send error message to user"""
        message = f"""❌ **Error**

{error_msg}

If this persists, please try reconnecting your account or contact support."""
        
        return await self.send_message(channel_id, message, "markdown")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
