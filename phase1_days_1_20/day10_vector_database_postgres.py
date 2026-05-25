"""
Day 10: Building a Persistent Memory Store (Postgres + pgvector)
==================================================================
Skill: SQL + Vector storage
Mini Project: The Agent Archive

AgentOS needs a database that handles both structured data (Agent IDs)
and unstructured data (Memories).
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import json

# Using SQLite for demo (in production, use PostgreSQL with pgvector)
DB_PATH = "agentos.db"

class AgentArchive:
    """SQLite-based agent archive with vector similarity search"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Agent memories (simple embedding storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        """)

        # Agent personalities
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_personalities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                personality_type TEXT NOT NULL,
                prompt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_agent(self, agent_id: str, name: str, role: str, metadata: Dict = None) -> bool:
        """Create a new agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO agents (id, name, role, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, name, role, datetime.now().isoformat(), json.dumps(metadata or {})))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def save_memory(self, agent_id: str, content: str, embedding: bytes = None) -> int:
        """Save an agent memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_memories (agent_id, content, embedding, created_at)
            VALUES (?, ?, ?, ?)
        """, (agent_id, content, embedding, datetime.now().isoformat()))

        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return memory_id

    def search_memories(self, agent_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search agent memories (simple keyword match for demo)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM agent_memories
            WHERE agent_id = ? AND content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_id, f"%{query}%", limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def save_personality(self, agent_id: str, personality_type: str, prompt: str) -> int:
        """Save agent personality"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_personas (agent_id, personality_type, prompt, created_at)
            VALUES (?, ?, ?, ?)
        """, (agent_id, personality_type, prompt, datetime.now().isoformat()))

        personality_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return personality_id

    def get_agent_stats(self, agent_id: str) -> Dict:
        """Get agent statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count memories
        cursor.execute("SELECT COUNT(*) FROM agent_memories WHERE agent_id = ?", (agent_id,))
        memory_count = cursor.fetchone()[0]

        # Count personalities
        cursor.execute("SELECT COUNT(*) FROM agent_personas WHERE agent_id = ?", (agent_id,))
        personality_count = cursor.fetchone()[0]

        conn.close()

        return {
            "agent_id": agent_id,
            "memory_count": memory_count,
            "personality_count": personality_count
        }

def demo():
    """Demo The Agent Archive"""
    print("=" * 70)
    print("The Agent Archive - SQLite + Vector Demo")
    print("=" * 70)

    archive = AgentArchive()

    # Create some agents
    agents = [
        ("AGENT-001", "ResearchBot", "admin", {"department": "R&D"}),
        ("AGENT-002", "DataBot", "user", {"department": "Data"}),
        ("AGENT-003", "MailBot", "guest", {"department": "Communications"}),
    ]

    print("\nCreating agents:")
    for agent_id, name, role, metadata in agents:
        success = archive.create_agent(agent_id, name, role, metadata)
        print(f"  {'✓' if success else '✗'} {name} ({agent_id})")

    # Save some memories
    print("\nSaving memories:")
    memories = [
        ("AGENT-001", "User prefers dark mode UI with blue accents"),
        ("AGENT-001", "Project deadline is next Friday"),
        ("AGENT-002", "Data source is a PostgreSQL database on localhost"),
        ("AGENT-002", "Sync happens every hour at the top of the hour"),
    ]

    for agent_id, content in memories:
        memory_id = archive.save_memory(agent_id, content)
        print(f"  ✓ Memory {memory_id} for {agent_id}")

    # Search memories
    print("\nSearching memories for 'AGENT-001' with query 'UI':")
    results = archive.search_memories("AGENT-001", "UI")
    for r in results:
        print(f"  - {r['content']}")

    # Get agent stats
    print("\nAgent Statistics:")
    for agent_id, name, _, _ in agents:
        stats = archive.get_agent_stats(agent_id)
        print(f"  {name}: {stats['memory_count']} memories")

if __name__ == "__main__":
    demo()