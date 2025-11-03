"""A2A Protocol data models and schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, Union
from datetime import datetime
from uuid import uuid4


# JSON-RPC Base Models
class JSONRPCError(BaseModel):
    """JSON-RPC Error object"""
    code: int
    message: str
    data: Optional[Any] = None

# A2A Message Parts
class TextPart(BaseModel):
    """Text content part"""
    kind: Literal["text"] = "text"
    text: str


class FilePart(BaseModel):
    """File reference part"""
    kind: Literal["file"] = "file"
    url: str
    mimeType: Optional[str] = None
    name: Optional[str] = None


class DataPart(BaseModel):
    """Structured data part"""
    kind: Literal["data"] = "data"
    data: Dict[str, Any]
    mimeType: str = "application/json"

# class MessagePart(BaseModel):
#     kind: Literal["text", "data", "file"]
#     text: Optional[str] = None
#     data: Optional[Dict[str, Any]] = None
#     file_url: Optional[str] = None




class MessagePart(BaseModel):
    kind: str
    text: Optional[str] = None
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None


Part = Union[TextPart, FilePart, DataPart]

class PushNotificationConfig(BaseModel):
    url: str
    token: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None

class MessageMetaData(BaseModel):
    telex_user_id: Optional[str] = None
    telex_channel_id: Optional[str] = None
    org_id: Optional[str] = None

# A2A Messages
class Message(BaseModel):
    """A2A Message"""
    kind: Literal["message"]
    role: Literal["user", "agent", "system"]
    parts: List[MessagePart]
    messageId: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    metadata: Optional[MessageMetaData] = None
    taskId: Optional[str] = None

class MessageConfiguration(BaseModel):
    blocking: bool = True
    acceptedOutputModes: List[str] = ["text/plain", "image/png", "image/svg+xml"]
    pushNotificationConfig: Optional[PushNotificationConfig] = None


class MessageSendParams(BaseModel):
    """Parameters for message/send method"""
    message: Message
    configuration: MessageConfiguration = Field(default_factory=MessageConfiguration)

class MessageParams(BaseModel):
    message: Message
    configuration: MessageConfiguration = Field(default_factory=MessageConfiguration)

class ExecuteParams(BaseModel):
    contextId: Optional[str] = None
    taskId: Optional[str] = None
    messages: List[Message]


# A2A Tasks
class TaskStatus(BaseModel):
    """Task status information"""
    state: Literal["submitted", "working", "completed", "failed", "canceled", "input-required"]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    message: Optional[Message] = None



class Artifact(BaseModel):
    """Task output artifact"""
    artifactId: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    parts: List[MessagePart]

class TaskResult(BaseModel):
    id: str
    contextId: str
    status: TaskStatus
    artifacts: List[Artifact] = []
    history: List[Message] = []
    kind: Literal["task"] = "task"

class Task(BaseModel):
    """A2A Task object"""
    id: str
    contextId: Optional[str] = None
    status: TaskStatus
    message: Optional[Message] = None
    artifacts: Optional[List[Artifact]] = None


# Agent Card Models
class AgentSkill(BaseModel):
    """Agent skill definition"""
    name: str
    description: str

class AgentCard(BaseModel):
    """Agent Card - agent's public metadata"""
    name: str
    description: str
    url: str
    version: str = "0.1.0"
    skills: List[AgentSkill]
    
    # Authentication (optional)
    authentication: Optional[Dict[str, Any]] = None
    
    # Capabilities
    supportsStreaming: bool = False
    supportsPushNotifications: bool = False

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request"""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: MessageSendParams | ExecuteParams



class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response"""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[TaskResult] = None
    error: Optional[JSONRPCError] = None

# Error Codes
class A2AErrorCode:
    """Standard A2A error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # A2A specific
    TASK_NOT_FOUND = -32001
    TASK_CANCELED = -32002
    UNAUTHORIZED = -32003
