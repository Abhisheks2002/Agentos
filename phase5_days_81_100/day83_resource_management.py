"""
Day 83: Agent Resource Management
==================================

Intelligent resource allocation and management for multi-agent systems.

Key Concepts:
- Resource pooling
- Dynamic allocation
- Load balancing
- Resource quotas
- Priority scheduling
- Resource monitoring
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import random


class ResourceType(Enum):
    """Types of resources"""
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    API_CALLS = "api_calls"
    CONCURRENT_TASKS = "concurrent_tasks"


class ResourceStatus(Enum):
    """Resource status"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    DEPLETED = "depleted"
    RESERVED = "reserved"


@dataclass
class Resource:
    """Represents a system resource"""
    resource_id: str
    resource_type: ResourceType
    capacity: float
    available: float
    unit: str
    status: ResourceStatus = ResourceStatus.AVAILABLE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceAllocation:
    """Resource allocation for an agent"""
    allocation_id: str
    agent_id: str
    resource_id: str
    resource_type: ResourceType
    amount: float
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class ResourceQuota:
    """Resource quota for an agent"""
    agent_id: str
    cpu_limit: float
    memory_limit: float
    storage_limit: float
    api_calls_limit: int
    concurrent_tasks_limit: int


class ResourcePool:
    """
    Resource Pool
    =============

    Manages a pool of resources.
    """

    def __init__(self, pool_name: str):
        self.pool_name = pool_name
        self.resources: Dict[str, Resource] = {}

    def add_resource(
        self,
        resource_type: ResourceType,
        capacity: float,
        unit: str
    ) -> Resource:
        """Add a resource to the pool"""
        resource = Resource(
            resource_id=str(uuid.uuid4())[:8],
            resource_type=resource_type,
            capacity=capacity,
            available=capacity,
            unit=unit
        )
        self.resources[resource.resource_id] = resource
        return resource

    def allocate(
        self,
        resource_type: ResourceType,
        amount: float
    ) -> Optional[Resource]:
        """Allocate resources of a specific type"""
        for resource in self.resources.values():
            if (
                resource.resource_type == resource_type and
                resource.status != ResourceStatus.DEPLETED and
                resource.available >= amount
            ):
                resource.available -= amount
                if resource.available <= 0:
                    resource.status = ResourceStatus.DEPLETED
                else:
                    resource.status = ResourceStatus.IN_USE
                return resource
        return None

    def release(
        self,
        resource_id: str,
        amount: float
    ):
        """Release allocated resources"""
        if resource_id in self.resources:
            resource = self.resources[resource_id]
            resource.available = min(
                resource.capacity,
                resource.available + amount
            )
            resource.status = ResourceStatus.AVAILABLE

    def get_available(
        self,
        resource_type: ResourceType
    ) -> float:
        """Get total available resources of a type"""
        return sum(
            r.available for r in self.resources.values()
            if r.resource_type == resource_type
        )

    def get_status(self) -> Dict[str, Any]:
        """Get pool status"""
        status = {}
        for resource_type in ResourceType:
            resources = [
                r for r in self.resources.values()
                if r.resource_type == resource_type
            ]
            if resources:
                status[resource_type.value] = {
                    "total": sum(r.capacity for r in resources),
                    "available": sum(r.available for r in resources),
                    "count": len(resources)
                }
        return status


class QuotaManager:
    """
    Quota Manager
    =============

    Manages resource quotas per agent.
    """

    def __init__(self):
        self.quotas: Dict[str, ResourceQuota] = {}
        self.usage: Dict[str, Dict[str, float]] = {}

    def set_quota(self, quota: ResourceQuota):
        """Set quota for an agent"""
        self.quotas[quota.agent_id] = quota
        self.usage[quota.agent_id] = {
            "cpu": 0,
            "memory": 0,
            "storage": 0,
            "api_calls": 0,
            "concurrent_tasks": 0
        }

    def check_quota(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: float
    ) -> bool:
        """Check if agent can allocate resource"""
        if agent_id not in self.quotas:
            return True  # No quota set, allow all

        quota = self.quotas[agent_id]
        current = self.usage.get(agent_id, {}).get(resource_type.value, 0)

        limits = {
            ResourceType.CPU: quota.cpu_limit,
            ResourceType.MEMORY: quota.memory_limit,
            ResourceType.STORAGE: quota.storage_limit,
            ResourceType.API_CALLS: quota.api_calls_limit,
            ResourceType.CONCURRENT_TASKS: quota.concurrent_tasks_limit,
            ResourceType.NETWORK: quota.api_calls_limit
        }

        limit = limits.get(resource_type, float('inf'))
        return (current + amount) <= limit

    def allocate(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: float
    ) -> bool:
        """Allocate resource and track usage"""
        if not self.check_quota(agent_id, resource_type, amount):
            return False

        if agent_id not in self.usage:
            self.usage[agent_id] = {
                "cpu": 0, "memory": 0, "storage": 0,
                "api_calls": 0, "concurrent_tasks": 0
            }

        self.usage[agent_id][resource_type.value] += amount
        return True

    def release(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: float
    ):
        """Release resource and update usage"""
        if agent_id in self.usage:
            self.usage[agent_id][resource_type.value] = max(
                0,
                self.usage[agent_id][resource_type.value] - amount
            )


