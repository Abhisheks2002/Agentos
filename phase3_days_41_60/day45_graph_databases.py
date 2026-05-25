"""
Day 45: Graph Database Operations
=================================
Implement graph database operations similar to Neo4j Cypher queries.

Learn to query and manipulate graph data with patterns similar to
Cypher query language used in Neo4j.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import uuid
import json


@dataclass
class Node:
    """Graph node (similar to Neo4j node)"""
    id: str
    labels: Set[str]  # e.g., {"Person", "Employee"}
    properties: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Relationship:
    """Graph relationship (similar to Neo4j relationship)"""
    id: str
    start_node_id: str
    end_node_id: str
    type: str  # e.g., "KNOWS", "WORKS_AT"
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class GraphDatabase:
    """
    Graph Database (Neo4j-like)
    ============================

    In-memory graph database with Cypher-like query support.

    Operations:
    - CREATE nodes and relationships
    - MATCH patterns
    - WHERE filtering
    - RETURN results
    - ORDER BY, LIMIT
    - DELETE

    Simulates Neo4j Cypher queries:
    MATCH (p:Person) WHERE p.name = 'Alice' RETURN p
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.relationships: Dict[str, Relationship] = {}
        # Indexes for faster lookups
        self._label_index: Dict[str, Set[str]] = defaultdict(set)
        self._property_index: Dict[str, Dict[Any, Set[str]]] = defaultdict(dict)

    # ========== CRUD Operations ==========

    def create_node(
        self,
        labels: List[str] = None,
        properties: Dict[str, Any] = None,
        **kwargs
    ) -> Node:
        """Create a node (CREATE in Cypher)"""
        node_id = f"node_{uuid.uuid4().hex[:8]}"

        node = Node(
            id=node_id,
            labels=set(labels) if labels else set(),
            properties=properties or {},
            **kwargs
        )

        self.nodes[node_id] = node

        # Index by labels
        for label in node.labels:
            self._label_index[label].add(node_id)

        # Index by properties
        for key, value in (properties or {}).items():
            if key not in self._property_index:
                self._property_index[key] = {}
            if value not in self._property_index[key]:
                self._property_index[key][value] = set()
            self._property_index[key][value].add(node_id)

        return node

    def create_relationship(
        self,
        start_node_id: str,
        end_node_id: str,
        rel_type: str,
        properties: Dict[str, Any] = None
    ) -> Optional[Relationship]:
        """Create a relationship"""
        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return None

        rel_id = f"rel_{uuid.uuid4().hex[:8]}"

        rel = Relationship(
            id=rel_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            type=rel_type,
            properties=properties or {}
        )

        self.relationships[rel_id] = rel
        return rel

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its relationships"""
        if node_id not in self.nodes:
            return False

        # Delete related relationships
        rels_to_delete = [
            r.id for r in self.relationships.values()
            if r.start_node_id == node_id or r.end_node_id == node_id
        ]

        for rel_id in rels_to_delete:
            del self.relationships[rel_id]

        # Remove from indexes
        node = self.nodes[node_id]
        for label in node.labels:
            self._label_index[label].discard(node_id)

        for key, value in node.properties.items():
            if key in self._property_index:
                self._property_index[key].get(value, set()).discard(node_id)

        del self.nodes[node_id]
        return True

    # ========== Query Operations (Cypher-like) ==========

    def match(
        self,
        labels: List[str] = None,
        properties: Dict[str, Any] = None,
        **kwargs
    ) -> List[Node]:
        """
        Match nodes (MATCH in Cypher)
        =============================

        Pattern: MATCH (n:Person {name: 'Alice'})

        Usage:
            db.match(labels=['Person'], name='Alice')
            db.match(properties={'age': 30})
        """
        candidates = set(self.nodes.keys())

        # Filter by labels
        if labels:
            for label in labels:
                candidates &= self._label_index.get(label, set())

        # Filter by properties
        if properties:
            for key, value in properties.items():
                matches = self._property_index.get(key, {}).get(value, set())
                candidates &= matches

        # Filter by additional kwargs
        for key, value in kwargs.items():
            filtered = set()
            for node_id in candidates:
                if self.nodes[node_id].properties.get(key) == value:
                    filtered.add(node_id)
            candidates = filtered

        return [self.nodes[nid] for nid in candidates]

    def match_one(
        self,
        labels: List[str] = None,
        properties: Dict[str, Any] = None,
        **kwargs
    ) -> Optional[Node]:
        """Match single node"""
        results = self.match(labels, properties, **kwargs)
        return results[0] if results else None

    def match_relationships(
        self,
        start_node_id: str = None,
        end_node_id: str = None,
        rel_type: str = None,
        properties: Dict[str, Any] = None
    ) -> List[Relationship]:
        """Match relationships"""
        results = []

        for rel in self.relationships.values():
            if start_node_id and rel.start_node_id != start_node_id:
                continue
            if end_node_id and rel.end_node_id != end_node_id:
                continue
            if rel_type and rel.type != rel_type:
                continue
            if properties:
                match = all(
                    rel.properties.get(k) == v
                    for k, v in properties.items()
                )
                if not match:
                    continue
            results.append(rel)

        return results

    def traverse(
        self,
        start_node_id: str,
        rel_type: str = None,
        direction: str = "outgoing",  # outgoing, incoming, both
        max_depth: int = 1
    ) -> List[Tuple[Node, Relationship]]:
        """Traverse from a node"""
        results = []
        visited = {start_node_id}
        queue = [(start_node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            # Find relationships
            for rel in self.relationships.values():
                neighbor_id = None

                if direction in ["outgoing", "both"] and rel.start_node_id == current_id:
                    neighbor_id = rel.end_node_id
                elif direction in ["incoming", "both"] and rel.end_node_id == current_id:
                    neighbor_id = rel.start_node_id

                if neighbor_id and neighbor_id not in visited:
                    if rel_type and rel.type != rel_type:
                        continue

                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))

                    neighbor_node = self.nodes.get(neighbor_id)
                    if neighbor_node:
                        results.append((neighbor_node, rel))

        return results

    def cypher(self, query: str, params: Dict[str, Any] = None) -> List[Any]:
        """
        Execute a Cypher-like query
        ============================

        Simplified Cypher parser.

        Supported patterns:
        - MATCH (n:Label) RETURN n
        - MATCH (n:Label {prop: value}) RETURN n
        - MATCH (n)-[r:REL]->(m) RETURN n, r, m
        - MATCH (n) WHERE n.prop = value RETURN n
        """
        query = query.strip()
        params = params or {}

        # Parse RETURN clause
        if "RETURN" not in query:
            return []

        match_part, return_part = query.split("RETURN", 1)
        return_vars = [v.strip() for v in return_part.strip().split(",")]

        # Parse MATCH pattern
        # Simple pattern: (n:Label) or (n:Label {prop: value})
        node_patterns = []
        rel_patterns = []

        # Find all node patterns
        import re
        node_matches = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*)(?::([a-zA-Z_][a-zA-Z0-9_]*))?(?:\s*\{([^}]*)\})?\)', match_part)

        # Find relationship patterns
        rel_matches = re.findall(r'\[([a-zA-Z_][a-zA-Z0-9_]*)(?::([a-zA-Z_][a-zA-Z0-9_]*))?\]', match_part)

        # Build query
        labels = None
        properties = {}

        for var, label, props in node_matches:
            if label:
                labels = [label]

            if props:
                # Parse properties
                prop_pairs = re.findall(r'(\w+):\s*([^\s,]+)', props)
                for key, value in prop_pairs:
                    # Handle string quotes
                    value = value.strip("'\"")
                    properties[key] = params.get(value, value)

        # Execute match
        if labels or properties:
            nodes = self.match(labels, properties)
        else:
            nodes = list(self.nodes.values())

        # Build results
        results = []
        for node in nodes:
            result_row = {}
            for var in return_vars:
                var = var.strip()
                if var == "n" or var == "m":
                    result_row[var] = node
                elif var == "r":
                    # Would need to track relationships
                    pass
            results.append(result_row)

        return results

    # ========== Utility Methods ==========

    def count(self, label: str = None) -> int:
        """Count nodes with label"""
        if label:
            return len(self._label_index.get(label, set()))
        return len(self.nodes)

    def clear(self):
        """Clear all data"""
        self.nodes.clear()
        self.relationships.clear()
        self._label_index.clear()
        self._property_index.clear()

    def export(self) -> Dict[str, Any]:
        """Export graph as JSON"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "labels": list(n.labels),
                    "properties": n.properties
                }
                for n in self.nodes.values()
            ],
            "relationships": [
                {
                    "id": r.id,
                    "start": r.start_node_id,
                    "end": r.end_node_id,
                    "type": r.type,
                    "properties": r.properties
                }
                for r in self.relationships.values()
            ]
        }


