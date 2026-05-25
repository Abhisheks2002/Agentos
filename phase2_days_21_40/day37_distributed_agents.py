"""
Day 37: Distributed Agent Systems
=================================
Skill: Distributed Computing
Mini Project: Node Registry

Building agents that can work across distributed systems.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import json
import hashlib


class NodeStatus(str, Enum):
    """Node status"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class AgentNode:
    """A node in the distributed system"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    host: str = "localhost"
    port: int = 8000
    status: NodeStatus = NodeStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    current_load: float = 0.0
    max_load: float = 100.0
    region: str = "us-east"
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    task_count: int = 0


@dataclass
class RemoteTask:
    """A task to be executed on a remote node"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    payload: Any = None
    target_node: Optional[str] = None
    source_node: str = ""
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


class NodeRegistry:
    """Registry for managing agent nodes"""

    def __init__(self):
        self.nodes: Dict[str, AgentNode] = {}
        self.node_groups: Dict[str, Set[str]] = {}

    def register_node(self, node: AgentNode) -> str:
        """Register a new node"""
        self.nodes[node.node_id] = node

        # Add to region group
        if node.region not in self.node_groups:
            self.node_groups[node.region] = set()
        self.node_groups[node.region].add(node.node_id)

        return node.node_id

    def unregister_node(self, node_id: str):
        """Unregister a node"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            if node.region in self.node_groups:
                self.node_groups[node.region].discard(node_id)
            del self.nodes[node_id]

    def get_node(self, node_id: str) -> Optional[AgentNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def find_nodes(
        self,
        capability: str = None,
        region: str = None,
        max_load: float = None
    ) -> List[AgentNode]:
        """Find nodes matching criteria"""
        candidates = list(self.nodes.values())

        if capability:
            candidates = [n for n in candidates if capability in n.capabilities]

        if region:
            candidates = [n for n in candidates if n.region == region]

        if max_load is not None:
            candidates = [n for n in candidates if n.current_load < max_load]

        # Sort by load (lowest first)
        candidates.sort(key=lambda n: n.current_load)

        return candidates

    def update_heartbeat(self, node_id: str):
        """Update node heartbeat"""
        if node_id in self.nodes:
            self.nodes[node_id].last_heartbeat = datetime.now().isoformat()
            self.nodes[node_id].status = NodeStatus.ACTIVE

    def get_healthy_nodes(self, timeout_seconds: int = 30) -> List[AgentNode]:
        """Get nodes that have sent recent heartbeats"""
        now = datetime.now()
        healthy = []

        for node in self.nodes.values():
            last_hb = datetime.fromisoformat(node.last_heartbeat)
            if (now - last_hb).total_seconds() < timeout_seconds:
                healthy.append(node)

        return healthy


class MessageRouter:
    """Routes messages between nodes"""

    def __init__(self, registry: NodeRegistry):
        self.registry = registry
        self.routes: Dict[str, str] = {}  # task_id -> node_id
        self.message_log: List[Dict[str, Any]] = []

    async def send_task(self, task: RemoteTask, target_node_id: str) -> bool:
        """Send a task to a target node"""
        node = self.registry.get_node(target_node_id)

        if not node or node.status == NodeStatus.OFFLINE:
            return False

        # Simulate sending
        task.target_node = target_node_id
        self.routes[task.task_id] = target_node_id
        node.current_load += 10
        node.task_count += 1
        node.status = NodeStatus.BUSY

        self.message_log.append({
            "type": "send",
            "task_id": task.task_id,
            "from": task.source_node,
            "to": target_node_id,
            "timestamp": datetime.now().isoformat()
        })

        return True

    async def receive_result(self, task: RemoteTask) -> Any:
        """Receive a result from a node"""
        if task.task_id in self.routes:
            node_id = self.routes.pop(task.task_id)
            node = self.registry.get_node(node_id)
            if node:
                node.current_load = max(0, node.current_load - 10)
                node.status = NodeStatus.IDLE if node.current_load < 10 else NodeStatus.BUSY

        self.message_log.append({
            "type": "receive",
            "task_id": task.task_id,
            "from": task.target_node,
            "timestamp": datetime.now().isoformat()
        })

        return task.result

    def get_route(self, task_id: str) -> Optional[str]:
        """Get the node handling a task"""
        return self.routes.get(task_id)


class DistributedAgent:
    """An agent that can work across distributed nodes"""

    def __init__(self, agent_id: str, registry: NodeRegistry, router: MessageRouter):
        self.agent_id = agent_id
        self.registry = registry
        self.router = router
        self.local_tasks: Dict[str, RemoteTask] = {}

    async def submit_task(
        self,
        name: str,
        payload: Any,
        capability_required: str = None,
        region: str = None
    ) -> str:
        """Submit a task to a distributed node"""
        task = RemoteTask(
            name=name,
            payload=payload,
            source_node=self.agent_id
        )

        # Find best node
        nodes = self.registry.find_nodes(
            capability=capability_required,
            region=region,
            max_load=90.0
        )

        if not nodes:
            raise Exception("No available nodes found")

        # Select the best node (lowest load)
        target_node = nodes[0]

        # Send task
        success = await self.router.send_task(task, target_node.node_id)

        if not success:
            raise Exception(f"Failed to send task to {target_node.node_id}")

        self.local_tasks[task.task_id] = task
        return task.task_id

    async def get_result(self, task_id: str, timeout: float = 30.0) -> Any:
        """Get task result"""
        task = self.local_tasks.get(task_id)

        if not task:
            return None

        # Simulate waiting for result
        await asyncio.sleep(0.5)

        # Simulate result
        task.status = "completed"
        task.result = f"Processed: {task.payload}"
        task.completed_at = datetime.now().isoformat()

        return await self.router.receive_result(task)


class LoadBalancer:
    """Load balancer for distributed agents"""

    def __init__(self, registry: NodeRegistry):
        self.registry = registry

    def select_node(self, capability: str = None) -> Optional[AgentNode]:
        """Select a node using least connections algorithm"""
        nodes = self.registry.find_nodes(
            capability=capability,
            max_load=90.0
        )

        if not nodes:
            return None

        # Select node with lowest load
        return min(nodes, key=lambda n: n.current_load)

    def get_distribution_stats(self) -> Dict[str, Any]:
        """Get load distribution statistics"""
        nodes = list(self.registry.nodes.values())

        if not nodes:
            return {"total_nodes": 0}

        return {
            "total_nodes": len(nodes),
            "total_load": sum(n.current_load for n in nodes),
            "average_load": sum(n.current_load for n in nodes) / len(nodes),
            "by_region": {
                region: {
                    "nodes": len(node_ids),
                    "total_load": sum(
                        self.registry.nodes[n].current_load
                        for n in node_ids
                    )
                }
                for region, node_ids in self.registry.node_groups.items()
            }
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Distributed Agent Systems Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create registry
        registry = NodeRegistry()
        router = MessageRouter(registry)

        # Register nodes
        print("\n[1] Register Nodes")
        print("-" * 40)

        node1 = AgentNode(
            name="Node-US-1",
            host="node1.example.com",
            port=8001,
            capabilities=["compute", "storage"],
            region="us-east"
        )

        node2 = AgentNode(
            name="Node-US-2",
            host="node2.example.com",
            port=8002,
            capabilities=["compute", "ml"],
            region="us-west"
        )

        node3 = AgentNode(
            name="Node-EU-1",
            host="node3.example.com",
            port=8003,
            capabilities=["storage", "ml"],
            region="eu-west"
        )

        registry.register_node(node1)
        registry.register_node(node2)
        registry.register_node(node3)

        print(f"  Registered: {node1.name}, {node2.name}, {node3.name}")

        # Find nodes
        print("\n[2] Find Nodes")
        print("-" * 40)

        compute_nodes = registry.find_nodes(capability="compute")
        print(f"  Compute nodes: {[n.name for n in compute_nodes]}")

        ml_nodes = registry.find_nodes(capability="ml")
        print(f"  ML nodes: {[n.name for n in ml_nodes]}")

        # Load balancer
        print("\n[3] Load Balancer")
        print("-" * 40)

        lb = LoadBalancer(registry)

        # Simulate load
        node1.current_load = 30
        node2.current_load = 50
        node3.current_load = 20

        selected = lb.select_node(capability="compute")
        print(f"  Selected for compute: {selected.name if selected else 'None'}")

        stats = lb.get_distribution_stats()
        print(f"  Total load: {stats['total_load']}")
        print(f"  Average load: {stats['average_load']:.1f}")

        # Distributed agent
        print("\n[4] Distributed Agent Tasks")
        print("-" * 40)

        agent = DistributedAgent("agent-main", registry, router)

        task_id = await agent.submit_task(
            "process_data",
            {"data": "sample"},
            capability_required="compute"
        )
        print(f"  Submitted task: {task_id}")

        result = await agent.get_result(task_id)
        print(f"  Result: {result}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()