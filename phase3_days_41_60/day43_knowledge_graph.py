"""
Day 43: Knowledge Graph Basics
==============================
Learn to build and query knowledge graphs for AI agents.

Knowledge graphs represent entities and their relationships as a graph structure,
enabling agents to reason about complex relationships and perform graph-based queries.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import uuid
import json


@dataclass
class Entity:
    """Represents a node in the knowledge graph"""
    id: str
    type: str  # person, organization, location, concept, etc.
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Relationship:
    """Represents an edge in the knowledge graph"""
    id: str
    source_id: str  # Entity ID
    target_id: str  # Entity ID
    type: str  # works_at, knows, located_in, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class KnowledgeGraph:
    """
    Knowledge Graph for Agent Memory
    =================================

    Stores entities and relationships, supports graph queries.

    Key operations:
    - add_entity(), add_relationship()
    - query_neighbors() - get connected entities
    - find_path() - BFS path finding
    - search_entities() - find by type/properties
    """

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        # Index for faster queries
        self._type_index: Dict[str, Set[str]] = defaultdict(set)
        self._name_index: Dict[str, Set[str]] = defaultdict(set)

    def add_entity(
        self,
        entity_type: str,
        name: str,
        properties: Dict[str, Any] = None
    ) -> Entity:
        """Add a new entity to the graph"""
        entity_id = f"entity_{uuid.uuid4().hex[:8]}"

        entity = Entity(
            id=entity_id,
            type=entity_type,
            name=name,
            properties=properties or {}
        )

        self.entities[entity_id] = entity
        self._type_index[entity_type].add(entity_id)
        self._name_index[name.lower()].add(entity_id)

        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Dict[str, Any] = None
    ) -> Optional[Relationship]:
        """Add a relationship between two entities"""
        # Verify entities exist
        if source_id not in self.entities or target_id not in self.entities:
            return None

        rel_id = f"rel_{uuid.uuid4().hex[:8]}"

        relationship = Relationship(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            type=rel_type,
            properties=properties or {}
        )

        self.relationships[rel_id] = relationship
        return relationship

    def get_relationships(
        self,
        entity_id: str,
        rel_type: str = None,
        direction: str = "both"  # "outgoing", "incoming", "both"
    ) -> List[Relationship]:
        """Get relationships for an entity"""
        results = []

        for rel in self.relationships.values():
            if direction in ["outgoing", "both"] and rel.source_id == entity_id:
                if rel_type is None or rel.type == rel_type:
                    results.append(rel)

            if direction in ["incoming", "both"] and rel.target_id == entity_id:
                if rel_type is None or rel.type == rel_type:
                    results.append(rel)

        return results

    def query_neighbors(
        self,
        entity_id: str,
        rel_type: str = None,
        depth: int = 1
    ) -> Dict[str, List[Entity]]:
        """
        Get neighboring entities at various depths

        Returns: {depth: [entities]}
        """
        results = {d: [] for d in range(1, depth + 1)}
        visited = {entity_id}
        current_level = {entity_id}

        for d in range(1, depth + 1):
            next_level = set()

            for entity_id in current_level:
                relationships = self.get_relationships(entity_id, rel_type)

                for rel in relationships:
                    neighbor_id = rel.target_id if rel.source_id == entity_id else rel.source_id

                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        next_level.add(neighbor_id)

                        entity = self.get_entity(neighbor_id)
                        if entity:
                            results[d].append(entity)

            current_level = next_level
            if not current_level:
                break

        return results

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find shortest path between two entities (BFS)"""
        if start_id == end_id:
            return [start_id]

        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            relationships = self.get_relationships(current_id)

            for rel in relationships:
                neighbor_id = rel.target_id if rel.source_id == current_id else rel.source_id

                if neighbor_id == end_id:
                    return path + [neighbor_id]

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def search_entities(
        self,
        entity_type: str = None,
        name: str = None,
        properties: Dict[str, Any] = None
    ) -> List[Entity]:
        """Search entities by type, name, or properties"""
        results = []

        # Start with type filter
        if entity_type:
            entity_ids = self._type_index.get(entity_type, set())
        else:
            entity_ids = set(self.entities.keys())

        # Filter by name
        if name:
            name_matches = self._name_index.get(name.lower(), set())
            entity_ids &= name_matches

        # Filter by properties
        for entity_id in entity_ids:
            entity = self.entities[entity_id]

            if properties:
                match = all(
                    entity.properties.get(k) == v
                    for k, v in properties.items()
                )
                if not match:
                    continue

            results.append(entity)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        type_counts = defaultdict(int)
        for entity in self.entities.values():
            type_counts[entity.type] += 1

        rel_counts = defaultdict(int)
        for rel in self.relationships.values():
            rel_counts[rel.type] += 1

        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entities_by_type": dict(type_counts),
            "relationships_by_type": dict(rel_counts)
        }

    def export_json(self) -> Dict[str, Any]:
        """Export graph as JSON"""
        return {
            "entities": [
                {
                    "id": e.id,
                    "type": e.type,
                    "name": e.name,
                    "properties": e.properties,
                    "created_at": e.created_at
                }
                for e in self.entities.values()
            ],
            "relationships": [
                {
                    "id": r.id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.type,
                    "properties": r.properties,
                    "created_at": r.created_at
                }
                for r in self.relationships.values()
            ]
        }


