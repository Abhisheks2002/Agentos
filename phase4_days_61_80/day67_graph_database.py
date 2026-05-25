"""
Day 67: Graph Database Integration
===================================
Integrating agents with graph databases for relationship modeling.

Key Concepts:
- Graph databases
- Node/Edge relationships
- Query optimization
- Relationship traversal
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class NodeType(Enum):
    """Types of nodes in the graph"""
    AGENT = "agent"
    TASK = "task"
    USER = "user"
    RESOURCE = "resource"
    WORKFLOW = "workflow"
    KNOWLEDGE = "knowledge"


class EdgeType(Enum):
    """Types of relationships between nodes"""
    EXECUTED = "executed"
    DEPENDS_ON = "depends_on"
    COLLABORATES_WITH = "collaborates_with"
    OWNS = "owns"
    ACCESSES = "accesses"
    KNOWS = "knows"
    PART_OF = "part_of"


@dataclass
class GraphNode:
    """A node in the knowledge graph"""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    labels: Set[str] = field(default_factory=set)


@dataclass
class GraphEdge:
    """An edge connecting two nodes"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


class GraphDatabase:
    """
    In-Memory Graph Database
    =========================

    Graph database for modeling agent relationships and workflows.
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        # Index for fast lookups
        self.type_index: Dict[NodeType, Set[str]] = defaultdict(set)
        self.edge_type_index: Dict[EdgeType, Set[str]] = defaultdict(set)
        self.adjacency: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self._lock = asyncio.Lock()

    async def create_node(
        self,
        node_type: NodeType,
        properties: Dict[str, Any] = None,
        labels: Set[str] = None
    ) -> GraphNode:
        """Create a new node"""
        async with self._lock:
            node = GraphNode(
                node_id=str(uuid.uuid4()),
                node_type=node_type,
                properties=properties or {},
                labels=labels or set()
            )

            self.nodes[node.node_id] = node
            self.type_index[node_type].add(node.node_id)

            return node

    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: Dict[str, Any] = None,
        weight: float = 1.0
    ) -> Optional[GraphEdge]:
        """Create an edge between two nodes"""
        async with self._lock:
            # Verify nodes exist
            if source_id not in self.nodes or target_id not in self.nodes:
                return None

            edge = GraphEdge(
                edge_id=str(uuid.uuid4()),
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                properties=properties or {},
                weight=weight
            )

            self.edges[edge.edge_id] = edge
            self.edge_type_index[edge_type].add(edge.edge_id)
            self.adjacency[source_id][edge_type.value].add(target_id)

            return edge

    async def get_neighbors(
        self,
        node_id: str,
        edge_types: List[EdgeType] = None
    ) -> List[GraphNode]:
        """Get neighboring nodes"""
        async with self._lock:
            if node_id not in self.adjacency:
                return []

            neighbors = []
            edge_types = edge_types or list(EdgeType)

            for edge_type in edge_types:
                neighbor_ids = self.adjacency[node_id].get(edge_type.value, set())
                for nid in neighbor_ids:
                    if nid in self.nodes:
                        neighbors.append(self.nodes[nid])

            return neighbors

    async def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find path between two nodes using BFS"""
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            current, path = queue.pop(0)

            if current == end_id:
                return path

            if len(path) >= max_depth:
                continue

            for neighbor in self.adjacency[current].values():
                for nid in neighbor:
                    if nid not in visited:
                        visited.add(nid)
                        queue.append((nid, path + [nid]))

        return None

    async def query_by_type(
        self,
        node_type: NodeType
    ) -> List[GraphNode]:
        """Query nodes by type"""
        async with self._lock:
            node_ids = self.type_index.get(node_type, set())
            return [self.nodes[nid] for nid in node_ids if nid in self.nodes]

    async def query_by_label(
        self,
        label: str
    ) -> List[GraphNode]:
        """Query nodes by label"""
        async with self._lock:
            return [
                node for node in self.nodes.values()
                if label in node.labels
            ]

    async def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes_by_type": {
                nt.value: len(ids)
                for nt, ids in self.type_index.items()
            },
            "edges_by_type": {
                et.value: len(ids)
                for et, ids in self.edge_type_index.items()
            }
        }


