"""Core data models for AgentOS."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent lifecycle states."""
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    """Types of agents supported."""
    CHAT = "chat"
    WORKFLOW = "workflow"
    AUTONOMOUS = "autonomous"
    ORCHESTRATOR = "orchestrator"


class PermissionLevel(str, Enum):
    """Permission levels for RBAC."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class ToolType(str, Enum):
    """Types of tools."""
    API = "api"
    DATABASE = "database"
    SEARCH = "search"
    CODE_EXECUTION = "code_execution"
    CUSTOM = "custom"


class MemoryType(str, Enum):
    """Types of memory."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"


class Agent(BaseModel):
    """Agent model."""
    id: str = Field(default_factory=lambda: f"agent_{datetime.now().timestamp()}")
    name: str
    type: AgentType = AgentType.CHAT
    description: Optional[str] = None
    status: AgentStatus = AgentStatus.CREATED
    config: Dict[str, Any] = Field(default_factory=dict)
    tools: List[str] = Field(default_factory=list)
    memory_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Tool(BaseModel):
    """Tool model."""
    id: str = Field(default_factory=lambda: f"tool_{datetime.now().timestamp()}")
    name: str
    type: ToolType = ToolType.CUSTOM
    description: Optional[str] = None
    endpoint: Optional[str] = None
    schema: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class Memory(BaseModel):
    """Memory entry model."""
    id: str = Field(default_factory=lambda: f"mem_{datetime.now().timestamp()}")
    agent_id: str
    type: MemoryType = MemoryType.SHORT_TERM
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class Workflow(BaseModel):
    """Workflow model."""
    id: str = Field(default_factory=lambda: f"wf_{datetime.now().timestamp()}")
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.now)


class User(BaseModel):
    """User model for governance."""
    id: str = Field(default_factory=lambda: f"user_{datetime.now().timestamp()}")
    username: str
    email: Optional[str] = None
    role: str = "user"
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class AuditLog(BaseModel):
    """Audit log entry."""
    id: str = Field(default_factory=lambda: f"log_{datetime.now().timestamp()}")
    user_id: str
    action: str
    resource: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class Task(BaseModel):
    """Task model for agent execution."""
    id: str = Field(default_factory=lambda: f"task_{datetime.now().timestamp()}")
    agent_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    status: str = "pending"
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