# Demo function
def demo():
    """Demonstrate Knowledge Graph"""
    print("=" * 60)
    print("  Knowledge Graph Demo")
    print("=" * 60)

    kg = KnowledgeGraph()

    # Add entities
    print("\n1. Creating entities...")
    alice = kg.add_entity("person", "Alice", {"role": "engineer", "age": 28})
    bob = kg.add_entity("person", "Bob", {"role": "designer", "age": 30})
    charlie = kg.add_entity("person", "Charlie", {"role": "manager", "age": 35})
    techcorp = kg.add_entity("organization", "TechCorp", {"founded": 2020})
    sf = kg.add_entity("location", "San Francisco", {"country": "USA"})
    nyc = kg.add_entity("location", "NYC", {"country": "USA"})
    ai = kg.add_entity("concept", "AI", {"field": "computer science"})

    print(f"   Created: {alice.name}, {bob.name}, {charlie.name}")
    print(f"   Created: {techcorp.name}, {sf.name}, {nyc.name}")

    # Add relationships
    print("\n2. Creating relationships...")
    kg.add_relationship(alice.id, techcorp.id, "works_at")
    kg.add_relationship(bob.id, techcorp.id, "works_at")
    kg.add_relationship(charlie.id, techcorp.id, "works_at")
    kg.add_relationship(alice.id, bob.id, "knows")
    kg.add_relationship(bob.id, charlie.id, "knows")
    kg.add_relationship(techcorp.id, sf.id, "located_in")
    kg.add_relationship(techcorp.id, nyc.id, "has_office")
    kg.add_relationship(alice.id, ai.id, "specializes_in")
    kg.add_relationship(bob.id, ai.id, "interested_in")

    print("   Added: works_at, knows, located_in, specializes_in...")

    # Query neighbors
    print("\n3. Querying neighbors of Alice...")
    neighbors = kg.query_neighbors(alice.id, depth=2)
    for depth, entities in neighbors.items():
        if entities:
            print(f"   Depth {depth}: {[e.name for e in entities]}")

    # Find path
    print("\n4. Finding path from Alice to Charlie...")
    path = kg.find_path(alice.id, charlie.id)
    if path:
        path_names = [kg.get_entity(eid).name for eid in path]
        print(f"   Path: {' -> '.join(path_names)}")

    # Search
    print("\n5. Searching for 'person' entities...")
    people = kg.search_entities(entity_type="person")
    print(f"   Found: {[p.name for p in people]}")

    # Stats
    print("\n6. Graph statistics:")
    stats = kg.get_stats()
    print(f"   Entities: {stats['total_entities']}")
    print(f"   Relationships: {stats['total_relationships']}")
    print(f"   By type: {stats['entities_by_type']}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()