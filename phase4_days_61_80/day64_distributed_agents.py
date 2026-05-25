"""
Day 64: Distributed Agent Coordination
======================================
Coordinating multiple agents across distributed systems.

Key Concepts:
- Agent discovery
- Load balancing
- Message passing
- Consensus mechanisms
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio


class AgentStatus(Enum):
    """Distributed agent status"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentNode:
    """A node in the distributed system"""
    node_id: str
    agent_id: str
    address: str
    port: int
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    last_heartbeat: datetime = field(default_factory=datetime.now)


@dataclass
class Message:
    """Message between agents"""
    message_id: str
    from_node: str
    to_node: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


class DistributedAgentCoordinator:
    """
    Distributed Agent Coordinator
    =============================

    Coordinates multiple agents across distributed nodes.
    """

    def __init__(self):
        self.nodes: Dict[str, AgentNode] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.handlers: Dict[str, Callable] = {}

    def register_node(
        self,
        agent_id: str,
        address: str,
        port: int,
        capabilities: List[str] = None
    ) -> AgentNode:
        """Register a new agent node"""
        node_id = f"node_{uuid.uuid4().hex[:8]}"

        node = AgentNode(
            node_id=node_id,
            agent_id=agent_id,
            address=address,
            port=port,
            capabilities=capabilities or []
        )

        self.nodes[node_id] = node
        return node

    def unregister_node(self, node_id: str) -> bool:
        """Unregister a node"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False

    def find_available_node(self, capability: str = None) -> Optional[AgentNode]:
        """Find an available node"""
        available = [
            n for n in self.nodes.values()
            if n.status == AgentStatus.IDLE
        ]

        if capability:
            available = [n for n in available if capability in n.capabilities]

        if not available:
            return None

        # Simple round-robin or first available
        return available[0]

    async def send_message(
        self,
        from_node: str,
        to_node: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> Message:
        """Send a message between nodes"""
        message = Message(
            message_id=str(uuid.uuid4()),
            from_node=from_node,
            to_node=to_node,
            message_type=message_type,
            payload=payload
        )

        await self.message_queue.put(message)

        # Handle message
        if message_type in self.handlers:
            handler = self.handlers[message_type]
            await handler(message)

        return message

    async def broadcast(
        self,
        from_node: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> List[Message]:
        """Broadcast message to all nodes"""
        messages = []

        for node_id in self.nodes:
            if node_id != from_node:
                msg = await self.send_message(
                    from_node,
                    node_id,
                    message_type,
                    payload
                )
                messages.append(msg)

        return messages

    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.handlers[message_type] = handler

    def get_node_status(self) -> List[Dict]:
        """Get status of all nodes"""
        return [
            {
                "node_id": n.node_id,
                "agent_id": n.agent_id,
                "status": n.status.value,
                "capabilities": n.capabilities,
                "current_task": n.current_task,
                "last_heartbeat": n.last_heartbeat.isoformat()
            }
            for n in self.nodes.values()
        ]

    def update_heartbeat(self, node_id: str):
        """Update node heartbeat"""
        if node_id in self.nodes:
            self.nodes[node_id].last_heartbeat = datetime.now()


# Demo
async def main():
    print("=" * 60)
    print("Day 64: Distributed Agent Coordination")
    print("=" * 60)

    coordinator = DistributedAgentCoordinator()

    # Register nodes
    node1 = coordinator.register_node(
        "agent_001", "192.168.1.10", 8001,
        ["analysis", "data_processing"]
    )
    node2 = coordinator.register_node(
        "agent_002", "192.168.1.11", 8001,
        ["web_search", "data_processing"]
    )
    node3 = coordinator.register_node(
        "agent_003", "192.168.1.12", 8001,
        ["file_operations"]
    )

    print(f"\nRegistered nodes: {len(coordinator.nodes)}")

    # Find available node
    available = coordinator.find_available_node("data_processing")
    if available:
        print(f"Available node: {available.node_id} ({available.agent_id})")

    # Send message
    print("\nSending message between nodes...")
    msg = await coordinator.send_message(
        node1.node_id,
        node2.node_id,
        "task_request",
        {"task": "analyze_data", "data": [1, 2, 3]}
    )
    print(f"Message sent: {msg.message_type} - {msg.message_id}")

    # Broadcast
    print("\nBroadcasting to all nodes...")
    messages = await coordinator.broadcast(
        node1.node_id,
        "system_notification",
        {"message": "System update in 5 minutes"}
    )
    print(f"Broadcast to {len(messages)} nodes")

    # Node status
    print("\n" + "-" * 40)
    print("Node Status:")
    for status in coordinator.get_node_status():
        print(f"  {status['node_id']}: {status['agent_id']} - {status['status']}")


if __name__ == "__main__":
    asyncio.run(main())