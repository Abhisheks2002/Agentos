#!/usr/bin/env python3
"""
AgentOS - AI Agent Governance Platform
Main backend application
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import uuid

# Import session management
from core.session import (
    Session, SessionManager, SessionStatus, SessionEventEmitter,
    get_session_manager, init_session_manager
)

class Tier(Enum):
    STARTUP = "startup"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class Permission(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    EXECUTE_COMMANDS = "execute_commands"
    NETWORK_ACCESS = "network_access"
    REGISTRY_ACCESS = "registry_access"
    INSTALL_SOFTWARE = "install_software"

class AgentStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"

class AuditAction(Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    WARNING = "warning"

class Agent:
    def __init__(self, name: str, agent_type: str, description: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.type = agent_type
        self.description = description
        self.status = AgentStatus.ACTIVE
        self.tasks_completed = 0
        self.errors = 0
        self.created_at = datetime.now()
        self.last_run = datetime.now()
        self.permissions = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "status": self.status.value,
            "tasks_completed": self.tasks_completed,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat(),
            "permissions": self.permissions
        }

class Workflow:
    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.nodes = []
        self.status = "draft"
        self.created_at = datetime.now()

    def add_node(self, node_type: str, config: dict):
        self.nodes.append({
            "type": node_type,
            "config": config,
            "id": len(self.nodes) + 1
        })

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": self.nodes,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }

class AuditLog:
    def __init__(self, agent_id: str, action: str, details: str, status: AuditAction, reason: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.agent_id = agent_id
        self.action = action
        self.details = details
        self.status = status
        self.reason = reason
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "action": self.action,
            "details": self.details,
            "status": self.status.value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }

class GovernanceRule:
    def __init__(self, name: str, permission: Permission, action: str):
        self.name = name
        self.permission = permission
        self.action = action  # "allow", "block", "require_approval"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "permission": self.permission.value,
            "action": self.action
        }

class Organization:
    def __init__(self, name: str, tier: Tier):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.tier = tier
        self.agents = []
        self.workflows = []
        self.audit_logs = []
        self.governance_rules = self._get_default_rules()
        self.created_at = datetime.now()

    def _get_default_rules(self) -> List[GovernanceRule]:
        return [
            GovernanceRule("Auto-block system file deletion", Permission.FILE_WRITE, "block"),
            GovernanceRule("Auto-block registry modification", Permission.REGISTRY_ACCESS, "block"),
            GovernanceRule("Require approval for elevated commands", Permission.EXECUTE_COMMANDS, "require_approval"),
            GovernanceRule("Allow file read", Permission.FILE_READ, "allow"),
            GovernanceRule("Allow network access", Permission.NETWORK_ACCESS, "allow"),
        ]

    def get_tier_limits(self) -> dict:
        limits = {
            Tier.STARTUP: {"max_agents": 5, "max_workflows": 10, "storage": "1GB"},
            Tier.BUSINESS: {"max_agents": 25, "max_workflows": 100, "storage": "50GB"},
            Tier.ENTERPRISE: {"max_agents": -1, "max_workflows": -1, "storage": "Unlimited"}
        }
        return limits[self.tier]

    def can_add_agent(self) -> bool:
        limits = self.get_tier_limits()
        return limits["max_agents"] == -1 or len(self.agents) < limits["max_agents"]

    def add_agent(self, name: str, agent_type: str, description: str = "") -> Optional[Agent]:
        if not self.can_add_agent():
            return None
        agent = Agent(name, agent_type, description)
        self.agents.append(agent)
        return agent

    def check_permission(self, agent_id: str, permission: Permission) -> tuple[bool, str]:
        """Check if agent has permission, returns (allowed, reason)"""
        agent = next((a for a in self.agents if a.id == agent_id), None)
        if not agent:
            return False, "Agent not found"

        for rule in self.governance_rules:
            if rule.permission == permission:
                if rule.action == "block":
                    return False, f"Auto-blocked: {rule.name}"
                elif rule.action == "require_approval":
                    return False, f"Requires approval: {rule.name}"
                elif rule.action == "allow":
                    return True, "Allowed"

        return True, "Allowed"

    def log_action(self, agent_id: str, action: str, details: str, status: AuditAction, reason: str = ""):
        log = AuditLog(agent_id, action, details, status, reason)
        self.audit_logs.append(log)
        return log

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier.value,
            "agents_count": len(self.agents),
            "workflows_count": len(self.workflows),
            "created_at": self.created_at.isoformat()
        }

class AgentOS:
    """Main AgentOS Controller"""

    def __init__(self, session_timeout: int = 3600, max_sessions: int = 100):
        self.organizations = {}
        self.current_org = None
        # Initialize session manager
        self.session_manager = SessionManager(
            session_timeout=session_timeout,
            max_sessions=max_sessions
        )
        # Register session event handlers
        self._setup_session_events()

    def _setup_session_events(self):
        """Setup session event handlers"""
        def on_session_created(session):
            print(f"Session created: {session.session_id} for agent {session.agent_id}")

        def on_session_expired(session):
            print(f"Session expired: {session.session_id}")

        def on_session_deleted(session):
            print(f"Session deleted: {session.session_id}")

        self.session_manager.events.on("session_created", on_session_created)
        self.session_manager.events.on("session_expired", on_session_expired)
        self.session_manager.events.on("session_deleted", on_session_deleted)

    def create_organization(self, name: str, tier: Tier) -> Organization:
        org = Organization(name, tier)
        self.organizations[org.id] = org
        return org

    def get_organization(self, org_id: str) -> Optional[Organization]:
        return self.organizations.get(org_id)

    def request_agent_action(self, org_id: str, agent_id: str, action: str, details: dict) -> dict:
        """Process agent action request through governance layer"""
        org = self.get_organization(org_id)
        if not org:
            return {"status": "error", "message": "Organization not found"}

        # Map action to permission
        permission_map = {
            "read_file": Permission.FILE_READ,
            "write_file": Permission.FILE_WRITE,
            "execute": Permission.EXECUTE_COMMANDS,
            "network": Permission.NETWORK_ACCESS,
            "registry": Permission.REGISTRY_ACCESS,
            "install": Permission.INSTALL_SOFTWARE
        }

        permission = permission_map.get(action)
        if permission:
            allowed, reason = org.check_permission(agent_id, permission)
            if not allowed:
                org.log_action(agent_id, action, str(details), AuditAction.BLOCKED, reason)
                return {
                    "status": "blocked",
                    "message": reason,
                    "requires_approval": "require_approval" in reason
                }

        # Log allowed action
        org.log_action(agent_id, action, str(details), AuditAction.ALLOWED)
        return {"status": "allowed", "message": "Action permitted"}

    # Session Management Methods
    def create_agent_session(self, agent_id: str, metadata: dict = None) -> Session:
        """Create a new session for an agent"""
        return self.session_manager.create_session(agent_id, metadata)

    def get_agent_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        return self.session_manager.get_session(session_id)

    def update_agent_session(self, session_id: str) -> bool:
        """Update session activity"""
        return self.session_manager.update_session(session_id)

    def close_agent_session(self, session_id: str) -> bool:
        """Close and delete a session"""
        return self.session_manager.delete_session(session_id)

    def cleanup_sessions(self) -> int:
        """Cleanup expired sessions"""
        return self.session_manager.cleanup_expired_sessions()

    def get_session_stats(self) -> dict:
        """Get session statistics"""
        return self.session_manager.get_stats()


# Initialize default AgentOS instance
agentos = AgentOS()

# Demo: Create sample organizations
demo_org = agentos.create_organization("Acme Corp", Tier.STARTUP)
agent1 = demo_org.add_agent("DataProcessor", "Data Processing", "Processes business data")
agent2 = demo_org.add_agent("FileSync", "File Management", "Syncs files to cloud")

# Demo: Test governance
result = agentos.request_agent_action(demo_org.id, agent1.id, "execute", {"command": "rm -rf /"})
print(f"Execute command result: {result}")

result = agentos.request_agent_action(demo_org.id, agent1.id, "network", {"url": "api.example.com"})
print(f"Network access result: {result}")

# Export configuration
def export_config():
    config = {
        "version": "1.0.0",
        "tiers": {
            "startup": {"max_agents": 5, "price": "Free"},
            "business": {"max_agents": 25, "price": "$99/mo"},
            "enterprise": {"max_agents": -1, "price": "Custom"}
        },
        "governance": {
            "auto_block": ["delete_system_files", "modify_registry", "install_software"],
            "require_approval": ["execute_elevated_commands", "write_to_system_dirs"]
        }
    }
    return config

if __name__ == "__main__":
    print("AgentOS Core initialized")
    print(f"Demo organization: {demo_org.name}")
    print(f"Total agents: {len(demo_org.agents)}")
