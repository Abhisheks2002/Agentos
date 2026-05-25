"""
Day 27: Agent Communication Protocols
======================================
Skill: Agent Communication
Mini Project: Protocol Implementation

Standardized communication patterns for multi-agent systems.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import json
import uuid


class MessageType(str, Enum):
    """Types of messages agents can send"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    QUERY = "query"
    BROADCAST = "broadcast"
    ERROR = "error"


class Priority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """Standardized message format for agent communication"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receivers: List[str] = field(default_factory=list)
    message_type: MessageType = MessageType.REQUEST
    priority: Priority = Priority.NORMAL
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "sender": self.sender,
            "receivers": self.receivers,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentMessage':
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            sender=data.get("sender", ""),
            receivers=data.get("receivers", []),
            message_type=MessageType(data.get("message_type", "request")),
            priority=Priority(data.get("priority", "normal")),
            content=data.get("content"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to")
        )


class MessageHandler(ABC):
    """Abstract message handler"""

    @abstractmethod
    async def handle(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle incoming message"""
        pass


class AgentProtocol:
    """Base protocol for agent communication"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.handlers: Dict[MessageType, List[MessageHandler]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.sent_messages: List[AgentMessage] = []
        self.received_messages: List[AgentMessage] = []

    def register_handler(self, msg_type: MessageType, handler: MessageHandler):
        """Register a message handler"""
        if msg_type not in self.handlers:
            self.handlers[msg_type] = []
        self.handlers[msg_type].append(handler)

    async def send_message(
        self,
        receiver: str,
        content: Any,
        msg_type: MessageType = MessageType.REQUEST,
        priority: Priority = Priority.NORMAL,
        correlation_id: Optional[str] = None
    ) -> AgentMessage:
        """Send a message to another agent"""
        message = AgentMessage(
            sender=self.agent_id,
            receivers=[receiver],
            message_type=msg_type,
            priority=priority,
            content=content,
            correlation_id=correlation_id
        )

        self.sent_messages.append(message)
        await self._transmit(message)
        return message

    async def broadcast(
        self,
        content: Any,
        receivers: List[str],
        msg_type: MessageType = MessageType.BROADCAST
    ) -> AgentMessage:
        """Broadcast to multiple agents"""
        message = AgentMessage(
            sender=self.agent_id,
            receivers=receivers,
            message_type=msg_type,
            content=content
        )

        self.sent_messages.append(message)
        await self._transmit(message)
        return message

    async def receive_message(self, message: AgentMessage):
        """Receive and process a message"""
        self.received_messages.append(message)

        # Route to handlers
        handlers = self.handlers.get(message.message_type, [])
        for handler in handlers:
            response = await handler.handle(message)
            if response:
                await self._transmit(response)

    async def _transmit(self, message: AgentMessage):
        """Simulate message transmission"""
        await asyncio.sleep(0.01)  # Simulate network latency

    def get_messages(self, msg_type: Optional[MessageType] = None) -> List[AgentMessage]:
        """Get received messages, optionally filtered by type"""
        if msg_type:
            return [m for m in self.received_messages if m.message_type == msg_type]
        return self.received_messages


class RequestResponseProtocol(AgentProtocol):
    """Request-Response pattern"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.pending_requests: Dict[str, asyncio.Future] = {}

    async def request(
        self,
        receiver: str,
        content: Any,
        timeout: float = 30.0
    ) -> Optional[AgentMessage]:
        """Send request and wait for response"""
        correlation_id = str(uuid.uuid4())
        message = await self.send_message(
            receiver=receiver,
            content=content,
            msg_type=MessageType.REQUEST,
            correlation_id=correlation_id
        )

        # Create future for response
        future = asyncio.Future()
        self.pending_requests[correlation_id] = future

        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            del self.pending_requests[correlation_id]
            return None

    async def handle_response(self, message: AgentMessage):
        """Handle incoming response"""
        if message.correlation_id and message.correlation_id in self.pending_requests:
            future = self.pending_requests.pop(message.correlation_id)
            if not future.done():
                future.set_result(message)


class PubSubProtocol(AgentProtocol):
    """Publish-Subscribe pattern"""

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.topics: Dict[str, List[str]] = {}
        self.subscriptions: Dict[str, asyncio.Queue] = {}

    async def subscribe(self, topic: str) -> asyncio.Queue:
        """Subscribe to a topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = asyncio.Queue()

        if topic not in self.topics:
            self.topics[topic] = []

        if self.agent_id not in self.topics[topic]:
            self.topics[topic].append(self.agent_id)

        return self.subscriptions[topic]

    async def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        if topic in self.topics and self.agent_id in self.topics[topic]:
            self.topics[topic].remove(self.agent_id)

    async def publish(self, topic: str, content: Any):
        """Publish to a topic"""
        message = AgentMessage(
            sender=self.agent_id,
            receivers=self.topics.get(topic, []),
            message_type=MessageType.NOTIFICATION,
            content={"topic": topic, "data": content}
        )

        # Queue to all subscribers
        if topic in self.subscriptions:
            await self.subscriptions[topic].put(message)


# Demo
def run_demo():
    print("=" * 70)
    print("Agent Communication Protocols Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create agents with protocols
        agent_a = AgentProtocol("AgentA")
        agent_b = AgentProtocol("AgentB")

        # Send message
        print("\n[1] Basic Message")
        print("-" * 40)
        msg = await agent_a.send_message(
            receiver="AgentB",
            content={"action": "query", "data": "Hello"},
            msg_type=MessageType.QUERY
        )
        print(f"  Sent: {msg.id[:8]}...")
        print(f"  Type: {msg.message_type.value}")
        print(f"  Priority: {msg.priority.value}")

        # Request-Response
        print("\n[2] Request-Response Protocol")
        print("-" * 40)

        req_agent = RequestResponseProtocol("RequestAgent")
        resp_agent = RequestResponseProtocol("ResponseAgent")

        # Simulate response
        response = AgentMessage(
            sender="ResponseAgent",
            receivers=["RequestAgent"],
            message_type=MessageType.RESPONSE,
            content={"status": "ok"},
            correlation_id="test-id"
        )
        await req_agent.handle_response(response)
        print(f"  Request-Response communication established")

        # Publish-Subscribe
        print("\n[3] Publish-Subscribe Protocol")
        print("-" * 40)

        pubsub = PubSubProtocol("Publisher")
        queue = await pubsub.subscribe("updates")
        await pubsub.publish("updates", {"message": "New data!"})

        # Receive
        if not queue.empty():
            msg = await queue.get()
            print(f"  Received on 'updates': {msg.content}")

        print("\n  Message formats:")
        print(f"  - JSON: {json.dumps(msg.to_dict(), indent=2)[:100]}...")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()