"""
Day 82: Agent Federation
========================

Federated multi-agent systems with distributed coordination
and cross-agent communication.

Key Concepts:
- Federated architecture
- Cross-agent communication
- Distributed coordination
- Agent networks
- Peer discovery
- Trust management
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import random


class FederationStatus(Enum):
    """Federation connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
    FAILED = "failed"


@dataclass
class AgentPeer:
    """Represents a peer agent in the federation"""
    peer_id: str
    name: str
    address: str
    capabilities: List[str]
    status: FederationStatus
    trust_score: float = 0.5
    last_seen: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FederationMessage:
    """Message between federated agents"""
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 10


@dataclass
class FederatedTask:
    """Task distributed across federation"""
    task_id: str
    description: str
    initiator_id: str
    assigned_peers: List[str]
    status: str = "pending"
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class PeerDiscovery:
    """
    Peer Discovery
    ==============

    Discovers and maintains peer agents in the federation.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.known_peers: Dict[str, AgentPeer] = {}
        self.discovery_interval = 30

    def discover_peers(self) -> List[AgentPeer]:
        """Discover available peer agents"""
        # Simulate peer discovery
        discovered = []

        # Simulate finding new peers
        if len(self.known_peers) < 5:
            new_peers = [
                AgentPeer(
                    peer_id=str(uuid.uuid4())[:8],
                    name=f"peer_{random.randint(100, 999)}",
                    address=f"192.168.1.{random.randint(10, 250)}",
                    capabilities=["data_processing", "api_integration"],
                    status=FederationStatus.CONNECTED,
                    trust_score=random.uniform(0.5, 0.9)
                )
                for _ in range(random.randint(1, 3))
            ]
            for peer in new_peers:
                self.known_peers[peer.peer_id] = peer
                discovered.append(peer)

        return list(self.known_peers.values())

    def get_peer(self, peer_id: str) -> Optional[AgentPeer]:
        """Get peer by ID"""
        return self.known_peers.get(peer_id)

    def update_peer_status(self, peer_id: str, status: FederationStatus):
        """Update peer connection status"""
        if peer_id in self.known_peers:
            self.known_peers[peer_id].status = status
            self.known_peers[peer_id].last_seen = datetime.now()


class TrustManager:
    """
    Trust Manager
    =============

    Manages trust scores between federated agents.
    """

    def __init__(self):
        self.trust_scores: Dict[str, float] = {}
        self.interaction_history: Dict[str, List[Dict]] = {}

    def calculate_trust(
        self,
        peer_id: str,
        interaction_result: str
    ) -> float:
        """Calculate trust score based on interactions"""
        if peer_id not in self.interaction_history:
            self.interaction_history[peer_id] = []

        self.interaction_history[peer_id].append({
            "result": interaction_result,
            "timestamp": datetime.now()
        })

        # Keep only recent history
        history = self.interaction_history[peer_id][-20:]

        # Calculate trust based on success rate
        successful = sum(1 for h in history if h["result"] == "success")
        trust = successful / len(history) if history else 0.5

        self.trust_scores[peer_id] = trust
        return trust

    def get_trust_score(self, peer_id: str) -> float:
        """Get current trust score for peer"""
        return self.trust_scores.get(peer_id, 0.5)

    def is_trusted(self, peer_id: str, threshold: float = 0.6) -> bool:
        """Check if peer is trusted above threshold"""
        return self.get_trust_score(peer_id) >= threshold


class FederationRouter:
    """
    Federation Router
    =================

    Routes messages between federated agents.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.message_queue: List[FederationMessage] = []
        self.routing_table: Dict[str, str] = {}

    def send_message(
        self,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> FederationMessage:
        """Send a message to a peer"""
        message = FederationMessage(
            message_id=str(uuid.uuid4())[:8],
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload
        )
        self.message_queue.append(message)
        return message

    def broadcast(
        self,
        message_type: str,
        payload: Dict[str, Any],
        peer_ids: List[str]
    ) -> List[FederationMessage]:
        """Broadcast message to multiple peers"""
        messages = []
        for peer_id in peer_ids:
            msg = self.send_message(peer_id, message_type, payload)
            messages.append(msg)
        return messages

    def get_pending_messages(self, recipient_id: str) -> List[FederationMessage]:
        """Get pending messages for a recipient"""
        return [
            m for m in self.message_queue
            if m.recipient_id == recipient_id
        ]


class AgentFederation:
    """
    Agent Federation
    ================

    Main federation system for multi-agent coordination.
    """

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.discovery = PeerDiscovery(agent_id)
        self.trust_manager = TrustManager()
        self.router = FederationRouter(agent_id)
        self.active_tasks: Dict[str, FederatedTask] = {}

    def join_federation(self) -> List[AgentPeer]:
        """Join the federation and discover peers"""
        print(f"[{self.name}] Joining federation...")
        peers = self.discovery.discover_peers()
        print(f"[{self.name}] Discovered {len(peers)} peers")
        return peers

    def assign_task(
        self,
        description: str,
        peer_ids: List[str]
    ) -> FederatedTask:
        """Assign a task to federated peers"""
        task = FederatedTask(
            task_id=str(uuid.uuid4())[:8],
            description=description,
            initiator_id=self.agent_id,
            assigned_peers=peer_ids,
            status="assigned"
        )
        self.active_tasks[task.task_id] = task

        # Notify assigned peers
        self.router.broadcast(
            "task_assignment",
            {
                "task_id": task.task_id,
                "description": description,
                "initiator": self.agent_id
            },
            peer_ids
        )

        print(f"[{self.name}] Task {task.task_id} assigned to {len(peer_ids)} peers")
        return task

    def receive_result(
        self,
        peer_id: str,
        task_id: str,
        result: Dict[str, Any]
    ):
        """Receive result from a peer"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.results[peer_id] = result
            task.status = "partial"

            # Update trust based on result
            success = result.get("status") == "success"
            self.trust_manager.calculate_trust(
                peer_id,
                "success" if success else "failure"
            )

            print(f"[{self.name}] Received result from {peer_id} for task {task_id}")

            # Check if all results are in
            if len(task.results) == len(task.assigned_peers):
                task.status = "completed"
                print(f"[{self.name}] Task {task_id} completed")

    def aggregate_results(self, task_id: str) -> Dict[str, Any]:
        """Aggregate results from all peers"""
        if task_id not in self.active_tasks:
            return {}

        task = self.active_tasks[task_id]
        results = list(task.results.values())

        if not results:
            return {}

        # Simple aggregation - combine all results
        aggregated = {
            "task_id": task_id,
            "total_results": len(results),
            "results": results,
            "summary": f"Aggregated {len(results)} peer results"
        }

        return aggregated


def main():
    """Demonstrate Agent Federation"""
    print("=" * 60)
    print("Agent Federation - Day 82")
    print("=" * 60)

    # Create federated agents
    agent1 = AgentFederation("agent_001", "DataProcessor")
    agent2 = AgentFederation("agent_002", "APIGateway")
    agent3 = AgentFederation("agent_003", "Analyzer")

    # Join federation
    print("\n[Joining Federation]")
    peers = agent1.join_federation()

    print("\n[Peer List]")
    for peer in peers:
        print(f"  - {peer.name} ({peer.peer_id}): {peer.status.value}")

    # Get peer IDs for task assignment
    peer_ids = [p.peer_id for p in peers[:2]]

    # Assign distributed task
    print("\n[Assigning Federated Task]")
    task = agent1.assign_task(
        "Process and analyze dataset",
        peer_ids
    )

    # Simulate receiving results
    print("\n[Simulating Results]")
    for peer_id in peer_ids:
        agent1.receive_result(
            peer_id,
            task.task_id,
            {
                "status": "success",
                "data_processed": random.randint(100, 1000),
                "analysis": "completed"
            }
        )

    # Aggregate results
    print("\n[Aggregating Results]")
    aggregated = agent1.aggregate_results(task.task_id)
    print(f"  Total Results: {aggregated.get('total_results', 0)}")

    # Trust scores
    print("\n[Trust Scores]")
    for peer_id in peer_ids:
        score = agent1.trust_manager.get_trust_score(peer_id)
        print(f"  {peer_id}: {score:.2f}")

    print("\n" + "=" * 60)
    print("Federation demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()