"""
Day 2: Advanced Python & AsyncIO
==================================
Skill: Asynchronous Programming
Mini Project: Heartbeat Monitor

Simulates checking if 10 agents are "Alive" or "Dead" concurrently.
This is critical for AgentOS - agents wait for LLM responses and we can't
block the OS while waiting.
"""

import asyncio
import random
from typing import List, Dict
from datetime import datetime

async def check_agent_health(agent_id: str) -> Dict[str, any]:
    """Simulate checking if an agent is alive"""
    # Simulate network latency (like calling an LLM)
    await asyncio.sleep(random.uniform(0.1, 0.5))

    # Randomly determine if agent is alive (90% chance)
    is_alive = random.random() > 0.1

    return {
        "agent_id": agent_id,
        "status": "alive" if is_alive else "dead",
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": random.randint(100, 500)
    }

async def heartbeat_monitor(agent_count: int = 10) -> List[Dict]:
    """
    Check health of multiple agents concurrently.
    Uses asyncio.gather to ping all agents simultaneously.
    """
    agent_ids = [f"agent_{i:03d}" for i in range(1, agent_count + 1)]

    # Create tasks for all agents
    tasks = [check_agent_health(agent_id) for agent_id in agent_ids]

    # Run all tasks concurrently - this is the key!
    results = await asyncio.gather(*tasks)

    return results

def analyze_heartbeat_results(results: List[Dict]) -> Dict:
    """Analyze heartbeat results"""
    alive = sum(1 for r in results if r['status'] == 'alive')
    dead = len(results) - alive

    return {
        "total_agents": len(results),
        "alive": alive,
        "dead": dead,
        "health_percentage": (alive / len(results)) * 100 if results else 0,
        "avg_response_time": sum(r['response_time_ms'] for r in results) / len(results) if results else 0
    }

async def main():
    """Run the heartbeat monitor"""
    print("Starting Heartbeat Monitor for 10 agents...")
    print("-" * 50)

    results = await heartbeat_monitor(10)

    print("Results:")
    for result in results:
        status_icon = "✓" if result['status'] == 'alive' else "✗"
        print(f"  {status_icon} {result['agent_id']}: {result['status']} ({result['response_time_ms']}ms)")

    analysis = analyze_heartbeat_results(results)
    print("-" * 50)
    print(f"Summary: {analysis['alive']}/{analysis['total_agents']} agents alive")
    print(f"Health: {analysis['health_percentage']:.1f}%")
    print(f"Avg Response Time: {analysis['avg_response_time']:.1f}ms")

if __name__ == "__main__":
    asyncio.run(main())