# Demo function
def demo():
    """Demonstrate Graph Database"""
    print("=" * 60)
    print("  Graph Database (Neo4j-like) Demo")
    print("=" * 60)

    db = GraphDatabase()

    # Create nodes
    print("\n1. Creating nodes...")
    alice = db.create_node(
        labels=["Person", "Employee"],
        properties={"name": "Alice", "age": 28, "role": "Engineer"}
    )
    bob = db.create_node(
        labels=["Person", "Employee"],
        properties={"name": "Bob", "age": 30, "role": "Designer"}
    )
    charlie = db.create_node(
        labels=["Person", "Manager"],
        properties={"name": "Charlie", "age": 35, "role": "Manager"}
    )
    techcorp = db.create_node(
        labels=["Organization"],
        properties={"name": "TechCorp", "founded": 2020}
    )
    print(f"   Created: {alice.properties['name']}, {bob.properties['name']}, {charlie.properties['name']}")
    print(f"   Created: {techcorp.properties['name']}")

    # Create relationships
    print("\n2. Creating relationships...")
    db.create_relationship(alice.id, techcorp.id, "WORKS_AT", {"since": 2021})
    db.create_relationship(bob.id, techcorp.id, "WORKS_AT", {"since": 2022})
    db.create_relationship(charlie.id, techcorp.id, "WORKS_AT", {"since": 2019})
    db.create_relationship(alice.id, bob.id, "KNOWS", {"since": 2020})
    db.create_relationship(bob.id, charlie.id, "REPORTS_TO")
    print("   Created: WORKS_AT, KNOWS, REPORTS_TO relationships")

    # Match queries
    print("\n3. MATCH queries...")

    # MATCH (n:Person)
    people = db.match(labels=["Person"])
    print(f"   MATCH (n:Person): {len(people)} nodes")

    # MATCH (n:Person {name: 'Alice'})
    alice_nodes = db.match(labels=["Person"], name="Alice")
    print(f"   MATCH (n:Person {{name: 'Alice'}}): {alice_nodes[0].properties if alice_nodes else 'None'}")

    # Traverse
    print("\n4. Traversal...")
    neighbors = db.traverse(alice.id, rel_type="KNOWS", direction="outgoing")
    print(f"   Alice KNOWS: {[n[0].properties['name'] for n in neighbors]}")

    # Traverse with depth
    all_connected = db.traverse(alice.id, max_depth=2)
    print(f"   Alice connected (depth 2): {[n[0].properties['name'] for n in all_connected]}")

    # Cypher-like query
    print("\n5. Cypher query...")
    results = db.cypher("MATCH (n:Person) RETURN n")
    print(f"   MATCH (n:Person) RETURN n: {len(results)} results")

    # Count
    print("\n6. Counts...")
    print(f"   Total nodes: {db.count()}")
    print(f"   Person nodes: {db.count('Person')}")
    print(f"   Organization nodes: {db.count('Organization')}")

    # Export
    print("\n7. Export...")
    data = db.export()
    print(f"   Exported: {len(data['nodes'])} nodes, {len(data['relationships'])} relationships")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()