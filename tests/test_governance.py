"""Tests for AgentOS Governance."""

import pytest
import asyncio
from core.governance.governance import GovernanceEngine, Permission


@pytest.fixture
def governance():
    """Create a governance engine instance."""
    return GovernanceEngine()


@pytest.mark.asyncio
async def test_create_user(governance):
    """Test user creation."""
    user = await governance.create_user(
        username="testuser",
        email="test@example.com",
        role="user"
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == "user"


@pytest.mark.asyncio
async def test_get_user(governance):
    """Test getting a user."""
    user = await governance.create_user(username="testuser")
    retrieved = await governance.get_user("testuser")

    assert retrieved is not None
    assert retrieved.username == "testuser"


@pytest.mark.asyncio
async def test_permission_check(governance):
    """Test permission checking."""
    user = await governance.create_user(username="testuser", role="user")

    # User with 'user' role should have AGENT_CREATE
    has_perm = await governance.check_permission(
        user.id,
        Permission.AGENT_CREATE
    )
    assert has_perm is True

    # But not ADMIN
    has_perm = await governance.check_permission(
        user.id,
        Permission.ADMIN
    )
    assert has_perm is False


@pytest.mark.asyncio
async def test_admin_permissions(governance):
    """Test admin role has all permissions."""
    admin = await governance.create_user(username="admin", role="admin")

    # Admin should have all permissions
    for perm in Permission:
        has_perm = await governance.check_permission(admin.id, perm)
        assert has_perm is True


@pytest.mark.asyncio
async def test_create_role(governance):
    """Test creating a custom role."""
    role = await governance.create_role(
        name="developer",
        permissions=[
            Permission.AGENT_CREATE,
            Permission.AGENT_READ,
            Permission.TOOL_USE
        ]
    )

    assert role.name == "developer"
    assert Permission.AGENT_CREATE in role.permissions


@pytest.mark.asyncio
async def test_audit_logging(governance):
    """Test audit logging."""
    user = await governance.create_user(username="testuser")

    # Perform some actions that should be logged
    await governance.check_permission(user.id, Permission.AGENT_CREATE)

    logs = await governance.get_audit_logs(user_id=user.id)
    assert len(logs) > 0


@pytest.mark.asyncio
async def test_content_safety(governance):
    """Test content safety check."""
    # Safe content
    result = await governance.check_content_safety("Hello world")
    assert result["safe"] is True

    # Content with violations
    result = await governance.check_content_safety("This is malicious content")
    assert result["safe"] is False
    assert len(result["violations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
