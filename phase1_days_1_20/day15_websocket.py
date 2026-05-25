"""
Day 15: WebSockets - Real-Time Agent Communication
====================================================
Skill: WebSockets for Real-Time
Mini Project: Agent Chat Room with WebSocket

Agents need to communicate in real-time. WebSockets provide the
"nervous system" for AgentOS.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set
import uuid

# Note: Run with: pip install websockets
# Then: python day15_websocket.py

# In-memory storage for connected agents
class AgentRegistry:
    """Manages connected agents via WebSocket"""

    def __init__(self):
        self.agents: Dict[str, dict] = {}
        self.connections: Dict[str, Set] = {}  # agent_id -> set of websocket connections
        self.message_history: list = []

    def register_agent(self, agent_id: str, name: str, role: str = "user") -> dict:
        """Register a new agent in the registry"""
        agent = {
            "id": agent_id,
            "name": name,
            "role": role,
            "status": "connected",
            "connected_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        self.agents[agent_id] = agent
        self.connections[agent_id] = set()
        return agent

    def disconnect_agent(self, agent_id: str):
        """Handle agent disconnection"""
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "disconnected"
            self.agents[agent_id]["disconnected_at"] = datetime.now().isoformat()
            self.connections[agent_id].clear()

    def add_connection(self, agent_id: str, websocket):
        """Add a WebSocket connection for an agent"""
        if agent_id not in self.connections:
            self.connections[agent_id] = set()
        self.connections[agent_id].add(websocket)
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "connected"
            self.agents[agent_id]["last_seen"] = datetime.now().isoformat()

    def remove_connection(self, agent_id: str, websocket):
        """Remove a WebSocket connection"""
        if agent_id in self.connections:
            self.connections[agent_id].discard(websocket)
            if not self.connections[agent_id]:
                self.disconnect_agent(agent_id)

    async def broadcast_to_agent(self, agent_id: str, message: dict):
        """Send message to specific agent"""
        if agent_id in self.connections:
            for ws in self.connections[agent_id]:
                try:
                    await ws.send(json.dumps(message))
                except Exception as e:
                    print(f"Error sending to {agent_id}: {e}")

    async def broadcast_to_all(self, message: dict, exclude: set = None):
        """Broadcast message to all connected agents"""
        exclude = exclude or set()
        for agent_id, connections in self.connections.items():
            if agent_id in exclude:
                continue
            for ws in connections:
                try:
                    await ws.send(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting to {agent_id}: {e}")

    def log_message(self, from_agent: str, to_agent: str, content: str):
        """Log message to history"""
        msg = {
            "id": str(uuid.uuid4()),
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.message_history.append(msg)
        return msg


# Global registry
registry = AgentRegistry()


# WebSocket message handlers
class MessageType:
    """Message type constants"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    CHAT = "chat"
    BROADCAST = "broadcast"
    STATUS = "status"
    ERROR = "error"
    ACK = "ack"


