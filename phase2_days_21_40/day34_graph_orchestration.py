"""
Day 34: Graph-Based Multi-Agent Orchestration
==============================================
Skill: Graph Orchestration
Mini Project: Agent Graph Builder

Using graph structures to orchestrate agent workflows.
"""

from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import deque


class NodeType(str, Enum):
    """Types of nodes in the graph"""
    AGENT = "agent"
    TASK = "task"
    CONDITION = "condition"
    MERGE = "merge"
    SPLIT = "split"
    OUTPUT = "output"


@dataclass
class GraphNode:
    """Node in the orchestration graph"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    node_type: NodeType = NodeType.AGENT
    config: Dict[str, Any] = field(default_factory=dict)
    in_edges: List[str] = field(default_factory=list)
    out_edges: List[str] = field(default_factory=list)


class AgentGraph:
    """Graph-based agent orchestration"""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.execution_order: List[str] = []

    def add_node(
        self,
        name: str,
        node_type: NodeType,
        config: Dict = None
    ) -> GraphNode:
        """Add a node to the graph"""
        node = GraphNode(
            name=name,
            node_type=node_type,
            config=config or {}
        )
        self.nodes[node.id] = node
        return node

    def add_edge(self, from_id: str, to_id: str):
        """Add an edge between nodes"""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].out_edges.append(to_id)
            self.nodes[to_id].in_edges.append(from_id)

    def remove_edge(self, from_id: str, to_id: str):
        """Remove an edge"""
        if from_id in self.nodes and to_id in self.nodes:
            if to_id in self.nodes[from_id].out_edges:
                self.nodes[from_id].out_edges.remove(to_id)
            if from_id in self.nodes[to_id].in_edges:
                self.nodes[to_id].in_edges.remove(from_id)

    def topological_sort(self) -> List[str]:
        """Get execution order using topological sort"""
        in_degree = {node_id: len(node.in_edges) for node_id, node in self.nodes.items()}
        queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for neighbor in self.nodes[node_id].out_edges:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Graph has cycles!")

        self.execution_order = result
        return result

    def get_executable_nodes(self, completed: Set[str]) -> List[GraphNode]:
        """Get nodes that can be executed"""
        executable = []

        for node_id, node in self.nodes.items():
            if node_id in completed:
                continue

            # Check if all inputs are satisfied
            if all(in_id in completed for in_id in node.in_edges):
                executable.append(node)

        return executable

    def visualize(self) -> Dict[str, Any]:
        """Get graph visualization data"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.value,
                    "config": n.config
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {"from": from_id, "to": to_id}
                for node in self.nodes.values()
                for to_id in node.out_edges
            ]
        }


class GraphExecutor:
    """Executes agent graphs"""

    def __init__(self, graph: AgentGraph):
        self.graph = graph
        self.results: Dict[str, Any] = {}
        self.agent_handlers: Dict[str, Callable] = {}

    def register_agent(self, name: str, handler: Callable):
        """Register an agent handler"""
        self.agent_handlers[name] = handler

    async def execute(
        self,
        start_nodes: List[str] = None,
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        """Execute the graph"""
        # Get execution order
        try:
            order = self.graph.topological_sort()
        except ValueError as e:
            return {"error": str(e)}

        completed: Set[str] = set()
        failed: Set[str] = set()

        iteration = 0
        while iteration < max_iterations:
            # Get executable nodes
            executable = self.graph.get_executable_nodes(completed)

            if not executable:
                break

            # Execute each executable node
            for node in executable:
                if node.node_type == NodeType.AGENT:
                    result = await self._execute_agent(node)
                elif node.node_type == NodeType.TASK:
                    result = await self._execute_task(node)
                elif node.node_type == NodeType.CONDITION:
                    result = await self._evaluate_condition(node)
                elif node.node_type == NodeType.MERGE:
                    result = await self._merge_results(node)
                else:
                    result = {"status": "skipped"}

                self.results[node.id] = result

                if result.get("status") == "failed":
                    failed.add(node.id)
                else:
                    completed.add(node.id)

            iteration += 1

        return {
            "completed": list(completed),
            "failed": list(failed),
            "results": self.results
        }

    async def _execute_agent(self, node: GraphNode) -> Dict[str, Any]:
        """Execute an agent node"""
        agent_name = node.config.get("agent", node.name)

        if agent_name in self.agent_handlers:
            handler = self.agent_handlers[agent_name]
            input_data = self._collect_inputs(node)
            result = await handler(input_data)
            return {"status": "success", "result": result}

        return {"status": "success", "result": f"Simulated: {node.name}"}

    async def _execute_task(self, node: GraphNode) -> Dict[str, Any]:
        """Execute a task node"""
        await asyncio.sleep(0.01)
        return {"status": "success", "output": f"Task: {node.name}"}

    async def _evaluate_condition(self, node: GraphNode) -> Dict[str, Any]:
        """Evaluate a condition node"""
        condition = node.config.get("condition", "true")
        return {
            "status": "success",
            "condition_met": condition == "true"
        }

    async def _merge_results(self, node: GraphNode) -> Dict[str, Any]:
        """Merge results from multiple inputs"""
        inputs = self._collect_inputs(node)
        return {"status": "success", "merged": inputs}

    def _collect_inputs(self, node: GraphNode) -> Dict[str, Any]:
        """Collect inputs from connected nodes"""
        inputs = {}
        for in_id in node.in_edges:
            if in_id in self.results:
                inputs[in_id] = self.results[in_id]
        return inputs


class ConditionalGraph(AgentGraph):
    """Graph with conditional branching"""

    def add_conditional_edge(
        self,
        from_id: str,
        to_id: str,
        condition: str
    ):
        """Add edge with condition"""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].out_edges.append(to_id)
            self.nodes[to_id].in_edges.append(from_id)
            # Store condition in config
            self.nodes[from_id].config[f"condition_{to_id}"] = condition


