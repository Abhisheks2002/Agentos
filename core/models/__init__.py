"""AgentOS Core Data Models"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent lifecycle states"""
    CREATED = "created"
    RUNNING = "running"
    IDLE = "idle"
    ERROR = "error"
    STOPPED = "stopped"


class AgentType(str, Enum):
    """Types of agents supported"""
    CONVERSATIONAL = "conversational"
    TASK_ORIENTED = "task_oriented"
    WORKFLOW = "workflow"
    RESEARCH = "research"


class PermissionLevel(str, Enum):
    """RBAC permission levels"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    GUEST = "guest"


class ToolType(str, Enum):
    """Types of tools available"""
    API = "api"
    DATABASE = "database"
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    FILE_SYSTEM = "file_system"


# ============ Agent Models ============

class AgentConfig(BaseModel):
    """Configuration for an agent"""
    name: str
    type: AgentType
    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    tools: list[str] = []
    memory_enabled: bool = True
    metadata: dict[str, Any] = {}


class Agent(BaseModel):
    """Core Agent model"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    type: AgentType
    config: AgentConfig
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: Optional[UUID] = None


class AgentExecution(BaseModel):
    """Execution context for an agent task"""
    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    task: str
    input_data: dict[str, Any] = {}
    output: Optional[dict[str, Any]] = None
    status: AgentStatus = AgentStatus.CREATED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


# ============ Tool Models ============

class ToolDefinition(BaseModel):
    """Tool definition schema"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    type: ToolType
    schema: dict[str, Any]
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ToolExecution(BaseModel):
    """Tool execution record"""
    id: UUID = Field(default_factory=uuid4)
    tool_id: UUID
    agent_id: UUID
    input_data: dict[str, Any]
    output: Optional[dict[str, Any]] = None
    status: str = "pending"
    error: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)


# ============ Memory Models ============

class MemoryEntry(BaseModel):
    """Memory entry for agent storage"""
    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    content: str
    embedding: Optional[list[float]] = None
    memory_type: str = "short_term"  # short_term, long_term, knowledge
    metadata: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemorySearchResult(BaseModel):
    """Memory search result"""
    entry: MemoryEntry
    similarity: float


# ============ Governance Models ============

class User(BaseModel):
    """User model for RBAC"""
    id: UUID = Field(default_factory=uuid4)
    username: str
    email: str
    role: PermissionLevel = PermissionLevel.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Permission(BaseModel):
    """Permission assignment"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    resource_type: str  # agent, tool, memory
    resource_id: UUID
    level: PermissionLevel
    granted_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(BaseModel):
    """Audit log entry"""
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID]
    action: str
    resource_type: str
    resource_id: Optional[UUID]
    details: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============ Workflow Models ============

class WorkflowStep(BaseModel):
    """Workflow step definition"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    agent_id: Optional[UUID]
    tool_id: Optional[UUID]
    input_mapping: dict[str, str] = {}
    output_mapping: dict[str, str] = {}
    on_error: str = "stop"  # stop, continue, retry


class Workflow(BaseModel):
    """Workflow definition"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str]
    steps: list[WorkflowStep]
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
