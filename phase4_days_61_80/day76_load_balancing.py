"""
Day 76: Load Balancing
======================
Intelligent load balancing for agent distribution.

Key Concepts:
- Round-robin distribution
- Weighted routing
- Health-aware balancing
- Least connections
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import hashlib


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    RANDOM = "random"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


@dataclass
class AgentEndpoint:
    """Agent endpoint for load balancing"""
    agent_id: str
    host: str
    port: int
    weight: int = 1
    healthy: bool = True
    active_connections: int = 0
    avg_response_time: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0


class LoadBalancer:
    """
    Load Balancer
    =============

    Distributes requests across agent endpoints.
    """

    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.endpoints: Dict[str, AgentEndpoint] = {}
        self._current_index = 0

    def add_endpoint(
        self,
        agent_id: str,
        host: str,
        port: int,
        weight: int = 1
    ):
        """Add an endpoint"""
        endpoint = AgentEndpoint(
            agent_id=agent_id,
            host=host,
            port=port,
            weight=weight
        )
        self.endpoints[agent_id] = endpoint

    def remove_endpoint(self, agent_id: str):
        """Remove an endpoint"""
        if agent_id in self.endpoints:
            del self.endpoints[agent_id]

    def get_endpoint(
        self,
        client_id: str = None,
        exclude_unhealthy: bool = True
    ) -> Optional[AgentEndpoint]:
        """Get next endpoint based on strategy"""
        healthy = [e for e in self.endpoints.values()
                   if not exclude_unhealthy or e.healthy]

        if not healthy:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(healthy)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(healthy)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            return self._weighted(healthy)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random(healthy)
        elif self.strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash(healthy, client_id or "default")
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time(healthy)

        return healthy[0]

    def _round_robin(self, endpoints: List[AgentEndpoint]) -> AgentEndpoint:
        """Round-robin selection"""
        endpoint = endpoints[self._current_index % len(endpoints)]
        self._current_index += 1
        return endpoint

    def _least_connections(self, endpoints: List[AgentEndpoint]) -> AgentEndpoint:
        """Least connections - route to endpoint with fewest active connections"""
        return min(endpoints, key=lambda e: e.active_connections)

    def _weighted(self, endpoints: List[AgentEndpoint]) -> AgentEndpoint:
        """Weighted selection based on weight"""
        total_weight = sum(e.weight for e in endpoints)
        if total_weight == 0:
            return endpoints[0]

        rand = random.uniform(0, total_weight)
        cumulative = 0

        for endpoint in endpoints:
            cumulative += endpoint.weight
            if rand <= cumulative:
                return endpoint

        return endpoints[-1]

    def _random(self, endpoints: List[AgentEndpoint]) -> AgentEndpoint:
        """Random selection"""
        return random.choice(endpoints)

    def _ip_hash(self, endpoints: List[AgentEndpoint], client_id: str) -> AgentEndpoint:
        """IP hash - consistent hashing based on client IP"""
        hash_value = int(hashlib.md5(client_id.encode()).hexdigest(), 16)
        index = hash_value % len(endpoints)
        return endpoints[index]

    def _least_response_time(self, endpoints: List[AgentEndpoint]) -> AgentEndpoint:
        """Least response time"""
        return min(endpoints, key=lambda e: e.avg_response_time or float('inf'))

    def record_request_start(self, agent_id: str):
        """Record request start"""
        if agent_id in self.endpoints:
            self.endpoints[agent_id].active_connections += 1
            self.endpoints[agent_id].total_requests += 1

    def record_request_end(
        self,
        agent_id: str,
        response_time_ms: float,
        success: bool = True
    ):
        """Record request completion"""
        if agent_id not in self.endpoints:
            return

        endpoint = self.endpoints[agent_id]
        endpoint.active_connections = max(0, endpoint.active_connections - 1)

        if success:
            # Update average response time
            total = endpoint.total_requests - endpoint.failed_requests
            if total > 0:
                endpoint.avg_response_time = (
                    (endpoint.avg_response_time * (total - 1) + response_time_ms) / total
                )
        else:
            endpoint.failed_requests += 1

        # Mark unhealthy if too many failures
        if endpoint.total_requests > 10:
            failure_rate = endpoint.failed_requests / endpoint.total_requests
            endpoint.healthy = failure_rate < 0.5

    def get_status(self) -> Dict[str, Any]:
        """Get load balancer status"""
        return {
            "strategy": self.strategy.value,
            "total_endpoints": len(self.endpoints),
            "healthy_endpoints": sum(1 for e in self.endpoints.values() if e.healthy),
            "endpoints": [
                {
                    "agent_id": e.agent_id,
                    "host": e.host,
                    "port": e.port,
                    "weight": e.weight,
                    "healthy": e.healthy,
                    "active_connections": e.active_connections,
                    "avg_response_time": e.avg_response_time,
                    "total_requests": e.total_requests,
                    "failed_requests": e.failed_requests,
                    "failure_rate": e.failed_requests / max(1, e.total_requests)
                }
                for e in self.endpoints.values()
            ]
        }


class AgentPool:
    """
    Agent Pool
    ==========

    Manages a pool of agent instances with load balancing.
    """

    def __init__(self, pool_id: str):
        self.pool_id = pool_id
        self.load_balancer = LoadBalancer()
        self.agents: Dict[str, Dict[str, Any]] = {}

    def add_agent(
        self,
        agent_id: str,
        host: str,
        port: int,
        weight: int = 1
    ):
        """Add agent to pool"""
        self.agents[agent_id] = {
            "agent_id": agent_id,
            "host": host,
            "port": port,
            "weight": weight,
            "status": "active"
        }
        self.load_balancer.add_endpoint(agent_id, host, port, weight)

    def remove_agent(self, agent_id: str):
        """Remove agent from pool"""
        if agent_id in self.agents:
            del self.agents[agent_id]
        self.load_balancer.remove_endpoint(agent_id)

    def get_agent(self, client_id: str = None) -> Optional[Dict[str, Any]]:
        """Get best agent for request"""
        endpoint = self.load_balancer.get_endpoint(client_id)
        if not endpoint:
            return None

        return self.agents.get(endpoint.agent_id)

    def select_agent(self, strategy: LoadBalancingStrategy = None) -> Optional[Dict[str, Any]]:
        """Select agent using specified strategy"""
        if strategy:
            old_strategy = self.load_balancer.strategy
            self.load_balancer.strategy = strategy

            endpoint = self.load_balancer.get_endpoint()
            result = self.agents.get(endpoint.agent_id) if endpoint else None

            self.load_balancer.strategy = old_strategy
            return result

        endpoint = self.load_balancer.get_endpoint()
        return self.agents.get(endpoint.agent_id) if endpoint else None


# Demo
def run_demo():
    print("=" * 70)
    print("Day 76: Load Balancing")
    print("=" * 70)

    # Create agent pool
    pool = AgentPool("primary")

    # Add agents with different weights
    print("\n[1] Adding Agents to Pool")
    print("-" * 40)

    pool.add_agent("agent-1", "192.168.1.10", 8000, weight=3)
    pool.add_agent("agent-2", "192.168.1.11", 8000, weight=2)
    pool.add_agent("agent-3", "192.168.1.12", 8000, weight=1)

    print("  Added agent-1 (weight: 3)")
    print("  Added agent-2 (weight: 2)")
    print("  Added agent-3 (weight: 1)")

    # Test different strategies
    print("\n[2] Round Robin Distribution")
    print("-" * 40)

    pool.load_balancer.strategy = LoadBalancingStrategy.ROUND_ROBIN
    for i in range(5):
        agent = pool.get_agent()
        print(f"  Request {i+1}: {agent['agent_id']}")

    print("\n[3] Weighted Distribution")
    print("-" * 40)

    pool.load_balancer.strategy = LoadBalancingStrategy.WEIGHTED
    distribution = {}
    for _ in range(100):
        agent = pool.get_agent()
        distribution[agent['agent_id']] = distribution.get(agent['agent_id'], 0) + 1

    for agent_id, count in sorted(distribution.items()):
        print(f"  {agent_id}: {count} requests ({count}%)")

    print("\n[4] IP Hash (Consistent)")
    print("-" * 40)

    clients = ["client-a", "client-b", "client-c", "client-d"]
    for client in clients:
        agent = pool.get_agent(client)
        print(f"  {client} -> {agent['agent_id']}")

    # Simulate request tracking
    print("\n[5] Health-Aware Load Balancing")
    print("-" * 40)

    # Record some requests
    for i in range(10):
        endpoint = pool.load_balancer.get_endpoint()
        if endpoint:
            pool.load_balancer.record_request_start(endpoint.agent_id)

            # Simulate response
            response_time = random.uniform(50, 200)
            success = random.random() > 0.1
            pool.load_balancer.record_request_end(
                endpoint.agent_id,
                response_time,
                success
            )

    # Get status
    status = pool.load_balancer.get_status()
    print(f"  Total endpoints: {status['total_endpoints']}")
    print(f"  Healthy endpoints: {status['healthy_endpoints']}")

    for ep in status['endpoints']:
        print(f"  {ep['agent_id']}:")
        print(f"    - Active: {ep['active_connections']}")
        print(f"    - Avg Response: {ep['avg_response_time']:.2f}ms")
        print(f"    - Failure Rate: {ep['failure_rate']*100:.1f}%")

    print("\n[6] Strategy Comparison")
    print("-" * 40)

    strategies = [
        LoadBalancingStrategy.ROUND_ROBIN,
        LoadBalancingStrategy.WEIGHTED,
        LoadBalancingStrategy.LEAST_CONNECTIONS,
        LoadBalancingStrategy.LEAST_RESPONSE_TIME
    ]

    for strategy in strategies:
        result = pool.select_agent(strategy)
        print(f"  {strategy.value}: {result['agent_id'] if result else 'None'}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()