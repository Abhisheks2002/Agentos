"""
Day 32: Hierarchical Multi-Agent Systems
=========================================
Skill: Hierarchical Orchestration
Mini Project: Org Chart Manager

Organizing agents in hierarchical structures.
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
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    level: AgentLevel = AgentLevel.WORKER
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    tasks_completed: int = 0


class HierarchicalSystem:
    """Hierarchical multi-agent system"""

    def __init__(self):
        self.nodes: Dict[str, AgentNode] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.root_id: Optional[str] = None

    def add_node(
        self,
        name: str,
        level: AgentLevel,
        parent_id: str = None,
        capabilities: List[str] = None
    ) -> AgentNode:
        """Add a node to the hierarchy"""
        node = AgentNode(
            name=name,
            level=level,
            parent_id=parent_id,
            capabilities=capabilities or []
        )

        self.nodes[node.id] = node

        # Update parent
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children_ids.append(node.id)

        # Set root if no parent
        if not parent_id:
            self.root_id = node.id

        return node

    def get_children(self, node_id: str) -> List[AgentNode]:
        """Get direct children of a node"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[cid] for cid in node.children_ids if cid in self.nodes]

    def get_ancestors(self, node_id: str) -> List[AgentNode]:
        """Get all ancestors of a node"""
        ancestors = []
        node = self.nodes.get(node_id)

        while node and node.parent_id:
            parent = self.nodes.get(node.parent_id)
            if parent:
                ancestors.append(parent)
                node = parent
            else:
                break

        return ancestors

    def get_descendants(self, node_id: str) -> List[AgentNode]:
        """Get all descendants of a node"""
        descendants = []
        to_visit = [node_id]

        while to_visit:
            current_id = to_visit.pop()
            node = self.nodes.get(current_id)

            if node:
                for child_id in node.children_ids:
                    child = self.nodes.get(child_id)
                    if child:
                        descendants.append(child)
                        to_visit.append(child_id)

        return descendants

    def find_node_by_capability(self, capability: str) -> List[AgentNode]:
        """Find nodes with a capability"""
        return [
            node for node in self.nodes.values()
            if capability in node.capabilities
        ]

    def visualize_hierarchy(self) -> Dict[str, Any]:
        """Visualize the hierarchy"""
        if not self.root_id:
            return {}

        root = self.nodes[self.root_id]
        return self._build_tree(root)

    def _build_tree(self, node: AgentNode) -> Dict[str, Any]:
        """Build tree structure"""
        children = [self._build_tree(self.nodes[cid]) for cid in node.children_ids if cid in self.nodes]

        return {
            "name": node.name,
            "level": node.level.value,
            "capabilities": node.capabilities,
            "children": children
        }


class ExecutiveAgent(HierarchicalSystem):
    """Executive-level agent that delegates"""

    def __init__(self):
        super().__init__()
        self.strategy: str = ""

    def set_strategy(self, strategy: str):
        """Set organizational strategy"""
        self.strategy = strategy

    async def delegate_work(self, work_description: str) -> List[str]:
        """Delegate work down the hierarchy"""
        # Find appropriate workers
        workers = [
            node.id for node in self.nodes.values()
            if node.level == AgentLevel.WORKER
        ]

        return workers[:3]  # Limit delegation

    async def collect_reports(self) -> Dict[str, Any]:
        """Collect reports from all levels"""
        report = {
            "executive": self.strategy,
            "managers": [],
            "workers": []
        }

        for node in self.nodes.values():
            if node.level == AgentLevel.MANAGER:
                report["managers"].append({
                    "name": node.name,
                    "tasks": node.tasks_completed
                })
            elif node.level == AgentLevel.WORKER:
                report["workers"].append({
                    "name": node.name,
                    "tasks": node.tasks_completed
                })

        return report


