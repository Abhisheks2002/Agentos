"""
Day 91: Advanced Agent Communication Protocols
================================================

Implementing advanced communication protocols for next-generation agent networks
including secure messaging, protocol negotiation, and intelligent routing.

Key Concepts:
- Protocol Negotiation
- Message Encryption
- Protocol Adapters
- Intelligent Routing
- Protocol Versioning
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import hashlib
import json


class ProtocolType(Enum):
    """Supported Protocol Types"""
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    MQTT = "mqtt"
    AMQP = "amqp"
    CUSTOM = "custom"
    QUANTUM = "quantum"


class MessagePriority(Enum):
    """Message Priority Levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BULK = 5


class ProtocolVersion(Enum):
    """Protocol Versions"""
    V1 = "1.0"
    V2 = "2.0"
    V3 = "3.0"


@dataclass
class MessageHeader:
    """Message Header"""
    message_id: str
    sender_id: str
    receiver_id: str
    timestamp: datetime
    priority: MessagePriority
    protocol: ProtocolType
    version: ProtocolVersion
    content_type: str
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl_seconds: int = 300
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class Message:
    """Agent Message"""
    header: MessageHeader
    payload: Any
    signature: Optional[str] = None
    encryption: Optional[str] = None


@dataclass
class ProtocolCapability:
    """Protocol Capability"""
    protocol: ProtocolType
    version: ProtocolVersion
    features: Set[str]
    max_message_size: int
    supports_streaming: bool
    supports_batching: bool


@dataclass
class NegotiationResult:
    """Protocol Negotiation Result"""
    agreed_protocol: ProtocolType
    agreed_version: ProtocolVersion
    features: Set[str]
    session_id: str


class ProtocolRegistry:
    """Registry of supported protocols"""

    def __init__(self):
        self.protocols: Dict[ProtocolType, ProtocolCapability] = {}
        self._register_protocols()

    def _register_protocols(self):
        """Register default protocols"""
        self.protocols[ProtocolType.HTTP] = ProtocolCapability(
            protocol=ProtocolType.HTTP,
            version=ProtocolVersion.V2,
            features={"compression", "keep-alive", "streaming"},
            max_message_size=10_000_000,
            supports_streaming=True,
            supports_batching=True
        )
        self.protocols[ProtocolType.WEBSOCKET] = ProtocolCapability(
            protocol=ProtocolType.WEBSOCKET,
            version=ProtocolVersion.V3,
            features={"bidirectional", "compression", "heartbeat"},
            max_message_size=10_000_000,
            supports_streaming=True,
            supports_batching=False
        )
        self.protocols[ProtocolType.GRPC] = ProtocolCapability(
            protocol=ProtocolType.GRPC,
            version=ProtocolVersion.V2,
            features={"streaming", "bidirectional", "protobuf"},
            max_message_size=100_000_000,
            supports_streaming=True,
            supports_batching=True
        )
        self.protocols[ProtocolType.MQTT] = ProtocolCapability(
            protocol=ProtocolType.MQTT,
            version=ProtocolVersion.V5,
            features={"qos", "retain", "will"},
            max_message_size=268_435_455,
            supports_streaming=False,
            supports_batching=True
        )
        self.protocols[ProtocolType.AMQP] = ProtocolCapability(
            protocol=ProtocolType.AMQP,
            version=ProtocolVersion.V1,
            features={"transactions", "reliability", "routing"},
            max_message_size=2_147_483_647,
            supports_streaming=False,
            supports_batching=True
        )

    def get_capability(self, protocol: ProtocolType) -> Optional[ProtocolCapability]:
        """Get protocol capability"""
        return self.protocols.get(protocol)

    def list_protocols(self) -> List[ProtocolType]:
        """List all registered protocols"""
        return list(self.protocols.keys())


