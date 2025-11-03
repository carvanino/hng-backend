"""Main Budget Agent - A2A compatible orchestrator"""

from typing import Optional, List
from uuid import uuid4
import logging
from datetime import datetime
import httpx
from .core import (
    GmailMonitor, TransactionParser, CategoryClassifier,
    ExcelManager, UserStore
)
from .a2a import (
    Message, MessageConfiguration, TaskResult, MessagePart, TaskStatus,
    Artifact
)

logger = logging.getLogger(__name__)


class BudgetAgent:
    """Main orchestrator for budget tracking via A2A protocol"""
    
    def __init__(self, user_store: UserStore, gemini_api_key: str, base_url: str):
        """
        Initialize Budget Agent
        
        Args:
            user_store: User data storage
            gemini_api_key: Gemini API key for categorization
            base_url: Base URL for OAuth callbacks
        """
        self.user_store = user_store
        self.parser = TransactionParser()
        self.classifier = CategoryClassifier(gemini_api_key)
        self.base_url = base_url
    
    async def process_message(
        self, 
        messages: List[Message], 
        user_id: str,
        task_id: str, 
        config: Optional[MessageConfiguration]
    ) -> TaskResult:
        """Process user message and return TaskResult."""
        import re
        
        def extract_command(parts) -> str:
            """Extract last text from parts (handles Pydantic models and dicts)"""
            all_texts = []
            
            def collect_texts(items):
                if not items:
                    return
                    
                for item in items:
                    # Convert Pydantic model to dict if needed
                    if hasattr(item, 'model_dump'):
                        item = item.model_dump()
                    
                    if not isinstance(item, dict):
                        continue
                    
                    kind = item.get("kind", "")
                    
                    if kind == "text":
                        text = item.get("text", "")
                        clean = re.sub(r'<[^>]+>', '', text).strip()
                        if clean:
                            all_texts.append(clean)
                    
                    elif kind == "data":
                        data = item.get("data", [])
                        if data:
                            collect_texts(data)
            
            collect_texts(parts)
            return all_texts[-1] if all_texts else ""

        #  # Generate IDs if not provided
        user_id = user_id or str(uuid4())
        task_id = task_id or str(uuid4())
        context_id = user_id  # Use user_id as context for continuity
        
        # Default error response
        response_text = "❌ No message received."
        state = "input-required"
        artifacts = []
        
        if messages:
            message = messages[-1]
            
            if hasattr(message, "parts") and message.parts:
                # Convert parts if they're Pydantic models
                parts = message.parts
                if hasattr(parts, '__iter__'):
                    parts = [p.model_dump() if hasattr(p, 'model_dump') else p for p in parts]
                
                command = extract_command(parts)
                
                if command:
                    command = re.sub(r'@[\w\s]+', '', command).strip()
                    logger.info(f"Command: {command}")
                    
                    try:
                        cmd = command.lower()
                        
                        if cmd in ["connect", "start", "setup", "link"]:
                            response_text = await self._handle_connect(user_id)
                        elif cmd in ["status", "check"]:
                            response_text = await self._handle_status(user_id)
                        elif cmd in ["sync", "update", "check transactions"]:
                            response_text = await self._handle_sync(user_id)
                        elif cmd in ["help", "?", "commands"]:
                            response_text = self._handle_help()
                        elif self._is_category_response(command):
                            response_text = await self._handle_category_input(user_id, command)
                        else:
                            response_text = self._handle_unknown(command)
                        
                        artifacts = [Artifact(name="result", parts=[MessagePart(kind="text", text=response_text)])]
                        
                    except Exception as e:
                        logger.error(f"Error: {e}", exc_info=True)
                        response_text = f"❌ Error: {str(e)}"
                else:
                    response_text = "❌ Could not understand your message. Type 'help' for available commands."
            else:
                response_text = "❌ Invalid message format."
        
        # Build response message
        response_message = Message(
            kind="message",
            role="agent",
            parts=[MessagePart(kind="text", text=response_text)],
            taskId=task_id
        )
        
        # Update history
        history = messages + [response_message]
        
        # Return TaskResult
        return TaskResult(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=state,
                message=response_message
            ),
            artifacts=artifacts,
            history=history
        )
  
    async def _handle_connect(self, user_id: str) -> str:
        """Handle connect request"""
        is_connected = self.user_store.is_user_connected(user_id)
        
        if is_connected:
            file_id = self.user_store.get_drive_file_id(user_id)
            credentials = self.user_store.get_credentials(user_id)
            if credentials and file_id:
                excel = ExcelManager(credentials)
                file_url = excel.get_file_url(file_id)
                return f"Already connected! Your budget tracker: {file_url}\n\nType 'sync' to check for new transactions."
        
        # Generate OAuth URL
        oauth_url = f"{self.base_url}/oauth/authorize?user_id={user_id}"
        
        return f"Connect Your Gmail & Google Drive\n\nTo start tracking your budget, I need access to Gmail and Google Drive.\n\nClick here to authorize: {oauth_url}\n\nYour data stays in YOUR Google account."
    
    async def _handle_status(self, user_id: str) -> str:
        """Handle status check"""
        is_connected = self.user_store.is_user_connected(user_id)
        
        if not is_connected:
            return """❌ **Not Connected**

Type 'connect' to link your Gmail and start tracking."""
        
        file_id = self.user_store.get_drive_file_id(user_id)
        credentials = self.user_store.get_credentials(user_id)
        
        if not credentials or not file_id:
            return "⚠️ Connection incomplete. Please type 'connect' to re-authorize."
        
        excel = ExcelManager(credentials)
        file_url = excel.get_file_url(file_id)
        
        return f"""✅ **Connected & Active**

**Budget Tracker:** {file_url}

**Status:**
• Gmail monitoring: Active
• Auto-categorization: Enabled
• Drive sync: Active

Type 'sync' to manually check for new transactions."""
    
    async def _handle_sync(self, user_id: str) -> str:
        """Handle manual sync request"""
        if not self.user_store.is_user_connected(user_id):
            return "❌ Please connect your account first using 'connect'"
        
        try:
            count = await self._process_transactions(user_id)
            
            if count == 0:
                return "✅ No new transactions found. You're all caught up!"
            
            return f"""✅ **Sync Complete**

Processed {count} new transaction(s) and updated your budget tracker.

Type 'status' to view your budget link."""
            
        except Exception as e:
            logger.error(f"Sync error for {user_id}: {e}")
            return f"❌ Sync failed: {str(e)}"
    
    async def _process_transactions(self, user_id: str) -> int:
        """Process unread transactions for user"""
        credentials = self.user_store.get_credentials(user_id)
        file_id = self.user_store.get_drive_file_id(user_id)
        
        if not credentials or not file_id:
            raise ValueError("User not properly connected")
        
        # Initialize services
        gmail = GmailMonitor(credentials)
        excel = ExcelManager(credentials)
        
        # Get relevant transaction emails
        messages = gmail.get_transaction_emails(max_results=20)
        processed = 0
        
        for message in messages:
            # Parse transaction
            transaction = self.parser.parse(message)

            logger.info(f"TRANSACTION --------> {transaction}")
            
            if not transaction:
                continue
            
            # Categorize
            result = self.classifier.categorize(transaction)
            category = result['category']
            
            # Add to Excel
            success = excel.add_transaction(file_id, transaction, category)
            
            if success:
                processed += 1
                gmail.mark_as_read(message['id'])
        
        return processed
    
    def _handle_help(self) -> str:
        """Return help message"""
        return """**Budget Tracker Agent - Commands**

**connect** - Link your Gmail and Google Drive
**status** - Check connection and budget status
**sync** - Manually check for new transactions
**help** - Show this help message

**How it works:**
1. Connect your Gmail and Drive
2. I'll create a budget tracker in your Drive
3. I automatically monitor your Gmail for bank alerts
4. Transactions are categorized and logged in your budget
5. You can view/edit your budget anytime in Google Drive"""
    
    def _handle_unknown(self, message: str) -> str:
        """Handle unknown command"""
        return f"""I didn't understand '{message}'.

Type 'help' to see available commands."""
    
    def _is_category_response(self, message: str) -> bool:
        """Check if message looks like a category response"""
        # Simple heuristic - if it's a single word/short phrase
        return len(message.split()) <= 3 and len(message) < 30
    
    async def _handle_category_input(self, user_id: str, category: str) -> str:
        """Handle user providing category for unclear transaction"""
        # For MVP, just acknowledge
        # Full implementation would store pending transaction and apply category
        return f"✅ Got it! I'll use '{category}' for that transaction."
    
    async def complete_oauth_setup(self, user_id: str, credentials) -> str:
        """
        Complete setup after OAuth authorization
        
        Args:
            user_id: User identifier
            credentials: Google OAuth credentials
            
        Returns:
            Success message
        """
        try:
            # Save OAuth tokens
            self.user_store.save_oauth_tokens(user_id, credentials)
            
            # Create budget file
            excel = ExcelManager(credentials)
            file_id = excel.create_budget_file(user_id)
            
            # Save file ID
            self.user_store.save_drive_file_id(user_id, file_id)
            
            # Get file URL
            file_url = excel.get_file_url(file_id)
            
            # Send proactive message with details
            response_text = f"""✅ **Setup Complete!**

Your budget tracker: {file_url}

I'm now monitoring your Gmail for transaction alerts. Whenever you receive a bank alert, I'll automatically categorize it and update your budget.

Type 'sync' to process any existing transactions, or just wait for new ones to arrive!"""
            
            await self.send_proactive_message(user_id, response_text)
            
            # Return a simple message for the OAuth callback page
            return "Authorization successful! You can close this window and return to Telex."
            
        except Exception as e:
            logger.error(f"OAuth setup error for {user_id}: {e}")
            # Potentially send a proactive failure message
            await self.send_proactive_message(user_id, f"❌ **Setup Failed!**\n\nAn error occurred: {e}")
            raise

    async def send_proactive_message(self, user_id: str, text: str):
        """
        Send a proactive message to the user.
        This requires a webhook URL and token to be configured.
        """
        webhook_url = self.user_store.get_webhook_url(user_id)
        token = self.user_store.get_webhook_token(user_id)
        
        if not webhook_url or not token:
            logger.warning(f"Webhook URL or token not configured for user {user_id}. Cannot send proactive message.")
            return
        
        task_id = str(uuid4())
        message = {
            "kind": "message",
            "role": "agent",
            "parts": [{"kind": "text", "text": text}],
            "messageId": str(uuid4()),
            "taskId": task_id,
            "contextId": user_id
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid4()),  # A new request ID
                "method": "message/send",
                "params": {
                    "message": message
                }
            }
            
            logger.info(f"Sending proactive message to {user_id} at {webhook_url}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Proactive message sent successfully to {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to send proactive message to {user_id}: {e}", exc_info=True)
            # Do not re-raise, as this is often a background task

   