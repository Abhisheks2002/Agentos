"""
Day 60: Recursive Problem Decomposition
========================================
Breaking down complex problems into smaller, manageable sub-problems.

Key Concepts:
- Problem decomposition
- Recursive solving
- Sub-problem coordination
- Solution synthesis
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class ProblemComplexity(Enum):
    """Complexity levels for problems"""
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    VERY_COMPLEX = 5


@dataclass
class SubProblem:
    """A sub-problem derived from decomposition"""
    id: str
    description: str
    complexity: ProblemComplexity
    solution: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    dependencies: List[str] = field(default_factory=list)
    children: List['SubProblem'] = field(default_factory=list)
    result: Optional[Dict] = None


@dataclass
class DecompositionResult:
    """Result of problem decomposition"""
    original_problem: str
    sub_problems: List[SubProblem]
    solution: Optional[str] = None
    execution_order: List[str] = field(default_factory=list)
    depth: int = 0


class RecursiveDecomposer:
    """
    Recursive Problem Decomposer
    ============================

    Breaks down complex problems into smaller sub-problems
    and solves them recursively.
    """

    def __init__(self, solver=None, max_depth: int = 5):
        self.solver = solver
        self.max_depth = max_depth
        self.problem_cache: Dict[str, DecompositionResult] = {}

    async def decompose_and_solve(
        self,
        problem: str,
        depth: int = 0
    ) -> DecompositionResult:
        """
        Decompose and solve a problem recursively.

        Args:
            problem: The problem to solve
            depth: Current recursion depth

        Returns:
            Solution with decomposition tree
        """
        # Check cache
        if problem in self.problem_cache:
            return self.problem_cache[problem]

        # Base case: problem is simple enough
        complexity = self._assess_complexity(problem)
        if complexity <= ProblemComplexity.MODERATE or depth >= self.max_depth:
            solution = await self._solve_direct(problem)
            result = DecompositionResult(
                original_problem=problem,
                sub_problems=[],
                solution=solution,
                depth=depth
            )
            self.problem_cache[problem] = result
            return result

        # Decompose into sub-problems
        sub_problems = await self._decompose(problem)

        # Solve sub-problems recursively
        execution_order = self._topological_sort(sub_problems)

        for sub_id in execution_order:
            sub = next(p for p in sub_problems if p.id == sub_id)

            # Check dependencies
            deps_solved = all(
                next((p for p in sub_problems if p.id == d), None)?.status == "completed"
                for d in sub.dependencies
            )

            if not deps_solved:
                sub.status = "failed"
                continue

            sub.status = "in_progress"

            # Recursively solve
            if sub.complexity > ProblemComplexity.SIMPLE:
                sub_result = await self.decompose_and_solve(sub.description, depth + 1)
                sub.result = sub_result.solution
                sub.solution = sub_result.solution
            else:
                sub.solution = await self._solve_direct(sub.description)

            sub.status = "completed"

        # Synthesize solution
        solution = await self._synthesize(problem, sub_problems)

        result = DecompositionResult(
            original_problem=problem,
            sub_problems=sub_problems,
            solution=solution,
            execution_order=execution_order,
            depth=depth
        )

        self.problem_cache[problem] = result
        return result

    def _assess_complexity(self, problem: str) -> ProblemComplexity:
        """Assess the complexity of a problem"""
        # Simple heuristics
        word_count = len(problem.split())

        if word_count < 5:
            return ProblemComplexity.TRIVIAL
        elif word_count < 15:
            return ProblemComplexity.SIMPLE
        elif word_count < 30:
            return ProblemComplexity.MODERATE
        elif word_count < 50:
            return ProblemComplexity.COMPLEX
        else:
            return ProblemComplexity.VERY_COMPLEX

    async def _decompose(self, problem: str) -> List[SubProblem]:
        """Decompose problem into sub-problems"""
        # In real implementation, this would use LLM
        sub_problems = []

        # Simple decomposition strategy
        keywords = ["and", "then", "also", "plus", "with"]

        parts = [problem]
        for keyword in keywords:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(f" {keyword} "))
            parts = new_parts

        for i, part in enumerate(parts):
            part = part.strip()
            if part and len(part) > 3:
                sub = SubProblem(
                    id=f"sub_{i}_{uuid.uuid4().hex[:6]}",
                    description=part,
                    complexity=self._assess_complexity(part)
                )
                sub_problems.append(sub)

        # If no decomposition happened, create a single sub-problem
        if not sub_problems:
            sub_problems.append(SubProblem(
                id=f"sub_0_{uuid.uuid4().hex[:6]}",
                description=problem,
                complexity=self._assess_complexity(problem)
            ))

        return sub_problems

    async def _solve_direct(self, problem: str) -> str:
        """Solve a problem directly (leaf node)"""
        # In real implementation, this would call the LLM
        return f"Solution for: {problem[:50]}..."

    def _topological_sort(self, sub_problems: List[SubProblem]) -> List[str]:
        """Sort sub-problems by dependencies"""
        # Build dependency graph
        in_degree = {sp.id: len(sp.dependencies) for sp in sub_problems}
        queue = [sp.id for sp in sub_problems if in_degree[sp.id] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Update dependent nodes
            for sp in sub_problems:
                if current in sp.dependencies:
                    in_degree[sp.id] -= 1
                    if in_degree[sp.id] == 0:
                        queue.append(sp.id)

        return result

    async def _synthesize(
        self,
        original: str,
        sub_problems: List[SubProblem]
    ) -> str:
        """Synthesize solutions from sub-problems"""
        solutions = [sp.solution for sp in sub_problems if sp.solution]

        if not solutions:
            return "No solution found"

        # Simple synthesis
        synthesis = " && ".join([s[:30] for s in solutions[:3]])
        if len(solutions) > 3:
            synthesis += f" ... ({len(solutions)} parts)"

        return synthesis

    def get_decomposition_tree(
        self,
        result: DecompositionResult,
        indent: int = 0
    ) -> str:
        """Get a visual representation of the decomposition tree"""
        prefix = "  " * indent

        if not result.sub_problems:
            return f"{prefix}└─ {result.original_problem[:40]} -> {result.solution[:30]}"

        lines = [f"{prefix}┌─ {result.original_problem[:40]}"]

        for sub in result.sub_problems:
            status_icon = {
                "pending": "○",
                "in_progress": "◐",
                "completed": "●",
                "failed": "✗"
            }.get(sub.status, "?")

            lines.append(f"{prefix}├─ {status_icon} {sub.description[:35]}")

            if sub.children:
                for child in sub.children:
                    lines.append(self.get_decomposition_tree(
                        DecompositionResult(
                            original_problem=child.description,
                            sub_problems=[child]
                        ),
                        indent + 2
                    ))

        return "\n".join(lines)


# Demo
async def main():
    print("=" * 60)
    print("Day 60: Recursive Problem Decomposition")
    print("=" * 60)

    decomposer = RecursiveDecomposer(max_depth=4)

    # Test with a complex problem
    problem = "Calculate the average of all prime numbers between 1 and 1000, then find all factors of that average"

    print(f"\nProblem: {problem}\n")

    result = await decomposer.decompose_and_solve(problem)

    print("Decomposition Tree:")
    print("-" * 40)
    print(decomposer.get_decomposition_tree(result))

    print(f"\nFinal Solution: {result.solution}")
    print(f"Depth: {result.depth}")
    print(f"Sub-problems: {len(result.sub_problems)}")
    print(f"Execution order: {result.execution_order}")

    # Test with simpler problem
    print("\n" + "=" * 60)
    print("Test 2: Simpler Problem")
    print("=" * 60)

    simple_problem = "Add 5 and 10"
    simple_result = await decomposer.decompose_and_solve(simple_problem)
    print(f"\nProblem: {simple_problem}")
    print(f"Solution: {simple_result.solution}")
    print(f"Sub-problems: {len(simple_result.sub_problems)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())