class ProtocolNegotiator:
    """
    Protocol Negotiation Handler
    ============================

    Handles negotiation between agents for protocol selection.
    """

    def __init__(self, registry: ProtocolRegistry):
        self.registry = registry
        self.active_sessions: Dict[str, NegotiationResult] = {}

    async def negotiate(
        self,
        agent_a_capabilities: List[ProtocolType],
        agent_b_capabilities: List[ProtocolType]
    ) -> NegotiationResult:
        """Negotiate protocol between two agents"""
        print(f"[ProtocolNegotiator] Starting negotiation...")
        await asyncio.sleep(0.1)

        # Find common protocols
        common = set(agent_a_capabilities) & set(agent_b_capabilities)

        if not common:
            # Fall back to custom protocol
            return NegotiationResult(
                agreed_protocol=ProtocolType.CUSTOM,
                agreed_version=ProtocolVersion.V1,
                features=set(),
                session_id=str(uuid.uuid4())
            )

        # Select best protocol (prefer gRPC > WebSocket > HTTP > MQTT > AMQP)
        priority = [ProtocolType.GRPC, ProtocolType.WEBSOCKET, ProtocolType.HTTP,
                    ProtocolType.MQTT, ProtocolType.AMQP]

        agreed_protocol = None
        for p in priority:
            if p in common:
                agreed_protocol = p
                break

        if not agreed_protocol:
            agreed_protocol = list(common)[0]

        # Get common features
        capability = self.registry.get_capability(agreed_protocol)
        features = capability.features if capability else set()

        session_id = str(uuid.uuid4())
        result = NegotiationResult(
            agreed_protocol=agreed_protocol,
            agreed_version=ProtocolVersion.V3,
            features=features,
            session_id=session_id
        )

        self.active_sessions[session_id] = result

        print(f"[ProtocolNegotiator] Negotiated: {agreed_protocol.value} {ProtocolVersion.V3.value}")
        return result

    async def upgrade_protocol(
        self,
        session_id: str,
        new_protocol: ProtocolType
    ) -> NegotiationResult:
        """Upgrade protocol mid-session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session: {session_id}")

        current = self.active_sessions[session_id]
        new_capability = self.registry.get_capability(new_protocol)

        # Create upgraded result
        result = NegotiationResult(
            agreed_protocol=new_protocol,
            agreed_version=ProtocolVersion.V3,
            features=current.features | new_capability.features if new_capability else current.features,
            session_id=session_id
        )

        self.active_sessions[session_id] = result
        return result


class MessageRouter:
    """
    Intelligent Message Router
    ==========================

    Routes messages based on load, latency, and other factors.
    """

    def __init__(self):
        self.routes: Dict[str, List[str]] = {}
        self.route_metrics: Dict[str, Dict[str, Any]] = {}

    def add_route(self, agent_id: str, endpoint: str):
        """Add route for an agent"""
        if agent_id not in self.routes:
            self.routes[agent_id] = []
        if endpoint not in self.routes[agent_id]:
            self.routes[agent_id].append(endpoint)
            self.route_metrics[endpoint] = {
                "messages_sent": 0,
                "latency_ms": 0,
                "errors": 0
            }

    def route_to(
        self,
        agent_id: str,
        priority: MessagePriority,
        message_size: int
    ) -> Optional[str]:
        """Route message to best endpoint"""
        if agent_id not in self.routes:
            return None

        endpoints = self.routes[agent_id]
        if not endpoints:
            return None

        # Score each endpoint
        scores = []
        for endpoint in metrics = self.route_metrics.get(endpoint, {}):
            score = 100

            # Penalize high latency
            latency = metrics.get("latency_ms", 0)
            score -= latency * 2

            # Penalize errors
            errors = metrics.get("errors", 0)
            score -= errors * 10

            # Bonus for capacity (for high priority)
            if priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
                score += 50

            scores.append((endpoint, score))

        # Select best endpoint
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0] if scores else None

    def update_metrics(self, endpoint: str, latency_ms: float, success: bool):
        """Update routing metrics"""
        if endpoint not in self.route_metrics:
            self.route_metrics[endpoint] = {
                "messages_sent": 0,
                "latency_ms": 0,
                "errors": 0
            }

        metrics = self.route_metrics[endpoint]
        metrics["messages_sent"] += 1

        # Exponential moving average for latency
        if metrics["messages_sent"] == 1:
            metrics["latency_ms"] = latency_ms
        else:
            metrics["latency_ms"] = 0.9 * metrics["latency_ms"] + 0.1 * latency_ms

        if not success:
            metrics["errors"] += 1


class SecureMessageHandler:
    """
    Secure Message Handler
    ======================

    Handles encryption and signing of messages.
    """

    def __init__(self):
        self.keys: Dict[str, Dict[str, str]] = {}

    def generate_key_pair(self, agent_id: str) -> Dict[str, str]:
        """Generate key pair for agent"""
        # Simulated key generation
        public_key = hashlib.sha256(f"{agent_id}_public".encode()).hexdigest()
        private_key = hashlib.sha256(f"{agent_id}_private".encode()).hexdigest()

        self.keys[agent_id] = {
            "public": public_key,
            "private": private_key
        }

        return {"public": public_key, "private": private_key}

    async def encrypt_message(self, message: Message, recipient_id: str) -> Message:
        """Encrypt message for recipient"""
        # Simulated encryption
        payload_str = json.dumps(message.payload) if isinstance(message.payload, dict) else str(message.payload)
        encrypted_payload = f"ENC[{hashlib.sha256(payload_str.encode()).hexdigest()[:16]}]"

        message.payload = encrypted_payload
        message.encryption = "AES-256-GCM"

        return message

    async def sign_message(self, message: Message, sender_id: str) -> Message:
        """Sign message with sender's private key"""
        if sender_id not in self.keys:
            self.generate_key_pair(sender_id)

        payload_str = json.dumps(message.payload) if isinstance(message.payload, dict) else str(message.payload)
        signature = hashlib.sha256(f"{payload_str}{self.keys[sender_id]['private']}".encode()).hexdigest()

        message.signature = signature
        return message

    async def verify_signature(self, message: Message, sender_id: str) -> bool:
        """Verify message signature"""
        if not message.signature or sender_id not in self.keys:
            return False

        payload_str = json.dumps(message.payload) if isinstance(message.payload, dict) else str(message.payload)
        expected = hashlib.sha256(f"{payload_str}{self.keys[sender_id]['private']}".encode()).hexdigest()

        return message.signature == expected