class ParallelGraph(AgentGraph):
    """Graph with parallel execution"""

    async def execute_parallel(
        self,
        node_ids: List[str],
        handlers: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """Execute nodes in parallel"""
        tasks = []

        for node_id in node_ids:
            node = self.nodes.get(node_id)
            if node and node.name in handlers:
                tasks.append(handlers[node.name]())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "results": dict(zip(node_ids, results))
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Graph-Based Multi-Agent Orchestration Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create graph
        graph = AgentGraph()

        # Add nodes
        print("\n[1] Build Graph")
        print("-" * 40)

        start = graph.add_node("Start", NodeType.TASK)
        research = graph.add_node("Research", NodeType.AGENT, {"agent": "researcher"})
        analyze = graph.add_node("Analyze", NodeType.AGENT, {"agent": "analyzer"})
        write = graph.add_node("Write", NodeType.AGENT, {"agent": "writer"})
        review = graph.add_node("Review", NodeType.AGENT, {"agent": "reviewer"})
        end = graph.add_node("End", NodeType.OUTPUT)

        # Add edges
        graph.add_edge(start.id, research.id)
        graph.add_edge(research.id, analyze.id)
        graph.add_edge(analyze.id, write.id)
        graph.add_edge(write.id, review.id)
        graph.add_edge(review.id, end.id)

        print(f"  Nodes: {len(graph.nodes)}")
        print(f"  Edges: {sum(len(n.out_edges) for n in graph.nodes.values())}")

        # Topological sort
        print("\n[2] Execution Order")
        print("-" * 40)

        order = graph.topological_sort()
        for node_id in order:
            node = graph.nodes[node_id]
            print(f"  {node.name} ({node.node_type.value})")

        # Execute graph
        print("\n[3] Execute Graph")
        print("-" * 40)

        executor = GraphExecutor(graph)

        # Register handlers
        async def research_handler(inputs):
            await asyncio.sleep(0.01)
            return {"data": "research results"}

        async def analyze_handler(inputs):
            await asyncio.sleep(0.01)
            return {"analysis": "analyzed"}

        async def write_handler(inputs):
            await asyncio.sleep(0.01)
            return {"document": "written"}

        async def review_handler(inputs):
            await asyncio.sleep(0.01)
            return {"approved": True}

        executor.register_agent("Research", research_handler)
        executor.register_agent("Analyze", analyze_handler)
        executor.register_agent("Write", write_handler)
        executor.register_agent("Review", review_handler)

        result = await executor.execute()
        print(f"  Completed: {len(result['completed'])} nodes")
        print(f"  Failed: {len(result['failed'])} nodes")

        # Visualize
        print("\n[4] Graph Visualization")
        print("-" * 40)

        viz = graph.visualize()
        print(f"  Nodes: {len(viz['nodes'])}")
        print(f"  Edges: {len(viz['edges'])}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()