class ResourceScheduler:
    """
    Resource Scheduler
    ==================

    Schedules resource allocation based on priority.
    """

    def __init__(self):
        self.pending_requests: List[ResourceAllocation] = []
        self.active_allocations: Dict[str, ResourceAllocation] = {}

    def request_allocation(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: float,
        priority: int = 5
    ) -> str:
        """Request resource allocation"""
        allocation = ResourceAllocation(
            allocation_id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            resource_id="",
            resource_type=resource_type,
            amount=amount,
            priority=priority
        )
        self.pending_requests.append(allocation)
        # Sort by priority (higher first)
        self.pending_requests.sort(key=lambda x: x.priority, reverse=True)
        return allocation.allocation_id

    def process_allocation(
        self,
        allocation: ResourceAllocation,
        resource: Resource
    ) -> bool:
        """Process a pending allocation"""
        allocation.resource_id = resource.resource_id
        self.active_allocations[allocation.allocation_id] = allocation
        if allocation.allocation_id in self.pending_requests:
            self.pending_requests.remove(allocation)
        return True

    def release_allocation(self, allocation_id: str):
        """Release an allocation"""
        if allocation_id in self.active_allocations:
            del self.active_allocations[allocation_id]


class AgentResourceManager:
    """
    Agent Resource Manager
    ======================

    Main resource management system.
    """

    def __init__(self):
        self.pools: Dict[str, ResourcePool] = {
            "default": ResourcePool("default")
        }
        self.quota_manager = QuotaManager()
        self.scheduler = ResourceScheduler()
        self._initialize_default_resources()

    def _initialize_default_resources(self):
        """Initialize default resource pools"""
        pool = self.pools["default"]

        # Add default resources
        pool.add_resource(ResourceType.CPU, 100, "cores")
        pool.add_resource(ResourceType.MEMORY, 64, "GB")
        pool.add_resource(ResourceType.STORAGE, 1000, "GB")
        pool.add_resource(ResourceType.NETWORK, 1000, "Mbps")
        pool.add_resource(ResourceType.API_CALLS, 10000, "calls/hour")
        pool.add_resource(ResourceType.CONCURRENT_TASKS, 50, "tasks")

    def allocate_resource(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: float,
        priority: int = 5
    ) -> Dict[str, Any]:
        """Allocate resource for an agent"""
        # Check quota first
        if not self.quota_manager.check_quota(agent_id, resource_type, amount):
            return {
                "success": False,
                "reason": "quota_exceeded"
            }

        # Request from scheduler
        allocation_id = self.scheduler.request_allocation(
            agent_id, resource_type, amount, priority
        )

        # Try to allocate from pool
        pool = self.pools["default"]
        resource = pool.allocate(resource_type, amount)

        if resource:
            # Track quota usage
            self.quota_manager.allocate(agent_id, resource_type, amount)

            # Process scheduler allocation
            allocation = ResourceAllocation(
                allocation_id=allocation_id,
                agent_id=agent_id,
                resource_id=resource.resource_id,
                resource_type=resource_type,
                amount=amount,
                priority=priority
            )
            self.scheduler.process_allocation(allocation, resource)

            return {
                "success": True,
                "allocation_id": allocation_id,
                "resource_id": resource.resource_id,
                "amount": amount
            }
        else:
            return {
                "success": False,
                "reason": "resources_unavailable"
            }

    def release_resource(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: float,
        resource_id: str = None
    ):
        """Release allocated resources"""
        # Release from pool
        pool = self.pools["default"]
        if resource_id:
            pool.release(resource_id, amount)

        # Release from quota
        self.quota_manager.release(agent_id, resource_type, amount)

    def set_agent_quota(self, agent_id: str, quota: ResourceQuota):
        """Set quota for an agent"""
        self.quota_manager.set_quota(quota)

    def get_status(self) -> Dict[str, Any]:
        """Get resource manager status"""
        return {
            "pools": {
                name: pool.get_status()
                for name, pool in self.pools.items()
            },
            "pending_requests": len(self.scheduler.pending_requests),
            "active_allocations": len(self.scheduler.active_allocations)
        }


def main():
    """Demonstrate Resource Management"""
    print("=" * 60)
    print("Agent Resource Management - Day 83")
    print("=" * 60)

    # Initialize manager
    manager = AgentResourceManager()

    # Set agent quotas
    manager.set_agent_quota("agent_001", ResourceQuota(
        agent_id="agent_001",
        cpu_limit=20,
        memory_limit=16,
        storage_limit=200,
        api_calls_limit=1000,
        concurrent_tasks_limit=10
    ))

    print("\n[Resource Status]")
    status = manager.get_status()
    for pool_name, pool_status in status["pools"].items():
        print(f"  Pool: {pool_name}")
        for res_type, res_info in pool_status.items():
            print(f"    {res_type}: {res_info['available']}/{res_info['total']} {res_info.get('unit', '')}")

    # Allocate resources
    print("\n[Allocating Resources]")
    result = manager.allocate_resource(
        "agent_001",
        ResourceType.CPU,
        5,
        priority=8
    )
    print(f"  CPU Allocation: {result}")

    result = manager.allocate_resource(
        "agent_001",
        ResourceType.MEMORY,
        8,
        priority=7
    )
    print(f"  Memory Allocation: {result}")

    # Check final status
    print("\n[Final Resource Status]")
    final_status = manager.get_status()
    for pool_name, pool_status in final_status["pools"].items():
        for res_type, res_info in pool_status.items():
            print(f"  {res_type}: {res_info['available']}/{res_info['total']}")

    print("\n" + "=" * 60)
    print("Resource management demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()