class ManagerAgent:
    """Manager-level agent"""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.pending_tasks: List[Dict] = []
        self.completed_tasks: List[Dict] = []

    async def assign_task(self, task: Dict, worker_id: str) -> bool:
        """Assign task to worker"""
        self.pending_tasks.append({
            **task,
            "worker_id": worker_id,
            "status": "assigned"
        })
        return True

    async def review_work(self, worker_id: str) -> Dict[str, Any]:
        """Review work from a worker"""
        worker_tasks = [
            t for t in self.completed_tasks
            if t.get("worker_id") == worker_id
        ]

        return {
            "worker_id": worker_id,
            "tasks_reviewed": len(worker_tasks),
            "approved": len(worker_tasks)
        }


class WorkerAgent:
    """Worker-level agent"""

    def __init__(self, node_id: str, capabilities: List[str]):
        self.node_id = node_id
        self.capabilities = capabilities
        self.current_task: Optional[Dict] = None

    async def execute_task(self, task: Dict) -> Dict[str, Any]:
        """Execute assigned task"""
        self.current_task = task

        # Simulate work
        await asyncio.sleep(0.1)

        result = {
            "task_id": task.get("id"),
            "status": "completed",
            "output": f"Task completed by worker"
        }

        self.current_task = None
        return result


# Demo
def run_demo():
    print("=" * 70)
    print("Hierarchical Multi-Agent Systems Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create hierarchical system
        system = ExecutiveAgent()

        # Add nodes
        print("\n[1] Build Hierarchy")
        print("-" * 40)

        ceo = system.add_node("CEO", AgentLevel.EXECUTIVE, capabilities=["strategy"])
        cto = system.add_node("CTO", AgentLevel.MANAGER, ceo.id, ["tech_strategy"])
        cfo = system.add_node("CFO", AgentLevel.MANAGER, ceo.id, ["finance_strategy"])

        dev1 = system.add_node("Dev1", AgentLevel.WORKER, cto.id, ["coding", "testing"])
        dev2 = system.add_node("Dev2", AgentLevel.WORKER, cto.id, ["coding", "review"])
        dev3 = system.add_node("Dev3", AgentLevel.WORKER, cto.id, ["devops"])

        acc1 = system.add_node("Acc1", AgentLevel.WORKER, cfo.id, ["accounting"])
        acc2 = system.add_node("Acc2", AgentLevel.WORKER, cfo.id, ["reporting"])

        print(f"  Total nodes: {len(system.nodes)}")
        print(f"  Root: {system.nodes[system.root_id].name}")

        # Explore hierarchy
        print("\n[2] Hierarchy Navigation")
        print("-" * 40)

        children = system.get_children(cto.id)
        print(f"  CTO's children: {[c.name for c in children]}")

        ancestors = system.get_ancestors(dev1.id)
        print(f"  Dev1's ancestors: {[a.name for a in ancestors]}")

        descendants = system.get_descendants(ceo.id)
        print(f"  CEO's descendants: {len(descendants)} nodes")

        # Find by capability
        print("\n[3] Find by Capability")
        print("-" * 40)

        coders = system.find_node_by_capability("coding")
        print(f"  Coders: {[n.name for n in coders]}")

        # Delegate work
        print("\n[4] Work Delegation")
        print("-" * 40)

        system.set_strategy("Q4 Goals")
        workers = await system.delegate_work("Implement feature X")
        print(f"  Delegated to: {len(workers)} workers")

        # Collect reports
        print("\n[5] Reports")
        print("-" * 40)

        report = await system.collect_reports()
        print(f"  Strategy: {report['executive']}")
        print(f"  Managers: {len(report['managers'])}")
        print(f"  Workers: {len(report['workers'])}")

        # Visualize
        print("\n[6] Hierarchy Tree")
        print("-" * 40)

        tree = system.visualize_hierarchy()
        print(f"  Root: {tree['name']} ({tree['level']})")
        print(f"  Children: {len(tree['children'])}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()