class ProtocolAdapter:
    """
    Protocol Adapter
    ===============

    Adapts between different protocols.
    """

    def __init__(self):
        self.translators: Dict[tuple, callable] = {}

    def register_translator(
        self,
        source: ProtocolType,
        target: ProtocolType,
        translator: callable
    ):
        """Register a translator between protocols"""
        self.translators[(source, target)] = translator

    async def translate(
        self,
        message: Message,
        target_protocol: ProtocolType
    ) -> Message:
        """Translate message to target protocol"""
        source = message.header.protocol

        if source == target_protocol:
            return message

        translator = self.translators.get((source, target_protocol))
        if translator:
            return await translator(message)

        # Default: wrap payload with protocol metadata
        message.header.headers["original_protocol"] = source.value
        message.header.protocol = target_protocol
        return message


class CommunicationManager:
    """
    Advanced Communication Manager
    ==============================

    Manages all aspects of agent communication.
    """

    def __init__(self):
        self.registry = ProtocolRegistry()
        self.negotiator = ProtocolNegotiator(self.registry)
        self.router = MessageRouter()
        self.secure_handler = SecureMessageHandler()
        self.adapter = ProtocolAdapter()
        self.message_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    async def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        payload: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        protocol: ProtocolType = ProtocolType.GRPC
    ) -> Message:
        """Send message between agents"""
        header = MessageHeader(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            timestamp=datetime.now(),
            priority=priority,
            protocol=protocol,
            version=ProtocolVersion.V3,
            content_type="application/json"
        )

        message = Message(header=header, payload=payload)

        # Encrypt and sign
        message = await self.secure_handler.encrypt_message(message, receiver_id)
        message = await self.secure_handler.sign_message(message, sender_id)

        # Route to best endpoint
        endpoint = self.router.route_to(receiver_id, priority, len(json.dumps(payload)))
        if endpoint:
            message.header.headers["endpoint"] = endpoint

        print(f"[Communication] Message {message.header.message_id[:8]} sent: {sender_id} -> {receiver_id} via {protocol.value}")

        return message

    async def negotiate_connection(
        self,
        agent_a: str,
        agent_b: str
    ) -> NegotiationResult:
        """Negotiate communication protocol"""
        agent_a_protocols = [ProtocolType.GRPC, ProtocolType.WEBSOCKET, ProtocolType.HTTP]
        agent_b_protocols = [ProtocolType.GRPC, ProtocolType.WEBSOCKET, ProtocolType.MQTT]

        return await self.negotiator.negotiate(agent_a_protocols, agent_b_protocols)

    async def process_queue(self):
        """Process message queue"""
        while not self.message_queue.empty():
            priority, message = await self.message_queue.get()
            print(f"[Queue] Processing message: {message.header.message_id[:8]}")
            self.message_queue.task_done()


