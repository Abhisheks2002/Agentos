"""
Day 63: Agent Versioning and State Management
==============================================
Version control and state management for AI agents.

Key Concepts:
- Agent versioning
- State snapshots
- Rollback capabilities
- State persistence
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


class VersionStatus(Enum):
    """Version status"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class AgentVersion:
    """A version of an agent"""
    version_id: str
    version_number: str
    name: str
    config: Dict[str, Any]
    tools: List[str] = field(default_factory=list)
    system_prompt: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    status: VersionStatus = VersionStatus.DRAFT
    parent_version: Optional[str] = None
    changelog: List[str] = field(default_factory=list)


@dataclass
class StateSnapshot:
    """Snapshot of agent state"""
    snapshot_id: str
    version_id: str
    state_data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""


class AgentVersionManager:
    """
    Agent Version Manager
    =====================

    Manages versions and state snapshots for agents.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.versions: Dict[str, AgentVersion] = {}
        self.snapshots: Dict[str, List[StateSnapshot]] = {}
        self.active_version: Optional[str] = None

    def create_version(
        self,
        version_number: str,
        name: str,
        config: Dict[str, Any],
        tools: List[str] = None,
        system_prompt: str = "",
        parent_version: Optional[str] = None,
        changelog: List[str] = None
    ) -> AgentVersion:
        """Create a new agent version"""
        version_id = f"{self.agent_id}_v{version_number}"

        version = AgentVersion(
            version_id=version_id,
            version_number=version_number,
            name=name,
            config=config,
            tools=tools or [],
            system_prompt=system_prompt,
            parent_version=parent_version,
            changelog=changelog or [],
            status=VersionStatus.DRAFT
        )

        self.versions[version_id] = version
        self.snapshots[version_id] = []

        return version

    def activate_version(self, version_id: str) -> bool:
        """Activate a version"""
        if version_id not in self.versions:
            return False

        # Deactivate current active version
        if self.active_version and self.active_version in self.versions:
            self.versions[self.active_version].status = VersionStatus.DRAFT

        # Activate new version
        self.versions[version_id].status = VersionStatus.ACTIVE
        self.active_version = version_id

        return True

    def create_snapshot(
        self,
        version_id: str,
        state_data: Dict[str, Any],
        description: str = ""
    ) -> StateSnapshot:
        """Create a state snapshot"""
        snapshot = StateSnapshot(
            snapshot_id=str(uuid.uuid4()),
            version_id=version_id,
            state_data=state_data,
            description=description
        )

        if version_id not in self.snapshots:
            self.snapshots[version_id] = []

        self.snapshots[version_id].append(snapshot)
        return snapshot

    def restore_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Restore from a snapshot"""
        for snapshots in self.snapshots.values():
            for snapshot in snapshots:
                if snapshot.snapshot_id == snapshot_id:
                    return snapshot.state_data

        return None

    def rollback_version(self, version_id: str) -> bool:
        """Rollback to a previous version"""
        if version_id not in self.versions:
            return False

        version = self.versions[version_id]

        # Can only rollback to archived or deprecated versions
        if version.status not in [VersionStatus.DEPRECATED, VersionStatus.ARCHIVED]:
            return False

        return self.activate_version(version_id)

    def get_version_history(self) -> List[Dict]:
        """Get version history"""
        return [
            {
                "version_id": v.version_id,
                "version_number": v.version_number,
                "name": v.name,
                "status": v.status.value,
                "created_at": v.created_at.isoformat(),
                "changelog": v.changelog
            }
            for v in sorted(
                self.versions.values(),
                key=lambda x: x.created_at,
                reverse=True
            )
        ]

    def get_snapshots(self, version_id: str) -> List[Dict]:
        """Get snapshots for a version"""
        snapshots = self.snapshots.get(version_id, [])
        return [
            {
                "snapshot_id": s.snapshot_id,
                "created_at": s.created_at.isoformat(),
                "description": s.description,
                "state_keys": list(s.state_data.keys())
            }
            for s in snapshots
        ]


# Demo
async def main():
    print("=" * 60)
    print("Day 63: Agent Versioning and State Management")
    print("=" * 60)

    manager = AgentVersionManager("agent_001")

    # Create versions
    v1 = manager.create_version(
        "1.0.0",
        "Initial Release",
        {"temperature": 0.7, "max_tokens": 1000},
        ["web_search", "calculator"],
        "You are a helpful assistant.",
        changelog=["Initial creation"]
    )
    print(f"\nCreated version: {v1.version_id}")

    v2 = manager.create_version(
        "1.1.0",
        "Added Tools",
        {"temperature": 0.7, "max_tokens": 1500},
        ["web_search", "calculator", "file_reader"],
        "You are a helpful assistant.",
        parent_version=v1.version_id,
        changelog=["Added file_reader tool", "Increased max_tokens"]
    )
    print(f"Created version: {v2.version_id}")

    # Activate version
    manager.activate_version(v1.version_id)
    print(f"\nActivated: {v1.version_id}")

    # Create snapshots
    snap1 = manager.create_snapshot(
        v1.version_id,
        {"memory": {"key": "value"}, "context": {}},
        "Before complex task"
    )
    print(f"Created snapshot: {snap1.snapshot_id}")

    snap2 = manager.create_snapshot(
        v1.version_id,
        {"memory": {"key": "new_value"}, "context": {"task": "analysis"}},
        "After complex task"
    )
    print(f"Created snapshot: {snap2.snapshot_id}")

    # Version history
    print("\n" + "-" * 40)
    print("Version History:")
    for v in manager.get_version_history():
        print(f"  {v['version_number']} - {v['name']} [{v['status']}]")
        for change in v['changelog']:
            print(f"    - {change}")

    # Restore snapshot
    print("\n" + "-" * 40)
    print("Restoring snapshot...")
    restored = manager.restore_snapshot(snap1.snapshot_id)
    print(f"Restored state: {restored}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())