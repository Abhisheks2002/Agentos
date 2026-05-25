"""
Day 32: Hierarchical Multi-Agent Systems
=========================================
Skill: Hierarchical Orchestration
Mini Project: Org Chart

Organizing agents in hierarchies for complex tasks.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class AgentLevel(str, Enum):
    """Levels in hierarchy"""
    EXECUTIVE = "executive"
    MANAGER = "manager"
    WORKER = "worker"
    SPECIALIST = "specialist"


@dataclass
class AgentNode:
    """Node in the hierarchy"""
    id: str = ""
    name: str = ""
    level: AgentLevel = AgentLevel.WORKER
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    task_count: int = 0


class HierarchicalAgentSystem:
    """Agents organized in a hierarchy"""

    def __init__(self, root_id: str):
        self.root_id = root_id
        self.nodes: Dict[str, AgentNode] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()

    def add_node(
        self,
        node_id: str,
        name: str,
        level: AgentLevel,
        parent_id: Optional[str] = None
    ):
        """Add a node to the hierarchy"""
        node = AgentNode(
            id=node_id,
            name=name,
            level=level,
            parent_id=parent_id
        )

        self.nodes[node_id] = node

        # Link to parent
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node_id)

    def get_children(self, node_id: str) -> List[AgentNode]:
        """Get all children of a node"""
        node = self.nodes.get(node_id)
        if not node:
            return []

        children = []
        for child_id in node.children:
            child = self.nodes.get(child_id)
            if child:
                children.append(child)

        return children

    def get_path_to_root(self, node_id: str) -> List[AgentNode]:
        """Get path from node to root"""
        path = []
        current = self.nodes.get(node_id)

        while current:
            path.append(current)
            if current.parent_id:
                current = self.nodes.get(current.parent_id)
            else:
                break

        return path

    async def assign_task(self, task: Dict[str, Any]) -> str:
        """Assign task to appropriate agent"""
        task_id = str(uuid.uuid4())

        # Determine level needed
        complexity = task.get("complexity", "normal")

        if complexity == "high":
            # Executive level
            target_level = AgentLevel.EXECUTIVE
        elif complexity == "medium":
            # Manager level
            target_level = AgentLevel.MANAGER
        else:
            # Worker level
            target_level = AgentLevel.WORKER

        # Find agent at that level
        target = self._find_agent_at_level(target_level)

        if target:
            target.task_count += 1
            return f"Task {task_id[:8]} assigned to {target.name}"

        return "No suitable agent found"

    def _find_agent_at_level(self, level: AgentLevel) -> Optional[AgentNode]:
        """Find an agent at a specific level"""
        for node in self.nodes.values():
            if node.level == level:
                return node
        return None


class ManagerAgent(AgentNode):
    """Agent that manages other agents"""

    def __init__(self, node_id: str, name: str):
        super().__init__(id=node_id, name=name, level=AgentLevel.MANAGER)
        self.delegated_tasks: List[Dict] = []
        self.results: List[Dict] = []

    async def delegate_task(self, task: Dict, workers: List[AgentNode]) -> Dict:
        """Delegate to workers and aggregate results"""
        if not workers:
            return {"error": "No workers available"}

        # Distribute to workers
        results = []
        for worker in workers:
            result = {
                "worker": worker.id,
                "task": task,
                "status": "completed"
            }
            results.append(result)

        # Aggregate
        aggregated = {
            "manager": self.name,
            "delegated": len(workers),
            "results": results
        }

        self.delegated_tasks.append(task)
        self.results.append(aggregated)

        return aggregated


class ExecutiveAgent(AgentNode):
    """Top-level agent that makes decisions"""

    def __init__(self, node_id: str, name: str):
        super().__init__(id=node_id, name=name, level=AgentLevel.EXECUTIVE)
        self.decisions: List[Dict] = []
        self.strategies: List[str] = []

    async def make_decision(self, context: Dict) -> Dict:
        """Make strategic decision"""
        # Analyze context
        complexity = context.get("complexity", 0)
        urgency = context.get("urgency", "normal")

        # Decide approach
        if complexity > 8 and urgency == "high":
            strategy = "full_team_deployment"
        elif complexity > 5:
            strategy = "selective_deployment"
        else:
            strategy = "minimal_deployment"

        decision = {
            "context": context,
            "strategy": strategy,
            "timestamp": datetime.now().isoformat()
        }

        self.decisions.append(decision)
        self.strategies.append(strategy)

        return decision


class SpecialistAgent(AgentNode):
    """Expert agent for specific tasks"""

    def __init__(self, node_id: str, name: str, expertise: str):
        super().__init__(id=node_id, name=name, level=AgentLevel.SPECIALIST)
        self.expertise = expertise
        self.completed_tasks: List[Dict] = []

    async def solve(self, task: Dict) -> Dict:
        """Solve specialized task"""
        result = {
            "task": task,
            "specialist": self.name,
            "expertise": self.expertise,
            "solution": f"Solved using {self.expertise}"
        }

        self.completed_tasks.append(result)
        return result


# Demo
def run_demo():
    print("=" * 70)
    print("Hierarchical Multi-Agent Systems Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create hierarchy
        system = HierarchicalAgentSystem("ceo")

        print("\n[1] Create Hierarchy")
        print("-" * 40)

        # Add nodes
        system.add_node("ceo", "CEO", AgentLevel.EXECUTIVE)
        system.add_node("cto", "CTO", AgentLevel.MANAGER, "ceo")
        system.add_node("cfo", "CFO", AgentLevel.MANAGER, "ceo")
        system.add_node("eng1", "Engineer1", AgentLevel.WORKER, "cto")
        system.add_node("eng2", "Engineer2", AgentLevel.WORKER, "cto")
        system.add_node("acc1", "Accountant1", AgentLevel.WORKER, "cfo")

        print(f"  Root: {system.root_id}")
        print(f"  Total nodes: {len(system.nodes)}")

        # Show structure
        print("\n[2] Hierarchy Structure")
        print("-" * 40)

        cto = system.nodes.get("cto")
        print(f"  CTO children: {[c.id for c in system.get_children('cto')]}")

        path = system.get_path_to_root("eng1")
        print(f"  Path to root: {[n.name for n in path]}")

        # Assign tasks
        print("\n[3] Task Assignment")
        print("-" * 40)

        result = await system.assign_task({
            "task": "Build API",
            "complexity": "high"
        })
        print(f"  {result}")

        result = await system.assign_task({
            "task": "Fix bug",
            "complexity": "low"
        })
        print(f"  {result}")

        # Manager delegation
        print("\n[4] Manager Delegation")
        print("-" * 40)

        manager = ManagerAgent("cto", "CTO")
        workers = [AgentNode(id="w1", name="Worker1", level=AgentLevel.WORKER)]

        result = await manager.delegate_task({"task": "Dev work"}, workers)
        print(f"  Delegated: {result['delegated']} workers")

        # Executive decision
        print("\n[5] Executive Decision")
        print("-" * 40)

        executive = ExecutiveAgent("ceo", "CEO")
        decision = await executive.make_decision({
            "complexity": 9,
            "urgency": "high"
        })
        print(f"  Strategy: {decision['strategy']}")

        # Specialist
        print("\n[6] Specialist Agent")
        print("-" * 40)

        specialist = SpecialistAgent("spec1", "Security Expert", "security")
        result = await specialist.solve({"task": "Security audit"})
        print(f"  Solution: {result['solution']}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()