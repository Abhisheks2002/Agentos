"""
Day 68: Multi-Tenancy Support
==============================
Implementing multi-tenant architecture for agent isolation.

Key Concepts:
- Tenant isolation
- Resource quotas
- Tenant-specific configurations
- Cross-tenant access control
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class TenantStatus(Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    DELETED = "deleted"


class PlanType(Enum):
    """Subscription plans"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class ResourceQuota:
    """Resource quotas for a tenant"""
    max_agents: int = 5
    max_tasks_per_day: int = 100
    max_storage_mb: int = 100
    max_concurrent_tasks: int = 3
    api_rate_limit: int = 60  # requests per minute


@dataclass
class Tenant:
    """Tenant entity"""
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.TRIAL
    plan: PlanType = PlanType.FREE
    quota: ResourceQuota = field(default_factory=ResourceQuota)
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageRecord:
    """Usage tracking record"""
    tenant_id: str
    resource_type: str
    amount: int
    timestamp: datetime = field(default_factory=datetime.now)


class TenantManager:
    """
    Multi-Tenant Manager
    ====================

    Manages tenant isolation, quotas, and configurations.
    """

    PLAN_QUOTAS = {
        PlanType.FREE: ResourceQuota(
            max_agents=3,
            max_tasks_per_day=50,
            max_storage_mb=50,
            max_concurrent_tasks=2,
            api_rate_limit=30
        ),
        PlanType.STARTER: ResourceQuota(
            max_agents=10,
            max_tasks_per_day=500,
            max_storage_mb=500,
            max_concurrent_tasks=5,
            api_rate_limit=120
        ),
        PlanType.PROFESSIONAL: ResourceQuota(
            max_agents=50,
            max_tasks_per_day=5000,
            max_storage_mb=5000,
            max_concurrent_tasks=20,
            api_rate_limit=300
        ),
        PlanType.ENTERPRISE: ResourceQuota(
            max_agents=-1,  # Unlimited
            max_tasks_per_day=-1,
            max_storage_mb=-1,
            max_concurrent_tasks=-1,
            api_rate_limit=-1
        )
    }

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.usage: Dict[str, List[UsageRecord]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def create_tenant(
        self,
        name: str,
        plan: PlanType = PlanType.FREE,
        metadata: Dict[str, Any] = None
    ) -> Tenant:
        """Create a new tenant"""
        async with self._lock:
            tenant = Tenant(
                tenant_id=str(uuid.uuid4()),
                name=name,
                plan=plan,
                quota=self.PLAN_QUOTAS[plan].__copy__(),
                metadata=metadata or {}
            )

            self.tenants[tenant.tenant_id] = tenant
            return tenant

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)

    async def update_plan(
        self,
        tenant_id: str,
        plan: PlanType
    ) -> bool:
        """Update tenant plan"""
        async with self._lock:
            if tenant_id not in self.tenants:
                return False

            tenant = self.tenants[tenant_id]
            tenant.plan = plan
            tenant.quota = self.PLAN_QUOTAS[plan].__copy__()
            return True

    async def check_quota(
        self,
        tenant_id: str,
        resource_type: str,
        amount: int = 1
    ) -> bool:
        """Check if tenant can use resource"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant or tenant.status != TenantStatus.ACTIVE:
            return False

        quota = tenant.quota

        if resource_type == "agents":
            current = len([
                r for r in self.usage[tenant_id]
                if r.resource_type == "agents"
            ])
            return current < quota.max_agents or quota.max_agents == -1

        elif resource_type == "tasks":
            today = datetime.now().date()
            today_usage = sum(
                r.amount for r in self.usage[tenant_id]
                if r.resource_type == "tasks" and r.timestamp.date() == today
            )
            return today_usage + amount <= quota.max_tasks_per_day or quota.max_tasks_per_day == -1

        elif resource_type == "concurrent":
            return True  # Handled separately

        return True

    async def record_usage(
        self,
        tenant_id: str,
        resource_type: str,
        amount: int = 1
    ):
        """Record resource usage"""
        async with self._lock:
            record = UsageRecord(
                tenant_id=tenant_id,
                resource_type=resource_type,
                amount=amount
            )
            self.usage[tenant_id].append(record)

    async def get_usage_summary(
        self,
        tenant_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get usage summary for tenant"""
        cutoff = datetime.now() - timedelta(days=days)
        tenant_usage = self.usage.get(tenant_id, [])

        recent = [r for r in tenant_usage if r.timestamp >= cutoff]

        summary = defaultdict(int)
        for r in recent:
            summary[r.resource_type] += r.amount

        tenant = await self.get_tenant(tenant_id)
        quota = tenant.quota if tenant else ResourceQuota()

        return {
            "period_days": days,
            "usage": dict(summary),
            "quota": {
                "max_agents": quota.max_agents,
                "max_tasks_per_day": quota.max_tasks_per_day,
                "max_storage_mb": quota.max_storage_mb,
                "api_rate_limit": quota.api_rate_limit
            }
        }

    async def suspend_tenant(self, tenant_id: str) -> bool:
        """Suspend tenant"""
        async with self._lock:
            if tenant_id not in self.tenants:
                return False

            self.tenants[tenant_id].status = TenantStatus.SUSPENDED
            return True

    async def activate_tenant(self, tenant_id: str) -> bool:
        """Activate tenant"""
        async with self._lock:
            if tenant_id not in self.tenants:
                return False

            self.tenants[tenant_id].status = TenantStatus.ACTIVE
            return True


