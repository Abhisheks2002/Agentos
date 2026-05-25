"""Governance Layer - RBAC, permissions, and audit logging."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import logging

from ..models.models import User, PermissionLevel, AuditLog

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions."""
    # Agent permissions
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"

    # Tool permissions
    TOOL_REGISTER = "tool:register"
    TOOL_USE = "tool:use"

    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"

    # Workflow permissions
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_EXECUTE = "workflow:execute"

    # Admin permissions
    ADMIN = "admin"
    AUDIT_READ = "audit:read"


class Role:
    """Role with associated permissions."""

    def __init__(self, name: str, permissions: List[str] = None):
        self.name = name
        self.permissions: Set[str] = set(permissions or [])

    def add_permission(self, permission: str):
        self.permissions.add(permission)

    def remove_permission(self, permission: str):
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        # Admin has all permissions
        if Permission.ADMIN in self.permissions:
            return True
        return permission in self.permissions


class GovernanceEngine:
    """
    Governance engine with RBAC, permissions, and audit logging.
    """

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._roles: Dict[str, Role] = {}
        self._audit_logs: List[AuditLog] = []
        self._default_role = "user"

        # Initialize default roles
        self._init_default_roles()

    def _init_default_roles(self):
        """Initialize default roles."""
        # Admin role
        admin = Role("admin", [Permission.ADMIN, Permission.AUDIT_READ])
        admin.permissions.update([
            Permission.AGENT_CREATE, Permission.AGENT_READ,
            Permission.AGENT_UPDATE, Permission.AGENT_DELETE,
            Permission.AGENT_EXECUTE, Permission.TOOL_REGISTER,
            Permission.TOOL_USE, Permission.MEMORY_READ,
            Permission.MEMORY_WRITE, Permission.MEMORY_DELETE,
            Permission.WORKFLOW_CREATE, Permission.WORKFLOW_EXECUTE
        ])
        self._roles["admin"] = admin

        # User role
        user = Role("user", [
            Permission.AGENT_CREATE, Permission.AGENT_READ,
            Permission.AGENT_UPDATE, Permission.AGENT_EXECUTE,
            Permission.TOOL_USE, Permission.MEMORY_READ,
            Permission.MEMORY_WRITE, Permission.WORKFLOW_CREATE,
            Permission.WORKFLOW_EXECUTE
        ])
        self._roles["user"] = user

        # Guest role
        guest = Role("guest", [
            Permission.AGENT_READ, Permission.MEMORY_READ
        ])
        self._roles["guest"] = guest

        logger.info("Initialized default roles")

    # --- User Management ---

    async def create_user(
        self,
        username: str,
        email: str = None,
        role: str = None
    ) -> User:
        """Create a new user."""
        user = User(
            id=f"user_{uuid.uuid4().hex[:12]}",
            username=username,
            email=email,
            role=role or self._default_role,
            permissions=[]
        )
        self._users[user.id] = user
        self._users[username] = user  # Also index by username

        await self._log_audit(
            user_id=user.id,
            action="user_created",
            resource="user",
            resource_id=user.id,
            details={"username": username, "role": role}
        )

        logger.info(f"Created user: {username}")
        return user

    async def get_user(self, identifier: str) -> Optional[User]:
        """Get user by ID or username."""
        return self._users.get(identifier)

    async def list_users(self) -> List[User]:
        """List all users."""
        # Return unique users
        seen = set()
        users = []
        for user in self._users.values():
            if user.id not in seen:
                seen.add(user.id)
                users.append(user)
        return users

    async def update_user_role(self, user_id: str, role: str) -> bool:
        """Update user role."""
        user = self._users.get(user_id)
        if not user:
            return False
        user.role = role

        await self._log_audit(
            user_id=user_id,
            action="role_updated",
            resource="user",
            resource_id=user_id,
            details={"new_role": role}
        )
        return True

    # --- Permission Checking ---

    async def check_permission(
        self,
        user_id: str,
        permission: Permission
    ) -> bool:
        """Check if user has a specific permission."""
        user = self._users.get(user_id)
        if not user:
            return False

        role = self._roles.get(user.role)
        if not role:
            return False

        has_perm = role.has_permission(permission.value)

        await self._log_audit(
            user_id=user_id,
            action="permission_check",
            resource="permission",
            details={
                "permission": permission.value,
                "granted": has_perm
            }
        )

        return has_perm

    async def require_permission(
        self,
        user_id: str,
        permission: Permission
    ):
        """Require a permission or raise an error."""
        if not await self.check_permission(user_id, permission):
            raise PermissionError(
                f"User {user_id} does not have permission: {permission.value}"
            )

    # --- Role Management ---

    async def create_role(
        self,
        name: str,
        permissions: List[str] = None
    ) -> Role:
        """Create a new role."""
        role = Role(name, permissions)
        self._roles[name] = role
        logger.info(f"Created role: {name}")
        return role

    async def get_role(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self._roles.get(name)

    async def update_role_permissions(
        self,
        role_name: str,
        permissions: List[str]
    ) -> bool:
        """Update role permissions."""
        role = self._roles.get(role_name)
        if not role:
            return False
        role.permissions = set(permissions)
        return True

    # --- Audit Logging ---

    async def _log_audit(
        self,
        user_id: str,
        action: str,
        resource: str,
        resource_id: str = None,
        details: Dict[str, Any] = None
    ):
        """Log an audit event."""
        log = AuditLog(
            id=f"log_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details or {}
        )
        self._audit_logs.append(log)

    async def get_audit_logs(
        self,
        user_id: str = None,
        resource: str = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filters."""
        logs = self._audit_logs

        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        if resource:
            logs = [l for l in logs if l.resource == resource]

        return logs[-limit:]

    # --- Safety Guardrails ---

    async def check_content_safety(self, content: str) -> Dict[str, Any]:
        """
        Check content for safety violations.
        In production, this would integrate with content moderation APIs.
        """
        # Simple placeholder - in production use moderation APIs
        blocked_words = ["malicious", "harmful"]  # Example

        content_lower = content.lower()
        violations = [word for word in blocked_words if word in content_lower]

        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "checked_at": datetime.now().isoformat()
        }

    # --- Tool Permission Checking ---

    async def check_tool_permission(
        self,
        tool_name: str,
        permissions: List[str],
        parameters: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Check if a tool execution is allowed based on governance rules.

        Args:
            tool_name: Name of the tool to check
            permissions: Required permissions for the tool
            parameters: Parameters being passed to the tool
            context: Execution context (agent_id, user_id, etc.)

        Returns:
            Dict with 'allowed' (bool) and optional 'reason'
        """
        # Get user context
        user_id = context.get("user_id") if context else None
        agent_id = context.get("agent_id") if context else None

        # Check each required permission
        for perm in permissions:
            # Map tool permissions to system permissions
            if perm == "file_read":
                has_perm = await self._check_permission_by_name(user_id, Permission.MEMORY_READ)
            elif perm == "file_write":
                has_perm = await self._check_permission_by_name(user_id, Permission.MEMORY_WRITE)
            elif perm == "network":
                has_perm = await self._check_permission_by_name(user_id, Permission.TOOL_USE)
            elif perm == "execute_commands":
                has_perm = await self._check_permission_by_name(user_id, Permission.AGENT_EXECUTE)
            elif perm == "read_system_info":
                has_perm = await self._check_permission_by_name(user_id, Permission.AGENT_READ)
            elif perm in ["read_user_data", "write_user_data", "read_business_data", "write_business_data"]:
                has_perm = await self._check_permission_by_name(user_id, Permission.MEMORY_READ)
            else:
                has_perm = await self._check_permission_by_name(user_id, Permission.TOOL_USE)

            if not has_perm:
                reason = f"Missing required permission: {perm}"
                await self._log_audit(
                    user_id=user_id or "system",
                    action="tool_permission_denied",
                    resource="tool",
                    resource_id=tool_name,
                    details={"permission": perm, "tool": tool_name}
                )
                return {"allowed": False, "reason": reason}

        # Check for dangerous parameter patterns
        if parameters:
            dangerous = self._check_dangerous_parameters(tool_name, parameters)
            if dangerous:
                return {"allowed": False, "reason": dangerous}

        # Log the tool execution permission check
        await self._log_audit(
            user_id=user_id or "system",
            action="tool_permission_checked",
            resource="tool",
            resource_id=tool_name,
            details={
                "tool": tool_name,
                "permissions": permissions,
                "allowed": True,
                "agent_id": agent_id
            }
        )

        return {"allowed": True}

    async def _check_permission_by_name(
        self,
        user_id: Optional[str],
        permission: Permission
    ) -> bool:
        """Check if user has a specific permission by name."""
        if not user_id:
            # No user context, allow by default for system operations
            return True

        user = await self.get_user(user_id)
        if not user:
            return False

        role = await self.get_role(user.role)
        if not role:
            return False

        return role.has_permission(permission.value)

    def _check_dangerous_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """Check for dangerous parameter patterns."""
        # File operations - check for dangerous paths
        if tool_name in ["file_read", "file_write", "file_delete"]:
            path = parameters.get("path", "")
            if not path:
                return None

            # Check for system paths
            dangerous_paths = [
                "/etc/",
                "/sys/",
                "/proc/",
                "C:\\Windows",
                "C:\\Program Files",
                "/System",
                "/Library"
            ]
            for dp in dangerous_paths:
                if dp.lower() in path.lower():
                    return f"Dangerous path detected: {path}"

        # Command execution - check for dangerous commands
        if tool_name == "execute_command":
            command = parameters.get("command", "")
            dangerous_cmds = ["rm -rf", "del /", "format", "mkfs", "> /dev/sd"]
            for dc in dangerous_cmds:
                if dc.lower() in command.lower():
                    return f"Dangerous command detected: {command[:50]}"

        return None

    async def check_rate_limit(
        self,
        user_id: str,
        action: str,
        window_seconds: int = 60,
        max_requests: int = 100
    ) -> bool:
        """
        Check if user has exceeded rate limit.
        Simple in-memory implementation.
        """
        # In production, use Redis for distributed rate limiting
        return True  # Placeholder

    async def check_tool_permission(
        self,
        tool_name: str,
        permissions: List[str],
        parameters: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Check if tool execution is allowed by governance rules.

        Args:
            tool_name: Name of the tool
            permissions: Required permissions for the tool
            parameters: Parameters being passed to the tool
            context: Execution context (agent_id, user_id, etc.)

        Returns:
            Dict with 'allowed' (bool) and optional 'reason'
        """
        context = context or {}
        user_id = context.get("user_id")
        agent_id = context.get("agent_id")

        # Check required permissions
        if user_id:
            user = await self.get_user(user_id)
            if user:
                role = await self.get_role(user.role)
                if role:
                    # Check if role has all required permissions
                    for permission in permissions:
                        if not role.has_permission(permission):
                            await self._log_audit(
                                user_id=user_id,
                                action="tool_permission_denied",
                                resource="tool",
                                resource_id=tool_name,
                                details={
                                    "permissions_required": permissions,
                                    "missing_permission": permission
                                }
                            )
                            return {
                                "allowed": False,
                                "reason": f"Missing permission: {permission}"
                            }

        # Check for dangerous operations in parameters
        if parameters:
            danger_check = self._check_dangerous_parameters(tool_name, parameters)
            if not danger_check.get("safe", True):
                await self._log_audit(
                    user_id=user_id or "unknown",
                    action="dangerous_tool_params_blocked",
                    resource="tool",
                    resource_id=tool_name,
                    details={"parameters": parameters, "warnings": danger_check.get("warnings")}
                )
                return {
                    "allowed": False,
                    "reason": f"Dangerous parameters detected: {danger_check.get('warnings')}"
                }

        # Log allowed tool execution
        await self._log_audit(
            user_id=user_id or "unknown",
            action="tool_execution_allowed",
            resource="tool",
            resource_id=tool_name,
            details={
                "permissions": parameters,
                "agent_id": agent_id
            }
        )

        return {"allowed": True}

    def _check_dangerous_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for dangerous patterns in tool parameters.
        Simple pattern matching for common attack vectors.
        """
        warnings = []
        dangerous_patterns = [
            ("..", "Path traversal"),
            ("/etc/passwd", "System file access"),
            ("C:\\Windows", "Windows system file"),
            ("rm -rf", "Destructive command"),
            ("del /s", "Recursive delete"),
            ("format", "Disk format"),
        ]

        # Check path parameters
        if tool_name in ("file_read", "file_write", "file_delete", "list_directory", "execute_command", "run_script"):
            path_param = parameters.get("path") or parameters.get("command") or ""
            for pattern, warning in dangerous_patterns:
                if pattern in path_param:
                    warnings.append(f"{warning}: contains '{pattern}'")

        return {
            "safe": len(warnings) == 0,
            "warnings": warnings
        }


# Global governance engine instance
_governance: Optional[GovernanceEngine] = None


def get_governance_engine() -> GovernanceEngine:
    """Get the global governance engine instance."""
    global _governance
    if _governance is None:
        _governance = GovernanceEngine()
    return _governance