async def main():
    """Demonstrate Advanced Communication Protocols"""
    print("=" * 60)
    print("Advanced Agent Communication Protocols - Day 91")
    print("=" * 60)

    # Initialize manager
    manager = CommunicationManager()

    # List available protocols
    print("\n[1] Available Protocols")
    print("-" * 40)
    protocols = manager.registry.list_protocols()
    for protocol in protocols:
        cap = manager.registry.get_capability(protocol)
        print(f"  {protocol.value}: v{cap.version.value}")
        print(f"    Features: {', '.join(cap.features)}")

    # Protocol negotiation
    print("\n[2] Protocol Negotiation")
    print("-" * 40)

    result = await manager.negotiate_connection("agent-001", "agent-002")
    print(f"  Negotiated: {result.agreed_protocol.value} {result.agreed_version.value}")
    print(f"  Session ID: {result.session_id[:8]}...")
    print(f"  Features: {', '.join(result.features)}")

    # Secure messaging
    print("\n[3] Secure Messaging")
    print("-" * 40)

    message = await manager.send_message(
        sender_id="agent-001",
        receiver_id="agent-002",
        payload={"action": "process", "data": {"key": "value"}},
        priority=MessagePriority.HIGH,
        protocol=ProtocolType.GRPC
    )

    print(f"  Message ID: {message.header.message_id[:8]}")
    print(f"  Encrypted: {message.encryption}")
    print(f"  Signed: {message.signature[:16] if message.signature else 'None'}...")

    # Message routing
    print("\n[4] Intelligent Routing")
    print("-" * 40)

    manager.router.add_route("agent-002", "endpoint-1")
    manager.router.add_route("agent-002", "endpoint-2")
    manager.router.add_route("agent-002", "endpoint-3")

    # Simulate some routing
    manager.router.update_metrics("endpoint-1", 10, True)
    manager.router.update_metrics("endpoint-2", 5, True)
    manager.router.update_metrics("endpoint-3", 20, False)

    route = manager.router.route_to("agent-002", MessagePriority.HIGH, 1000)
    print(f"  Selected route: {route}")

    # Protocol translation
    print("\n[5] Protocol Adaptation")
    print("-" * 40)

    original_msg = Message(
        header=MessageHeader(
            message_id=str(uuid.uuid4()),
            sender_id="agent-001",
            receiver_id="agent-003",
            timestamp=datetime.now(),
            priority=MessagePriority.NORMAL,
            protocol=ProtocolType.HTTP,
            version=ProtocolVersion.V2,
            content_type="application/json"
        ),
        payload={"test": "data"}
    )

    translated = await manager.adapter.translate(original_msg, ProtocolType.MQTT)
    print(f"  Original protocol: {original_msg.header.protocol.value}")
    print(f"  Translated protocol: {translated.header.protocol.value}")
    print(f"  Original headers preserved: {'original_protocol' in translated.header.headers}")

    # Multi-agent communication
    print("\n[6] Multi-Agent Communication")
    print("-" * 40)

    agents = ["agent-a", "agent-b", "agent-c", "agent-d"]
    for i, sender in enumerate(agents):
        receiver = agents[(i + 1) % len(agents)]
        await manager.send_message(sender, receiver, {"task": f"task-{i}"}, protocol=ProtocolType.WEBSOCKET)

    print(f"  Sent {len(agents)} messages in mesh topology")

    print("\n" + "=" * 60)
    print("Advanced Communication Protocols complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())