class TenantIsolation:
    """
    Tenant Isolation Manager
    ========================

    Provides data isolation between tenants.
    """

    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self.data_store: Dict[str, Dict[str, Any]] = defaultdict(dict)

    async def store(
        self,
        tenant_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Store data for tenant"""
        # Check quota
        if not await self.tenant_manager.check_quota(tenant_id, "storage"):
            return False

        self.data_store[tenant_id][key] = value
        return True

    async def retrieve(
        self,
        tenant_id: str,
        key: str
    ) -> Optional[Any]:
        """Retrieve data for tenant (isolated)"""
        return self.data_store.get(tenant_id, {}).get(key)

    async def list_keys(self, tenant_id: str) -> List[str]:
        """List all keys for tenant"""
        return list(self.data_store.get(tenant_id, {}).keys())

    async def delete(self, tenant_id: str, key: str) -> bool:
        """Delete data for tenant"""
        if key in self.data_store.get(tenant_id, {}):
            del self.data_store[tenant_id][key]
            return True
        return False


# Demo
async def main():
    print("=" * 60)
    print("Day 68: Multi-Tenancy Support")
    print("=" * 60)

    manager = TenantManager()
    isolation = TenantIsolation(manager)

    # Create tenants
    tenant1 = await manager.create_tenant(
        "Acme Corp",
        PlanType.PROFESSIONAL,
        {"industry": "finance"}
    )

    tenant2 = await manager.create_tenant(
        "StartupXYZ",
        PlanType.FREE,
        {"industry": "tech"}
    )

    print(f"\nCreated tenants:")
    print(f"  - {tenant1.name} ({tenant1.plan.value})")
    print(f"  - {tenant2.name} ({tenant2.plan.value})")

    # Check quotas
    print(f"\nQuota check for {tenant1.name}:")
    can_create = await manager.check_quota(tenant1.tenant_id, "agents", 1)
    print(f"  Can create agent: {can_create}")

    # Record usage
    await manager.record_usage(tenant1.tenant_id, "tasks", 10)
    await manager.record_usage(tenant1.tenant_id, "tasks", 5)

    # Store isolated data
    await isolation.store(tenant1.tenant_id, "config", {"theme": "dark"})
    await isolation.store(tenant2.tenant_id, "config", {"theme": "light"})

    print(f"\nIsolated data:")
    config1 = await isolation.retrieve(tenant1.tenant_id, "config")
    config2 = await isolation.retrieve(tenant2.tenant_id, "config")
    print(f"  {tenant1.name} config: {config1}")
    print(f"  {tenant2.name} config: {config2}")

    # Usage summary
    summary = await manager.get_usage_summary(tenant1.tenant_id)
    print(f"\nUsage summary for {tenant1.name}:")
    print(f"  Tasks: {summary['usage'].get('tasks', 0)}")
    print(f"  Quota: {summary['quota']['max_tasks_per_day']}")


if __name__ == "__main__":
    asyncio.run(main())