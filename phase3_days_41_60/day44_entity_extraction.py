"""
Day 44: Entity Extraction
===========================
Extract entities from text and link them to knowledge graphs.

Entity extraction identifies named entities (people, organizations, locations)
from unstructured text and prepares them for graph construction.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import uuid


class EntityType(Enum):
    """Standard entity types"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    MONEY = "money"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    CONCEPT = "concept"
    PRODUCT = "product"
    EVENT = "event"


@dataclass
class ExtractedEntity:
    """An entity extracted from text"""
    text: str
    type: EntityType
    start_pos: int
    end_pos: int
    confidence: float = 1.0
    normalized: str = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Result of entity extraction"""
    entities: List[ExtractedEntity]
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EntityExtractor:
    """
    Entity Extraction System
    ========================

    Extracts named entities from text using pattern matching and rules.

    Supports:
    - Pattern-based extraction (regex)
    - Context-aware extraction
    - Entity normalization
    - Confidence scoring

    In production, would use NLP models (spaCy, NER, etc.)
    """

    # Regex patterns for entity types
    PATTERNS = {
        EntityType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        EntityType.PHONE: r'\b(\+?1?[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        EntityType.URL: r'https?://[^\s<>"{}|\\^`\[\]]+',
        EntityType.DATE: r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(st|nd|rd|th)?(,? \d{4})?)\b',
        EntityType.MONEY: r'\$[\d,]+(\.\d{2})?|\b\d+ dollars?\b',
    }

    # Common person name patterns
    PERSON_PREFIXES = ['Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Prof.', 'Sir', 'Lady']
    PERSON_TITLES = ['CEO', 'CTO', 'CFO', 'President', 'Director', 'Manager', 'Engineer']

    def __init__(self):
        self.custom_patterns: Dict[EntityType, str] = {}
        self.known_entities: Dict[str, Set[str]] = {
            EntityType.PERSON: set(),
            EntityType.ORGANIZATION: set(),
            EntityType.LOCATION: set(),
            EntityType.CONCEPT: set(),
            EntityType.PRODUCT: set(),
        }

    def add_known_entity(self, entity_type: EntityType, value: str):
        """Add a known entity for matching"""
        self.known_entities[entity_type].add(value.lower())

    def extract(self, text: str) -> ExtractionResult:
        """Extract all entities from text"""
        entities = []

        # Extract pattern-based entities
        for entity_type, pattern in self.PATTERNS.items():
            entities.extend(self._extract_pattern(text, entity_type, pattern))

        # Extract capitalized entities (potential names/organizations)
        entities.extend(self._extract_capitalized(text))

        # Extract known entities
        entities.extend(self._extract_known(text))

        # Sort by position
        entities.sort(key=lambda e: e.start_pos)

        # Remove overlaps (keep higher confidence)
        entities = self._remove_overlaps(entities)

        return ExtractionResult(entities=entities, text=text)

    def _extract_pattern(
        self,
        text: str,
        entity_type: EntityType,
        pattern: str
    ) -> List[ExtractedEntity]:
        """Extract using regex pattern"""
        entities = []

        for match in re.finditer(pattern, text, re.IGNORECASE):
            normalized = match.group(0)

            # Normalize specific types
            if entity_type == EntityType.EMAIL:
                normalized = normalized.lower()
            elif entity_type == EntityType.DATE:
                normalized = self._normalize_date(match.group(0))

            entity = ExtractedEntity(
                text=match.group(0),
                type=entity_type,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.95,
                normalized=normalized
            )
            entities.append(entity)

        return entities

    def _extract_capitalized(self, text: str) -> List[ExtractedEntity]:
        """Extract capitalized sequences (potential names/orgs)"""
        entities = []

        # Match capitalized word sequences
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'

        for match in re.finditer(pattern, text):
            word = match.group(1)

            # Skip common words
            if word.lower() in {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}:
                continue

            # Determine likely type based on context
            entity_type = self._guess_type(word, text, match.start())

            if entity_type:
                entity = ExtractedEntity(
                    text=word,
                    type=entity_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.7 if entity_type in {EntityType.PERSON, EntityType.ORGANIZATION} else 0.5,
                    normalized=word
                )
                entities.append(entity)

        return entities

    def _extract_known(self, text: str) -> List[ExtractedEntity]:
        """Extract known entities"""
        entities = []

        for entity_type, known_set in self.known_entities.items():
            for known in known_set:
                # Case-insensitive search
                pattern = r'\b' + re.escape(known) + r'\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entity = ExtractedEntity(
                        text=match.group(0),
                        type=entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=1.0,
                        normalized=known
                    )
                    entities.append(entity)

        return entities

    def _guess_type(self, word: str, text: str, pos: int) -> Optional[EntityType]:
        """Guess entity type based on context"""
        # Check for person indicators
        prev_text = text[max(0, pos-20):pos].lower()
        next_text = text[pos+len(word):min(len(text), pos+len(word)+20)].lower()

        # Title after name suggests person
        for title in self.PERSON_TITLES:
            if title in next_text:
                return EntityType.PERSON

        # Prefix suggests person
        for prefix in self.PERSON_PREFIXES:
            if prefix in prev_text:
                return EntityType.PERSON

        # Location indicators
        location_words = {'city', 'country', 'in', 'at', 'located', 'from'}
        if any(w in prev_text for w in location_words):
            return EntityType.LOCATION

        # Organization indicators
        org_words = {'company', 'corp', 'inc', 'llc', 'ltd', 'organization', 'team'}
        if any(w in prev_text.split() + next_text.split() for w in org_words):
            return EntityType.ORGANIZATION

        # Check for common organization suffixes
        org_suffixes = ['Inc', 'Corp', 'LLC', 'Ltd', 'Company', 'Group', 'Technologies', 'Solutions']
        if any(word.endswith(s) for s in org_suffixes):
            return EntityType.ORGANIZATION

        # Single word - could be any, default to concept
        if ' ' not in word:
            return EntityType.CONCEPT

        return EntityType.PERSON

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to standard format"""
        # Simple normalization - in production use dateparser
        return date_str.strip()

    def _remove_overlaps(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove overlapping entities, keeping higher confidence"""
        if not entities:
            return []

        # Sort by confidence descending
        sorted_entities = sorted(entities, key=lambda e: -e.confidence)

        result = []
        for entity in sorted_entities:
            # Check for overlap with existing
            overlaps = False
            for existing in result:
                if (entity.start_pos < existing.end_pos and
                    entity.end_pos > existing.start_pos):
                    overlaps = True
                    break

            if not overlaps:
                result.append(entity)

        # Sort by position
        result.sort(key=lambda e: e.start_pos)
        return result

    def extract_to_graph(self, text: str, graph):
        """Extract entities and add to knowledge graph"""
        result = self.extract(text)

        entity_mapping = {}  # text -> entity_id

        for ext_entity in result.entities:
            # Add to graph
            entity = graph.add_entity(
                entity_type=ext_entity.type.value,
                name=ext_entity.normalized or ext_entity.text,
                properties={
                    "original_text": ext_entity.text,
                    "confidence": ext_entity.confidence,
                    "extracted_from": "entity_extraction"
                }
            )
            entity_mapping[ext_entity.text] = entity.id

        # Link consecutive entities
        sorted_texts = sorted(entity_mapping.keys(), key=lambda t: text.index(t))
        for i in range(len(sorted_texts) - 1):
            # Check if entities are adjacent or close
            pos1 = text.index(sorted_texts[i])
            pos2 = text.index(sorted_texts[i + 1])

            if pos2 - pos1 < 50:  # Within 50 chars
                graph.add_relationship(
                    entity_mapping[sorted_texts[i]],
                    entity_mapping[sorted_texts[i + 1]],
                    "followed_by"
                )

        return entity_mapping, result


# Demo function
def demo():
    """Demonstrate Entity Extraction"""
    print("=" * 60)
    print("  Entity Extraction Demo")
    print("=" * 60)

    extractor = EntityExtractor()

    # Add known entities
    print("\n1. Adding known entities...")
    extractor.add_known_entity(EntityType.ORGANIZATION, "TechCorp")
    extractor.add_known_entity(EntityType.ORGANIZATION, "OpenAI")
    extractor.add_known_entity(EntityType.PERSON, "Alice")
    extractor.add_known_entity(EntityType.PERSON, "Bob")
    print("   Added: TechCorp, OpenAI, Alice, Bob")

    # Test text
    test_text = """
    Alice works at TechCorp in San Francisco. She collaborates with
    Bob from OpenAI. They meet every Monday at 9:00 AM at the TechCorp
    office located at 123 Market Street. Contact alice@techcorp.com
    for more info. Their project budget is $50,000.
    """

    print(f"\n2. Processing text:\n{test_text.strip()}")

    # Extract entities
    result = extractor.extract(test_text)

    print("\n3. Extracted entities:")
    for entity in result.entities:
        print(f"   {entity.type.value:15} | {entity.text:30} | conf: {entity.confidence:.2f}")

    # Test with knowledge graph integration
    print("\n4. Integration with Knowledge Graph...")
    from day43_knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()

    entity_map, _ = extractor.extract_to_graph(test_text, kg)

    stats = kg.get_stats()
    print(f"   Added {stats['total_entities']} entities and relationships to graph")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()