class AgentGraph:
    """
    Agent Knowledge Graph
    =====================

    Graph-based representation of agent relationships and knowledge.
    """

    def __init__(self):
        self.db = GraphDatabase()
        self.agent_cache: Dict[str, str] = {}  # agent_id -> node_id

    async def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        metadata: Dict[str, Any] = None
    ) -> GraphNode:
        """Register an agent in the knowledge graph"""
        node = await self.db.create_node(
            node_type=NodeType.AGENT,
            properties={
                "agent_id": agent_id,
                "capabilities": capabilities,
                "metadata": metadata or {}
            },
            labels=set(capabilities)
        )

        self.agent_cache[agent_id] = node.node_id
        return node

    async def record_execution(
        self,
        agent_id: str,
        task_id: str,
        result: str
    ):
        """Record task execution as graph edge"""
        agent_node_id = self.agent_cache.get(agent_id)
        if not agent_node_id:
            return

        # Create task node
        task_node = await self.db.create_node(
            node_type=NodeType.TASK,
            properties={
                "task_id": task_id,
                "result": result
            }
        )

        # Create execution edge
        await self.db.create_edge(
            source_id=agent_node_id,
            target_id=task_node.node_id,
            edge_type=EdgeType.EXECUTED,
            properties={"result": result}
        )

    async def find_collaborators(
        self,
        agent_id: str,
        capability: str = None
    ) -> List[GraphNode]:
        """Find potential collaborators for an agent"""
        agent_node_id = self.agent_cache.get(agent_id)
        if not agent_node_id:
            return []

        # Get agents that this agent collaborates with
        collaborators = await self.db.get_neighbors(
            agent_node_id,
            [EdgeType.COLLABORATES_WITH]
        )

        # Filter by capability if specified
        if capability:
            collaborators = [
                c for c in collaborators
                if capability in c.labels
            ]

        return collaborators

    async def get_agent_relationships(
        self,
        agent_id: str
    ) -> Dict[str, List[GraphNode]]:
        """Get all relationships for an agent"""
        agent_node_id = self.agent_cache.get(agent_id)
        if not agent_node_id:
            return {}

        relationships = {}
        for edge_type in EdgeType:
            neighbors = await self.db.get_neighbors(agent_node_id, [edge_type])
            if neighbors:
                relationships[edge_type.value] = neighbors

        return relationships


# Demo
async def main():
    print("=" * 60)
    print("Day 67: Graph Database Integration")
    print("=" * 60)

    graph = AgentGraph()

    # Register agents
    agent1 = await graph.register_agent(
        "agent_1",
        ["analysis", "reporting"],
        {"name": "Analyzer Agent"}
    )

    agent2 = await graph.register_agent(
        "agent_2",
        ["data_processing", "analysis"],
        {"name": "Processing Agent"}
    )

    agent3 = await graph.register_agent(
        "agent_3",
        ["reporting", "visualization"],
        {"name": "Report Agent"}
    )

    print("\nRegistered agents in knowledge graph:")
    print(f"  - {agent1.properties['name']}: {agent1.properties['capabilities']}")
    print(f"  - {agent2.properties['name']}: {agent2.properties['capabilities']}")
    print(f"  - {agent3.properties['name']}: {agent3.properties['capabilities']}")

    # Create collaboration relationships
    await graph.db.create_edge(
        source_id=agent1.node_id,
        target_id=agent2.node_id,
        edge_type=EdgeType.COLLABORATES_WITH,
        weight=0.8
    )

    await graph.db.create_edge(
        source_id=agent2.node_id,
        target_id=agent3.node_id,
        edge_type=EdgeType.COLLABORATES_WITH,
        weight=0.9
    )

    # Record task executions
    await graph.record_execution("agent_1", "task_001", "completed")
    await graph.record_execution("agent_2", "task_002", "completed")

    # Find collaborators
    print("\nFinding collaborators for agent_1:")
    collaborators = await graph.find_collaborators("agent_1")
    for c in collaborators:
        print(f"  - {c.properties.get('name', 'Unknown')}")

    # Get all relationships
    print("\nAgent relationships:")
    relationships = await graph.get_agent_relationships("agent_1")
    for rel_type, nodes in relationships.items():
        print(f"  {rel_type}: {len(nodes)} connections")

    # Graph stats
    stats = await graph.db.get_stats()
    print("\nGraph statistics:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")


if __name__ == "__main__":
    asyncio.run(main())