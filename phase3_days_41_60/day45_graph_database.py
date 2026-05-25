"""
Day 45: Graph Database Integration (Neo4j)
==========================================
Integrate knowledge graphs with Neo4j for persistent storage.

Neo4j is a powerful graph database that supports Cypher queries,
allowing complex traversals and aggregations.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import json
import uuid


# Abstract interface for graph databases
class GraphDatabase(ABC):
    """Abstract graph database interface"""

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def create_node(self, label: str, properties: Dict) -> str:
        pass

    @abstractmethod
    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Dict = None
    ) -> str:
        pass

    @abstractmethod
    def query(self, cypher: str) -> List[Dict]:
        pass

    @abstractmethod
    def find_node(self, label: str, property_key: str, property_value: Any) -> Optional[Dict]:
        pass


class InMemoryGraphDB(GraphDatabase):
    """
    In-Memory Graph Database
    =========================

    A simple in-memory implementation for learning/demonstration.
    In production, replace with Neo4j or similar.

    Features:
    - Node CRUD
    - Relationship CRUD
    - Cypher-like query support (simplified)
    - Transaction support
    """

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.labels: Dict[str, Dict[str, str]] = {}  # label -> {property -> node_id}
        self.relationships: Dict[str, Dict] = {}
        self._id_counter = 0

    def connect(self) -> bool:
        """Connect to database"""
        # In-memory always succeeds
        return True

    def disconnect(self):
        """Disconnect from database"""
        pass

    def _generate_id(self) -> str:
        """Generate unique node ID"""
        self._id_counter += 1
        return f"node_{self._id_counter}"

    def create_node(self, label: str, properties: Dict) -> str:
        """Create a node with label and properties"""
        node_id = self._generate_id()

        node = {
            "id": node_id,
            "label": label,
            "properties": properties,
            "created_at": datetime.now().isoformat()
        }

        self.nodes[node_id] = node

        # Index by label
        if label not in self.labels:
            self.labels[label] = {}

        # Index by primary property (usually 'name' or 'id')
        primary_key = properties.get('name') or properties.get('id') or node_id
        self.labels[label][str(primary_key)] = node_id

        return node_id

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    def update_node(self, node_id: str, properties: Dict) -> bool:
        """Update node properties"""
        if node_id not in self.nodes:
            return False

        self.nodes[node_id]["properties"].update(properties)
        return True

    def delete_node(self, node_id: str) -> bool:
        """Delete node and its relationships"""
        if node_id not in self.nodes:
            return False

        # Remove relationships
        to_delete = [
            rid for rid, rel in self.relationships.items()
            if rel["from"] == node_id or rel["to"] == node_id
        ]
        for rid in to_delete:
            del self.relationships[rid]

        # Remove from index
        label = self.nodes[node_id]["label"]
        if label in self.labels:
            primary_key = self.nodes[node_id]["properties"].get('name') or node_id
            self.labels[label].pop(str(primary_key), None)

        del self.nodes[node_id]
        return True

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Dict = None
    ) -> Optional[str]:
        """Create a relationship between nodes"""
        if from_id not in self.nodes or to_id not in self.nodes:
            return None

        rel_id = f"rel_{uuid.uuid4().hex[:8]}"

        relationship = {
            "id": rel_id,
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat()
        }

        self.relationships[rel_id] = relationship
        return rel_id

    def find_node(self, label: str, property_key: str, property_value: Any) -> Optional[Dict]:
        """Find node by label and property"""
        if label not in self.labels:
            return None

        node_id = self.labels[label].get(str(property_value))
        if node_id:
            return self.nodes.get(node_id)
        return None

    def find_nodes(self, label: str, property_key: str = None, property_value: Any = None) -> List[Dict]:
        """Find all nodes with label, optionally filtered"""
        results = []

        for node in self.nodes.values():
            if node["label"] == label:
                if property_key is None or node["properties"].get(property_key) == property_value:
                    results.append(node)

        return results

    def get_neighbors(
        self,
        node_id: str,
        rel_type: str = None,
        direction: str = "both"
    ) -> List[Dict]:
        """Get neighboring nodes"""
        neighbors = []

        for rel in self.relationships.values():
            neighbor_id = None

            if direction in ["outgoing", "both"] and rel["from"] == node_id:
                neighbor_id = rel["to"]
            elif direction in ["incoming", "both"] and rel["to"] == node_id:
                neighbor_id = rel["from"]

            if neighbor_id:
                if rel_type is None or rel["type"] == rel_type:
                    neighbor = self.nodes.get(neighbor_id)
                    if neighbor:
                        neighbors.append({
                            "node": neighbor,
                            "relationship": rel
                        })

        return neighbors

    def execute_cypher(self, query: str) -> List[Dict]:
        """
        Execute simplified Cypher-like query

        Supported patterns:
        - MATCH (n:Label) RETURN n
        - MATCH (n:Label {prop: value}) RETURN n
        - MATCH (a:Label1)-[r:REL_TYPE]->(b:Label2) RETURN a, b
        """
        query = query.strip()

        # Simple MATCH pattern
        if query.startswith("MATCH"):
            return self._execute_match(query)

        return []

    def _execute_match(self, query: str) -> List[Dict]:
        """Execute MATCH pattern"""
        results = []

        # Parse node patterns: (n:Label) or (n:Label {prop: value})
        import re
        node_pattern = re.search(r'\(([a-zA-Z_][a-zA-Z0-9_]*):?([A-Za-z]+)?\s*(\{[^}]+\})?\)', query)

        if not node_pattern:
            return results

        var_name = node_pattern.group(1)
        label = node_pattern.group(2)
        props_str = node_pattern.group(3)

        # Parse properties
        properties = {}
        if props_str:
            props_str = props_str.strip('{}')
            for prop in props_str.split(','):
                key, value = prop.split(':')
                key = key.strip().strip('"')
                value = value.strip().strip('"\'')

                # Try to convert type
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)

                properties[key] = value

        # Find matching nodes
        if label:
            nodes = self.find_nodes(label, **properties) if properties else self.find_nodes(label)
        else:
            nodes = list(self.nodes.values())

        results = [{"n": node} for node in nodes]
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        label_counts = {}
        for node in self.nodes.values():
            label = node["label"]
            label_counts[label] = label_counts.get(label, 0) + 1

        rel_counts = {}
        for rel in self.relationships.values():
            rel_type = rel["type"]
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "labels": label_counts,
            "relationship_types": rel_counts
        }

    def clear(self):
        """Clear all data"""
        self.nodes.clear()
        self.labels.clear()
        self.relationships.clear()
        self._id_counter = 0


class Neo4jWrapper:
    """
    Neo4j Wrapper (Production Implementation)
    =============================================

    This shows how to wrap the real Neo4j driver.
    In production, install neo4j driver: pip install neo4j

    Example:
        from neo4j import GraphDatabase

        class RealNeo4j(GraphDatabase):
            def __init__(self, uri, user, password):
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
            ...
    """

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = ""):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None

    def connect(self) -> bool:
        """Connect to Neo4j"""
        # In production:
        # self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        # return True
        print(f"  [Neo4j] Would connect to {self.uri}")
        return True

    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute Cypher query"""
        # In production:
        # with self.driver.session() as session:
        #     result = session.run(query, parameters or {})
        #     return [dict(record) for record in result]
        return []


