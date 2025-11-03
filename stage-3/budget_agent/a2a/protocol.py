"""A2A JSON-RPC protocol handler"""

from .schemas import (
    JSONRPCRequest, JSONRPCResponse, JSONRPCError,
    Message, Task, TaskStatus, TextPart, A2AErrorCode
)
from typing import Dict, Any, Optional
import httpx
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class A2AProtocolHandler:
    """Handle A2A JSON-RPC requests"""
    
    def __init__(self, agent_handler, user_store):
        """
        Initialize protocol handler
        
        Args:
            agent_handler: The budget agent that processes messages
        """
        self.agent = agent_handler
        self.user_store = user_store
        self.tasks: Dict[str, Task] = {}  # In-memory task store

    async def _send_push_notification(self, webhook_url: str, token: str, task: Dict[str, Any], original_request_id: str):
        """Send task result to Telex webhook for non-blocking responses"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Telex expects a message/send format response
            payload = {
                "jsonrpc": "2.0",
                "id": original_request_id,  # Use original request ID
                "method": "message/send",   # Must be message/send
                "params": {
                    "message": task.get("message", {})  # Send the message part
                }
            }
            
            logger.info(f"Sending webhook payload: {payload}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload, headers=headers)
                
                logger.info(f"Webhook response status: {response.status_code}")
                logger.info(f"Webhook response body: {response.text}")
                
                response.raise_for_status()
                logger.info(f"Push notification sent successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error sending push notification: {e}", exc_info=True)
            return False

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming JSON-RPC request
        
        Args:
            request_data: Raw request dictionary
            
        Returns:
            JSON-RPC response dictionary
        """
        try:
            # Parse request
            request = JSONRPCRequest(**request_data)

            messages = []
            context_id = None
            task_id = None
            config = None
            
            # Route to method handler
            if request.method == "message/send":
                messages = [request.params.message]
                config = request.params.configuration
                metadata = request.params.message.metadata
                if metadata:
                    context_id = metadata.telex_user_id

                    # save webhook_url in user data
                    webhook_url = config.pushNotificationConfig.url
                    token = config.pushNotificationConfig.token
                    self.user_store.save_webhook_config(context_id, webhook_url, token)
                # result = await self._handle_message_send(request)
            elif request.method == "tasks/get":
                result = await self._handle_tasks_get(request)
            else:
                # Method not found
                return self._error_response(
                    request.id,
                    A2AErrorCode.METHOD_NOT_FOUND,
                    f"Method '{request.method}' not found"
                )
            
            logger.info(f"USER ID -> {context_id}")
            
            result = await self.agent.process_message(
                messages=messages,
                user_id=context_id,
                task_id=task_id,
                config=config
            )

            logger.info(f"RESULT -> {result}")

            
            # Success response
            return JSONRPCResponse(
                id=request.id,
                result=result
            ).model_dump(exclude_none=True)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(
                None,
                A2AErrorCode.INTERNAL_ERROR,
                str(e)
            )

    async def _handle_message_send(self, request: JSONRPCRequest) -> Dict[str, Any]:
        """Handle message/send method - Full A2A Task format"""
        try:
            params = request.params or {}
            message_data = params.get("message", {})
            
            # Extract user message text
            user_text = ""
            parts = message_data.get("parts", [])
            
            for part in parts:
                if isinstance(part, dict):
                    part_kind = part.get("kind", "")
                    
                    if part_kind == "text":
                        text = part.get("text", "")
                        if text and not text.startswith("<p>"):
                            user_text = text
                    
                    elif part_kind == "data":
                        data_array = part.get("data", [])
                        if isinstance(data_array, list) and len(data_array) > 0:
                            last_item = data_array[-1]
                            if isinstance(last_item, dict) and last_item.get("kind") == "text":
                                user_text = last_item.get("text", "")
            
            # Clean up
            import re
            user_text = re.sub(r'<[^>]+>', '', user_text).strip()
            user_text = re.sub(r'@\w+\s*', '', user_text).strip()
            
            if not user_text:
                user_text = "help"
            
            logger.info(f"Extracted user message: {user_text}")
            
            # Process with agent
            context_id = message_data.get("messageId", str(uuid.uuid4()))
            task_id = str(uuid.uuid4())
            
            response_text = await self.agent.process_message(
                message=user_text,
                user_id=context_id,
                task_id=task_id
            )
            
            # Return full Task object
            result = {
                "id": task_id,
                "contextId": context_id,
                "status": {
                    "state": "completed",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": {
                        "messageId": str(uuid.uuid4()),
                        "role": "agent",
                        "parts": [
                            {
                                "kind": "text",
                                "text": response_text
                            }
                        ],
                        "kind": "message",
                        "taskId": task_id
                    }
                },
                "kind": "task"
            }
            
            logger.info(f"Returning full Task response")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in message/send: {e}", exc_info=True)
            raise
    async def _process_and_notify(self, user_text: str, context_id: str, 
                                task_id: str, webhook_url: str, token: str, request_id: str):
        """Background task to process message and send notification"""
        try:
            # Process message
            response_text = await self.agent.process_message(
                message=user_text,
                user_id=context_id,
                task_id=task_id
            )
            
            # Create completed task
            task = {
                "id": task_id,
                "contextId": context_id,
                "status": {
                    "state": "completed",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "message": {
                    "kind": "message",
                    "role": "agent",
                    "parts": [{"kind": "text", "text": response_text}],
                    "messageId": str(uuid.uuid4()),
                    "taskId": task_id
                }
            }
            
            # Send to webhook
            await self._send_push_notification(webhook_url, token, task, request_id)
            
        except Exception as e:
            logger.error(f"Error in background processing: {e}")

    async def _handle_tasks_get(self, request: JSONRPCRequest) -> Dict[str, Any]:
        """Handle tasks/get method"""
        params = request.params or {}
        task_id = params.get("id")
        
        if not task_id:
            raise ValueError("Task ID required")
        
        task = self.tasks.get(task_id)
        if not task:
            return self._error_response(
                request.id,
                A2AErrorCode.TASK_NOT_FOUND,
                f"Task {task_id} not found"
            )
        
        return task.model_dump(exclude_none=True)
    
    def _error_response(self, request_id: Optional[Any], 
                       code: int, message: str) -> Dict[str, Any]:
        """Create error response"""
        return JSONRPCResponse(
            id=request_id,
            error=JSONRPCError(code=code, message=message)
        ).model_dump(exclude_none=True)
