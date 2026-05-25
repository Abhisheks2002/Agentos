"""
Day 53: Tree of Thought
=======================
Exploring multiple reasoning paths in parallel.

Key Concepts:
- Parallel thought exploration
- Breadth-first search
- Depth-first exploration
- Path evaluation and pruning
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import heapq


class ExplorationStrategy(Enum):
    """How to explore the thought tree"""
    BFS = "breadth_first"
    DFS = "depth_first"
    BEST_FIRST = "best_first"
    ASTAR = "a_star"


@dataclass
class ThoughtNode:
    """A node in the thought tree"""
    id: str
    content: str
    depth: int
    score: float = 0.0
    parent: Optional[str] = None  # Parent node ID
    children: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    is_leaf: bool = False
    is_final: bool = False


@dataclass
class ThoughtTree:
    """A tree of thoughts"""
    id: str
    root_content: str
    nodes: Dict[str, ThoughtNode] = field(default_factory=dict)
    strategy: ExplorationStrategy = ExplorationStrategy.BFS

    def add_node(
        self,
        content: str,
        parent_id: str = None,
        depth: int = 0,
        score: float = 0.0
    ) -> ThoughtNode:
        """Add a node to the tree"""
        node = ThoughtNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            content=content,
            depth=depth,
            score=score,
            parent=parent_id
        )
        self.nodes[node.id] = node

        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node.id)

        return node

    def get_path(self, node_id: str) -> List[ThoughtNode]:
        """Get the path from root to a node"""
        path = []
        current = self.nodes.get(node_id)

        while current:
            path.insert(0, current)
            current = self.nodes.get(current.parent) if current.parent else None

        return path

    def get_best_leaf(self) -> ThoughtNode:
        """Get the leaf with highest score"""
        leaves = [n for n in self.nodes.values() if n.is_leaf or not n.children]
        if not leaves:
            return None
        return max(leaves, key=lambda n: n.score)

    def get_all_leaves(self) -> List[ThoughtNode]:
        """Get all leaf nodes"""
        return [n for n in self.nodes.values() if n.is_leaf or not n.children]


class TreeOfThought:
    """
    Tree of Thought Reasoner
    ========================

    Explores multiple reasoning paths using tree search.
    """

    def __init__(
        self,
        generate_fn: Callable[[str, int], List[str]] = None,
        evaluate_fn: Callable[[str], float] = None,
        max_branches: int = 3,
        max_depth: int = 4,
        strategy: ExplorationStrategy = ExplorationStrategy.BEST_FIRST
    ):
        self.generate_fn = generate_fn or self._default_generate
        self.evaluate_fn = evaluate_fn or (lambda x: 1.0)
        self.max_branches = max_branches
        self.max_depth = max_depth
        self.strategy = strategy

    def _default_generate(self, state: str, num: int) -> List[str]:
        """Default thought generation"""
        return [f"Option {i+1} for: {state[:30]}..." for i in range(num)]

    def solve(
        self,
        problem: str,
        early_stopping_fn: Callable[[str], bool] = None
    ) -> Tuple[ThoughtTree, ThoughtNode]:
        """Solve problem using tree of thought"""
        # Initialize tree
        tree = ThoughtTree(
            id=f"tree_{uuid.uuid4().hex[:8]}",
            root_content=problem,
            strategy=self.strategy
        )

        # Add root
        root_score = self.evaluate_fn(problem)
        root = tree.add_node(problem, depth=0, score=root_score)

        # Explore based on strategy
        if self.strategy == ExplorationStrategy.BFS:
            return self._bfs_search(tree, root, early_stopping_fn)
        elif self.strategy == ExplorationStrategy.DFS:
            return self._dfs_search(tree, root, early_stopping_fn)
        elif self.strategy == ExplorationStrategy.BEST_FIRST:
            return self._best_first_search(tree, root, early_stopping_fn)
        else:
            return self._bfs_search(tree, root, early_stopping_fn)

    def _bfs_search(
        self,
        tree: ThoughtTree,
        root: ThoughtNode,
        early_stopping_fn
    ) -> Tuple[ThoughtTree, ThoughtNode]:
        """Breadth-first search"""
        queue = [(root.score, root.id)]

        while queue:
            _, current_id = heapq.heappop(queue)
            current = tree.nodes[current_id]

            # Check stopping condition
            if early_stopping_fn and early_stopping_fn(current.content):
                current.is_final = True
                return tree, current

            # Stop if max depth reached
            if current.depth >= self.max_depth:
                current.is_leaf = True
                continue

            # Generate branches
            branches = self.generate_fn(current.content, self.max_branches)

            for branch_content in branches:
                score = self.evaluate_fn(branch_content)
                child = tree.add_node(
                    content=branch_content,
                    parent_id=current.id,
                    depth=current.depth + 1,
                    score=score
                )
                heapq.heappush(queue, (-score, child.id))

        # Return best leaf
        best_leaf = tree.get_best_leaf()
        best_leaf.is_final = True
        return tree, best_leaf

    def _dfs_search(
        self,
        tree: ThoughtTree,
        root: ThoughtNode,
        early_stopping_fn
    ) -> Tuple[ThoughtTree, ThoughtNode]:
        """Depth-first search"""
        best_result = None
        best_score = root.score

        def dfs(node: ThoughtNode):
            nonlocal best_result, best_score

            # Check stopping
            if early_stopping_fn and early_stopping_fn(node.content):
                node.is_final = True
                if node.score > best_score:
                    best_score = node.score
                    best_result = node
                return

            # Stop at max depth
            if node.depth >= self.max_depth:
                node.is_leaf = True
                if node.score > best_score:
                    best_score = node.score
                    best_result = node
                return

            # Generate and explore branches
            branches = self.generate_fn(node.content, self.max_branches)

            for branch_content in branches:
                score = self.evaluate_fn(branch_content)
                child = tree.add_node(
                    content=branch_content,
                    parent_id=node.id,
                    depth=node.depth + 1,
                    score=score
                )
                dfs(child)

        dfs(root)

        if not best_result:
            best_result = tree.get_best_leaf()
            if best_result:
                best_result.is_final = True

        return tree, best_result

    def _best_first_search(
        self,
        tree: ThoughtTree,
        root: ThoughtNode,
        early_stopping_fn
    ) -> Tuple[ThoughtTree, ThoughtNode]:
        """Best-first search - always explore highest scoring node"""
        # Priority queue: (-score, node_id)
        pq = [(-root.score, root.id)]
        visited = set()

        while pq:
            neg_score, current_id = heapq.heappop(pq)

            if current_id in visited:
                continue
            visited.add(current_id)

            current = tree.nodes[current_id]

            # Check stopping
            if early_stopping_fn and early_stopping_fn(current.content):
                current.is_final = True
                return tree, current

            # Stop at max depth
            if current.depth >= self.max_depth:
                current.is_leaf = True
                continue

            # Generate branches
            branches = self.generate_fn(current.content, self.max_branches)

            for branch_content in branches:
                score = self.evaluate_fn(branch_content)
                child = tree.add_node(
                    content=branch_content,
                    parent_id=current.id,
                    depth=current.depth + 1,
                    score=score
                )
                heapq.heappush(pq, (-score, child.id))

        best_leaf = tree.get_best_leaf()
        best_leaf.is_final = True
        return tree, best_leaf

    def get_solution_path(self, tree: ThoughtTree, leaf: ThoughtNode) -> str:
        """Get the full solution path"""
        path = tree.get_path(leaf.id)
        return "\n".join(f"Step {i+1}: {node.content[:50]}..."
                        for i, node in enumerate(path))


class DiverseThoughtExplorer:
    """
    Diverse Thought Explorer
    ========================

    Ensures thought diversity to avoid local minima.
    """

    def __init__(self, thought_generator, diversity_fn: Callable = None):
        self.thought_generator = thought_generator
        self.diversity_fn = diversity_fn or self._default_diversity

    def _default_diversity(self, thoughts: List[str]) -> float:
        """Calculate diversity score"""
        if len(thoughts) < 2:
            return 0.0

        # Simple diversity: average pairwise difference
        total = 0
        count = 0
        for i in range(len(thoughts)):
            for j in range(i + 1, len(thoughts)):
                # Jaccard similarity of words
                words_i = set(thoughts[i].lower().split())
                words_j = set(thoughts[j].lower().split())
                if words_i or words_j:
                    jaccard = 1 - len(words_i & words_j) / len(words_i | words_j)
                    total += jaccard
                    count += 1

        return total / count if count > 0 else 0.0

    def generate_diverse_thoughts(
        self,
        state: str,
        num_thoughts: int = 3,
        min_diversity: float = 0.3
    ) -> List[str]:
        """Generate diverse thoughts"""
        all_thoughts = []
        attempts = 0
        max_attempts = 10

        while len(all_thoughts) < num_thoughts and attempts < max_attempts:
            # Generate batch
            new_thoughts = self.thought_generator(state, num_thoughts)

            for thought in new_thoughts:
                if thought not in all_thoughts:
                    # Check diversity with existing thoughts
                    test_thoughts = all_thoughts + [thought]
                    diversity = self.diversity_fn(test_thoughts)

                    if diversity >= min_diversity or len(all_thoughts) < 2:
                        all_thoughts.append(thought)

            attempts += 1

        return all_thoughts[:num_thoughts]


# Demo function
def demo():
    """Demonstrate Tree of Thought"""
    print("=" * 60)
    print("  Tree of Thought Demo")
    print("=" * 60)

    # Sample thought generator
    def generate_thoughts(state: str, num: int) -> List[str]:
        options = [
            "Consider the mathematical approach using algebra",
            "Try a graphical interpretation of the problem",
            "Break it down into smaller sub-problems",
            "Look for patterns in the given information",
            "Consider edge cases and special scenarios",
            "Use logical deduction to narrow possibilities"
        ]
        import random
        return random.sample(options, min(num, len(options)))

    # Sample evaluator
    def evaluate_thought(thought: str) -> float:
        score = 0.5  # Base score
        if "mathematical" in thought.lower():
            score += 0.3
        if "pattern" in thought.lower():
            score += 0.2
        return min(score, 1.0)

    # Test different strategies
    problem = "How to solve a complex mathematical proof?"

    print(f"\nProblem: {problem}")

    for strategy in [ExplorationStrategy.BFS, ExplorationStrategy.BEST_FIRST]:
        print(f"\n{'-' * 50}")
        print(f"Strategy: {strategy.value}")

        tot = TreeOfThought(
            generate_fn=generate_thoughts,
            evaluate_fn=evaluate_thought,
            max_branches=3,
            max_depth=3,
            strategy=strategy
        )

        tree, best = tot.solve(problem)

        print(f"Total nodes: {len(tree.nodes)}")
        print(f"Best leaf score: {best.score:.2f}")
        print(f"Best path: {tot.get_solution_path(tree, best)[:100]}...")

    # Diverse thoughts
    print(f"\n{'-' * 50}")
    print("Diverse Thought Exploration:")

    explorer = DiverseThoughtExplorer(generate_thoughts)
    diverse = explorer.generate_diverse_thoughts(problem, num_thoughts=3)

    for i, thought in enumerate(diverse, 1):
        print(f"  {i}. {thought}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()