"""
Day 14: FastAPI - The Gateway to AgentOS
==========================================
Skill: Web Frameworks for AI
Mini Project: REST API with LLM integration

Agents will communicate over HTTP. FastAPI is the fastest way to
build these "nerves."
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime
import asyncio

# Note: Run with: pip install fastapi uvicorn
# Then: uvicorn day14_fastapi_gateway:app --reload

app = FastAPI(
    title="AgentOS API",
    description="The Gateway to AgentOS - Manage agents, memory, and tools",
    version="1.0.0"
)

# In-memory storage (use database in production)
agents_db = {}
messages_db = []

# Request/Response models
class AgentCreate(BaseModel):
    name: str
    role: str = "user"
    system_prompt: Optional[str] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    status: str
    created_at: str

class MessageRequest(BaseModel):
    agent_id: str
    content: str

class MessageResponse(BaseModel):
    id: str
    agent_id: str
    content: str
    response: str
    timestamp: str

class SpawnAgentRequest(BaseModel):
    name: str
    role: str = "user"
    personality: Optional[str] = None

class LLMRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = "You are a helpful assistant."
    model: str = "gpt-4o-mini"
    temperature: float = 0.7

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AgentOS API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_count": len(agents_db)
    }

@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(request: AgentCreate):
    """Create a new agent"""
    agent_id = f"AGENT-{uuid.uuid4().hex[:6].upper()}"

    agent = {
        "id": agent_id,
        "name": request.name,
        "role": request.role,
        "status": "active",
        "system_prompt": request.system_prompt,
        "created_at": datetime.now().isoformat()
    }

    agents_db[agent_id] = agent

    return AgentResponse(**agent)

@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents():
    """List all agents"""
    return [AgentResponse(**agent) for agent in agents_db.values()]

@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(**agents_db[agent_id])

@app.post("/api/agents/{agent_id}/pause")
async def pause_agent(agent_id: str):
    """Pause an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")

    agents_db[agent_id]["status"] = "paused"
    return {"status": "paused", "agent_id": agent_id}

@app.post("/api/agents/{agent_id}/resume")
async def resume_agent(agent_id: str):
    """Resume an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")

    agents_db[agent_id]["status"] = "active"
    return {"status": "active", "agent_id": agent_id}

@app.post("/api/spawn_agent")
async def spawn_agent(request: SpawnAgentRequest):
    """
    Spawn Agent Endpoint - Creates and configures a new agent
    This is the main entry point for agent creation
    """
    agent_id = f"AGENT-{uuid.uuid4().hex[:6].upper()}"

    agent = {
        "id": agent_id,
        "name": request.name,
        "role": request.role,
        "personality": request.personality,
        "status": "initialized",
        "created_at": datetime.now().isoformat()
    }

    agents_db[agent_id] = agent

    return {
        "success": True,
        "agent_id": agent_id,
        "message": f"Agent '{request.name}' spawned successfully"
    }

@app.post("/api/llm/generate")
async def generate_with_llm(request: LLMRequest):
    """
    Simple LLM integration endpoint
    In production, integrate with OpenAI/Anthropic API
    """
    # Simulate LLM response
    await asyncio.sleep(0.1)  # Simulate API delay

    response_text = f"Response to: {request.prompt[:50]}..."

    return {
        "prompt": request.prompt,
        "response": response_text,
        "model": request.model,
        "tokens_used": len(request.prompt.split()) * 1.3
    }

@app.get("/api/messages")
async def get_messages(agent_id: Optional[str] = None):
    """Get messages, optionally filtered by agent"""
    if agent_id:
        return [m for m in messages_db if m["agent_id"] == agent_id]
    return messages_db

def demo_startup():
    """Show how to run the server"""
    print("=" * 70)
    print("AgentOS FastAPI Gateway")
    print("=" * 70)
    print("\nTo run the API server:")
    print("  1. Install dependencies: pip install fastapi uvicorn")
    print("  2. Run server: uvicorn day14_fastapi_gateway:app --reload")
    print("  3. Open: http://localhost:8000/docs")
    print("\nAvailable endpoints:")
    print("  GET  /                    - Root")
    print("  GET  /health              - Health check")
    print("  POST /api/agents          - Create agent")
    print("  GET  /api/agents          - List agents")
    print("  POST /api/spawn_agent     - Spawn new agent")
    print("  POST /api/llm/generate     - Generate with LLM")

if __name__ == "__main__":
    demo_startup()