async def handle_client(websocket, path):
    """Handle WebSocket client connections"""
    client_agent_id = None

    try:
        # Wait for connection message
        connect_msg = await websocket.recv()
        data = json.loads(connect_msg)

        if data.get("type") == MessageType.CONNECT:
            agent_id = data.get("agent_id", f"agent-{uuid.uuid4().hex[:6]}")
            name = data.get("name", "Anonymous")
            role = data.get("role", "user")

            client_agent_id = agent_id
            registry.register_agent(agent_id, name, role)
            registry.add_connection(agent_id, websocket)

            # Send acknowledgment
            await websocket.send(json.dumps({
                "type": MessageType.ACK,
                "agent_id": agent_id,
                "status": "connected",
                "message": f"Welcome, {name}!"
            }))

            # Notify others
            await registry.broadcast_to_all({
                "type": MessageType.STATUS,
                "message": f"{name} has joined",
                "timestamp": datetime.now().isoformat()
            }, exclude={agent_id})

            print(f"[+] Agent connected: {name} ({agent_id})")

            # Handle incoming messages
            async for raw_msg in websocket:
                try:
                    msg_data = json.loads(raw_msg)
                    msg_type = msg_data.get("type")

                    if msg_type == MessageType.CHAT:
                        # Direct message to agent
                        to_agent = msg_data.get("to")
                        content = msg_data.get("content", "")

                        if to_agent:
                            # Send to specific agent
                            await registry.broadcast_to_agent(to_agent, {
                                "type": MessageType.CHAT,
                                "from": agent_id,
                                "from_name": name,
                                "to": to_agent,
                                "content": content,
                                "timestamp": datetime.now().isoformat()
                            })

                            # Log message
                            registry.log_message(agent_id, to_agent, content)

                            # Acknowledge sent
                            await websocket.send(json.dumps({
                                "type": MessageType.ACK,
                                "message": "Message delivered"
                            }))

                    elif msg_type == MessageType.BROADCAST:
                        # Broadcast to all
                        content = msg_data.get("content", "")
                        await registry.broadcast_to_all({
                            "type": MessageType.BROADCAST,
                            "from": agent_id,
                            "from_name": name,
                            "content": content,
                            "timestamp": datetime.now().isoformat()
                        }, exclude={agent_id})

                        registry.log_message(agent_id, "ALL", content)

                    elif msg_type == MessageType.STATUS:
                        # Update status
                        status = msg_data.get("status", "active")
                        if agent_id in registry.agents:
                            registry.agents[agent_id]["status"] = status
                            await registry.broadcast_to_all({
                                "type": MessageType.STATUS,
                                "agent_id": agent_id,
                                "status": status,
                                "timestamp": datetime.now().isoformat()
                            }, exclude={agent_id})

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": MessageType.ERROR,
                        "message": "Invalid JSON"
                    }))

    except Exception as e:
        print(f"[-] Error: {e}")

    finally:
        if client_agent_id:
            registry.remove_connection(client_agent_id, websocket)
            agent_name = registry.agents.get(client_agent_id, {}).get("name", "Unknown")
            print(f"[-] Agent disconnected: {agent_name}")


async def start_websocket_server():
    """Start WebSocket server"""
    print("=" * 70)
    print("AgentOS WebSocket Server")
    print("=" * 70)
    print("\nStarting WebSocket server on ws://localhost:8765")
    print("\nTo test, use JavaScript client or websocat:")
    print("  echo '{\"type\":\"connect\",\"name\":\"Test\",\"role\":\"user\"}' | websocat ws://localhost:8765")
    print("\nMessage types:")
    print("  - connect: Establish connection")
    print("  - chat: Send direct message")
    print("  - broadcast: Send to all")
    print("  - status: Update agent status")
    print("=" * 70)

    async with asynciowebsockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever


# Demo functions
async def demo_client_simulation():
    """Simulate client interactions"""
    import asyncio

    async def simulate_agent(name: str, delay: float):
        await asyncio.sleep(delay)
        print(f"  [{name}] Would connect and communicate...")

    print("\nSimulating agent connections...")
    await asyncio.gather(
        simulate_agent("Agent-Alice", 0.5),
        simulate_agent("Agent-Bob", 1.0),
        simulate_agent("Agent-Charlie", 1.5),
    )


def demo_usage():
    """Show how to use the WebSocket server"""
    print("=" * 70)
    print("AgentOS WebSocket - Real-Time Communication")
    print("=" * 70)
    print("\nThis module provides WebSocket-based real-time communication")
    print("for AgentOS agents.")
    print("\nUsage:")
    print("  1. Run server: python -m websockets day15_websocket:start_websocket_server")
    print("  2. Connect agents via WebSocket protocol")
    print("\nFeatures:")
    print("  - Real-time message delivery")
    print("  - Agent registration & status tracking")
    print("  - Direct messaging between agents")
    print("  - Broadcast to all agents")
    print("  - Message history logging")
    print("\nMessage Format:")
    print('  {"type": "connect", "agent_id": "A1", "name": "Alice", "role": "user"}')
    print('  {"type": "chat", "to": "A2", "content": "Hello!"}')
    print('  {"type": "broadcast", "content": "Hello everyone!"}')


if __name__ == "__main__":
    try:
        import websockets
        print("Starting WebSocket server...")
        asyncio.run(start_websocket_server())
    except ImportError:
        print("websockets package not installed. Showing demo instead.")
        demo_usage()
        asyncio.run(demo_client_simulation())