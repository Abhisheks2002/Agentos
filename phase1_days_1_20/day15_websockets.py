"""
Day 15: WebSockets - Real-Time Agent Communication
===================================================
Skill: Real-Time Communication
Mini Project: Live Agent Chat Hub

WebSockets enable agents to communicate in real-time - essential for
multi-agent systems and live dashboards.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum

# Note: Run with: pip install fastapi uvicorn websockets
# Then: uvicorn day15_websockets:app --reload

app = FastAPI(title="AgentOS WebSocket Hub")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageType(str, Enum):
    """Message types for WebSocket communication"""
    JOIN = "join"
    LEAVE = "leave"
    CHAT = "chat"
    AGENT_STATUS = "agent_status"
    TOOL_RESULT = "tool_result"
    HEARTBEAT = "heartbeat"


class ConnectionManager:
    """Manages WebSocket connections for agents"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_rooms: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and track a new connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """Remove a connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        # Remove from all rooms
        for room in self.agent_rooms.values():
            if client_id in room:
                room.remove(client_id)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: Dict[str, Any], room: str = None):
        """Broadcast message to all or specific room"""
        if room and room in self.agent_rooms:
            targets = self.agent_rooms[room]
        else:
            targets = list(self.active_connections.keys())

        for client_id in targets:
            if client_id in self.active_connections:
                await self.active_connections[client_id].send_text(
                    json.dumps(message)
                )

    def join_room(self, client_id: str, room: str):
        """Add client to a room"""
        if room not in self.agent_rooms:
            self.agent_rooms[room] = []
        if client_id not in self.agent_rooms[room]:
            self.agent_rooms[room].append(client_id)

    def leave_room(self, client_id: str, room: str):
        """Remove client from a room"""
        if room in self.agent_rooms and client_id in self.agent_rooms[room]:
            self.agent_rooms[room].remove(client_id)


# Global connection manager
manager = ConnectionManager()

# Agent state storage
agents: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AgentOS WebSocket Hub",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/{client_id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "agents": len(agents)
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Main WebSocket endpoint for real-time agent communication

    Client sends messages like:
    {
        "type": "join",
        "agent_id": "agent_123",
        "room": "general"
    }

    Or:
    {
        "type": "chat",
        "content": "Hello agents!",
        "room": "general"
    }
    """
    await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "welcome",
            "client_id": client_id,
            "message": "Connected to AgentOS WebSocket Hub",
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Send current agents list
        await manager.send_personal_message({
            "type": "agents_list",
            "agents": list(agents.keys()),
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            await handle_message(client_id, message)

    except WebSocketDisconnect:
        # Handle disconnect
        await handle_disconnect(client_id)
    except Exception as e:
        print(f"Error: {e}")
        await handle_disconnect(client_id)


async def handle_message(client_id: str, message: Dict[str, Any]):
    """Process incoming WebSocket messages"""
    msg_type = message.get("type")

    if msg_type == MessageType.JOIN:
        # Agent joins
        agent_id = message.get("agent_id", client_id)
        room = message.get("room", "general")

        # Store or update agent
        agents[agent_id] = {
            "id": agent_id,
            "client_id": client_id,
            "room": room,
            "status": "online",
            "joined_at": datetime.now().isoformat()
        }

        manager.join_room(client_id, room)

        # Notify others
        await manager.broadcast({
            "type": MessageType.AGENT_STATUS,
            "agent_id": agent_id,
            "status": "joined",
            "room": room,
            "timestamp": datetime.now().isoformat()
        }, room)

    elif msg_type == MessageType.CHAT:
        # Chat message
        room = message.get("room", "general")
        content = message.get("content", "")
        agent_id = message.get("agent_id", "unknown")

        # Broadcast to room
        await manager.broadcast({
            "type": MessageType.CHAT,
            "agent_id": agent_id,
            "content": content,
            "room": room,
            "timestamp": datetime.now().isoformat()
        }, room)

    elif msg_type == MessageType.TOOL_RESULT:
        # Tool execution result
        room = message.get("room", "general")
        tool_name = message.get("tool_name", "unknown")
        result = message.get("result", {})

        await manager.broadcast({
            "type": MessageType.TOOL_RESULT,
            "tool_name": tool_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }, room)

    elif msg_type == MessageType.HEARTBEAT:
        # Heartbeat/ping
        agent_id = message.get("agent_id")
        if agent_id and agent_id in agents:
            agents[agent_id]["last_heartbeat"] = datetime.now().isoformat()
            await manager.send_personal_message({
                "type": "heartbeat_ack",
                "timestamp": datetime.now().isoformat()
            }, manager.active_connections[client_id])


async def handle_disconnect(client_id: str):
    """Handle client disconnection"""
    manager.disconnect(client_id)

    # Find and update any agents owned by this client
    disconnected_agents = [
        agent_id for agent_id, agent in agents.items()
        if agent["client_id"] == client_id
    ]

    for agent_id in disconnected_agents:
        old_room = agents[agent_id]["room"]
        agents[agent_id]["status"] = "offline"

        # Notify room
        await manager.broadcast({
            "type": MessageType.AGENT_STATUS,
            "agent_id": agent_id,
            "status": "disconnected",
            "room": old_room,
            "timestamp": datetime.now().isoformat()
        }, old_room)


# Example: Trigger agent action via REST (for integration)
class AgentAction(BaseModel):
    agent_id: str
    action: str
    params: Dict[str, Any] = {}


@app.post("/api/agent/action")
async def trigger_agent_action(action: AgentAction):
    """Trigger an action on an agent via WebSocket"""
    if action.agent_id not in agents:
        return {"error": "Agent not found"}, 404

    agent = agents[action.agent_id]

    # Send action to agent via WebSocket
    if agent["client_id"] in manager.active_connections:
        await manager.send_personal_message({
            "type": "action",
            "action": action.action,
            "params": action.params,
            "timestamp": datetime.now().isoformat()
        }, manager.active_connections[agent["client_id"]])

        return {"status": "sent", "agent_id": action.agent_id}

    return {"error": "Agent not connected"}, 400


@app.get("/api/agents")
async def list_agents():
    """List all registered agents"""
    return {
        "agents": [
            {
                "id": agent_id,
                "status": agent["status"],
                "room": agent["room"],
                "joined_at": agent["joined_at"]
            }
            for agent_id, agent in agents.items()
        ]
    }


def demo_instructions():
    """Show demo instructions"""
    print("=" * 70)
    print("AgentOS WebSocket Hub - Real-Time Communication")
    print("=" * 70)
    print("\nTo run:")
    print("  pip install fastapi uvicorn websockets")
    print("  uvicorn day15_websockets:app --reload")
    print("\nTo test, use WebSocket client to connect to:")
    print("  ws://localhost:8000/ws/client_123")
    print("\nExample message to join:")
    print('  {"type": "join", "agent_id": "agent_001", "room": "general"}')
    print("\nExample chat message:")
    print('  {"type": "chat", "content": "Hello!", "room": "general"}')


if __name__ == "__main__":
    demo_instructions()