# Demo function
def demo():
    """Demonstrate Graph Database"""
    print("=" * 60)
    print("  Graph Database Demo")
    print("=" * 60)

    # Create in-memory database
    db = InMemoryGraphDB()
    db.connect()

    print("\n1. Creating nodes...")
    alice_id = db.create_node("Person", {"name": "Alice", "role": "Engineer"})
    bob_id = db.create_node("Person", {"name": "Bob", "role": "Designer"})
    techcorp_id = db.create_node("Company", {"name": "TechCorp", "founded": 2020})
    sf_id = db.create_node("City", {"name": "San Francisco"})

    print(f"   Created: Alice, Bob, TechCorp, San Francisco")

    print("\n2. Creating relationships...")
    db.create_relationship(alice_id, techcorp_id, "WORKS_AT")
    db.create_relationship(bob_id, techcorp_id, "WORKS_AT")
    db.create_relationship(techcorp_id, sf_id, "LOCATED_IN")

    print("   Created: WORKS_AT (x2), LOCATED_IN")

    print("\n3. Finding nodes...")
    alice = db.find_node("Person", "name", "Alice")
    print(f"   Found: {alice}")

    print("\n4. Getting neighbors...")
    neighbors = db.get_neighbors(alice_id)
    for n in neighbors:
        print(f"   {n['node']['label']}: {n['node']['properties']['name']}")
        print(f"      via: {n['relationship']['type']}")

    print("\n5. Executing Cypher query...")
    results = db.execute_cypher("MATCH (n:Person) RETURN n")
    print(f"   Found {len(results)} Person nodes")
    for r in results:
        print(f"   - {r['n']['properties']}")

    print("\n6. Statistics:")
    stats = db.get_stats()
    print(f"   Nodes: {stats['total_nodes']}")
    print(f"   Relationships: {stats['total_relationships']}")
    print(f"   Labels: {stats['labels']}")

    print("\n7. Neo4j wrapper (no actual connection)...")
    neo4j = Neo4jWrapper()
    neo4j.connect()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()