"""REST API Server for AgentOS."""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uvicorn
import logging

from ..runtime.runtime import get_runtime, AgentRuntime
from ..memory.memory import get_memory_manager, MemoryManager
from ..tools.registry import get_tool_registry, ToolRegistry
from ..governance.governance import get_governance_engine, GovernanceEngine, Permission
from ..models.models import Agent, AgentType, AgentStatus, Task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AgentOS API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Dependencies ---

def get_services():
    """Get all service instances."""
    return {
        "runtime": get_runtime(),
        "memory": get_memory_manager(),
        "tools": get_tool_registry(),
        "governance": get_governance_engine()
    }


# --- Request/Response Models ---

class CreateAgentRequest(BaseModel):
    name: str
    agent_type: AgentType = AgentType.CHAT
    description: Optional[str] = None
    config: Dict[str, Any] = {}
    tools: List[str] = []


class RunTaskRequest(BaseModel):
    agent_id: str
    input_data: Dict[str, Any] = {}


class StoreMemoryRequest(BaseModel):
    agent_id: str
    content: str
    memory_type: str = "short_term"
    metadata: Dict[str, Any] = {}


class SearchMemoryRequest(BaseModel):
    agent_id: str
    query: str
    limit: int = 5
    memory_type: Optional[str] = None


class RegisterToolRequest(BaseModel):
    name: str
    tool_type: str = "custom"
    description: Optional[str] = None
    schema: Dict[str, Any] = {}


class ExecuteToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}
    context: Dict[str, Any] = {}


# --- Agent Endpoints ---

@app.post("/agents/create", response_model=Agent)
async def create_agent(
    request: CreateAgentRequest,
    services: Dict = Depends(get_services)
):
    """Create a new agent."""
    runtime: AgentRuntime = services["runtime"]

    agent = await runtime.create_agent(
        name=request.name,
        agent_type=request.agent_type,
        description=request.description,
        config=request.config,
        tools=request.tools
    )

    return agent


@app.get("/agents", response_model=List[Agent])
async def list_agents(
    status: Optional[AgentStatus] = None,
    services: Dict = Depends(get_services)
):
    """List all agents."""
    runtime: AgentRuntime = services["runtime"]
    return await runtime.list_agents(status=status)


@app.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    services: Dict = Depends(get_services)
):
    """Get agent by ID."""
    runtime: AgentRuntime = services["runtime"]
    agent = await runtime.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.post("/agents/run", response_model=Task)
async def run_agent_task(
    request: RunTaskRequest,
    services: Dict = Depends(get_services)
):
    """Run a task with an agent."""
    runtime: AgentRuntime = services["runtime"]

    # Create and execute task
    task = await runtime.create_task(
        agent_id=request.agent_id,
        input_data=request.input_data
    )

    # Execute synchronously
    result = await runtime.execute_task(task.id)

    task = await runtime.get_task_status(task.id)
    return task


@app.get("/agents/status/{agent_id}")
async def get_agent_status(
    agent_id: str,
    services: Dict = Depends(get_services)
):
    """Get agent status."""
    runtime: AgentRuntime = services["runtime"]
    agent = await runtime.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent_id": agent.id,
        "name": agent.name,
        "status": agent.status.value,
        "type": agent.type.value
    }


@app.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    services: Dict = Depends(get_services)
):
    """Delete an agent."""
    runtime: AgentRuntime = services["runtime"]
    success = await runtime.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "deleted", "agent_id": agent_id}


# --- Memory Endpoints ---

@app.post("/memory/store")
async def store_memory(
    request: StoreMemoryRequest,
    services: Dict = Depends(get_services)
):
    """Store a memory."""
    memory: MemoryManager = services["memory"]

    if request.memory_type == "short_term":
        memory_id = await memory.add_short_term(
            agent_id=request.agent_id,
            content=request.content,
            metadata=request.metadata
        )
    elif request.memory_type == "long_term":
        memory_id = await memory.add_long_term(
            agent_id=request.agent_id,
            content=request.content,
            metadata=request.metadata
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid memory type")

    return {"memory_id": memory_id, "agent_id": request.agent_id}


@app.get("/memory/{agent_id}")
async def get_memory(
    agent_id: str,
    memory_type: str = "short_term",
    limit: int = 10,
    services: Dict = Depends(get_services)
):
    """Get memories for an agent."""
    memory: MemoryManager = services["memory"]

    if memory_type == "short_term":
        memories = await memory.get_short_term(agent_id, limit=limit)
    elif memory_type == "long_term":
        memories = await memory.get_long_term(agent_id, limit=limit)
    else:
        raise HTTPException(status_code=400, detail="Invalid memory type")

    return {"agent_id": agent_id, "memories": memories}


@app.post("/memory/search")
async def search_memory(
    request: SearchMemoryRequest,
    services: Dict = Depends(get_services)
):
    """Search memories semantically."""
    memory: MemoryManager = services["memory"]

    results = await memory.search(
        agent_id=request.agent_id,
        query=request.query,
        limit=request.limit,
        memory_type=request.memory_type
    )

    return {"results": results}


# --- Tool Endpoints ---

@app.post("/tools/register")
async def register_tool(
    request: RegisterToolRequest,
    services: Dict = Depends(get_services)
):
    """Register a new tool."""
    tools: ToolRegistry = services["tools"]

    tool = await tools.register_tool(
        name=request.name,
        tool_type=request.tool_type,
        description=request.description,
        schema=request.schema
    )

    return tool


@app.get("/tools", response_model=List)
async def list_tools(
    services: Dict = Depends(get_services)
):
    """List all tools."""
    tools: ToolRegistry = services["tools"]
    tool_list = await tools.list_tools()
    return [{"id": t.id, "name": t.name, "type": t.type.value, "enabled": t.enabled}
            for t in tool_list]


@app.post("/tools/execute")
async def execute_tool(
    request: ExecuteToolRequest,
    services: Dict = Depends(get_services)
):
    """Execute a tool."""
    tools: ToolRegistry = services["tools"]

    result = await tools.execute(
        tool_name=request.tool_name,
        parameters=request.parameters,
        context=request.context
    )

    return result


# --- Health Check ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AgentOS API"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AgentOS",
        "version": "0.1.0",
        "docs": "/docs"
    }


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    logger.info(f"Starting AgentOS API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
