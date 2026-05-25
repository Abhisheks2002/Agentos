"""
Day 60: Iterative Refinement
=============================
Iterative refinement of solutions through multiple passes.

Key Concepts:
- Progressive improvement
- Quality thresholds
- Solution space exploration
- Convergence detection
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import math


class RefinementStrategy(Enum):
    """Strategies for iterative refinement"""
    GRADUAL = "gradual"  # Small incremental changes
    RADICAL = "radical"  # Large changes to explore new areas
    HYBRID = "hybrid"    # Mix of gradual and radical
    FOCUSED = "focused"  # Focus on specific weak points


@dataclass
class Solution:
    """A candidate solution"""
    id: str
    content: Any
    score: float = 0.0
    generation: int = 0
    parent_id: Optional[str] = None
    mutations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementResult:
    """Result of iterative refinement"""
    best_solution: Solution
    all_solutions: List[Solution]
    generations: int
    converged: bool
    total_evaluations: int


class IterativeRefiner:
    """
    Iterative Refiner
    =================

    Refines solutions through multiple iterations with
    various refinement strategies.
    """

    def __init__(
        self,
        evaluate_fn: Callable[[Any], float] = None,
        mutate_fn: Callable[[Any, str], Any] = None,
        max_generations: int = 100,
        population_size: int = 10
    ):
        self.evaluate_fn = evaluate_fn or self._default_evaluate
        self.mutate_fn = mutate_fn or self._default_mutate
        self.max_generations = max_generations
        self.population_size = population_size
        self.solutions: List[Solution] = []
        self.best_history: List[float] = []

    async def refine(
        self,
        initial_solution: Any,
        strategy: RefinementStrategy = RefinementStrategy.HYBRID,
        convergence_threshold: float = 0.01,
        max_no_improvement: int = 10
    ) -> RefinementResult:
        """
        Iteratively refine a solution.

        Args:
            initial_solution: Starting solution
            strategy: Refinement strategy to use
            convergence_threshold: Stop when improvement is below this
            max_no_improvement: Stop after this many generations without improvement

        Returns:
            Best solution found and refinement details
        """
        # Initialize population
        self.solutions = []
        self.best_history = []

        # Add initial solution
        initial = Solution(
            id="gen0_0",
            content=initial_solution,
            score=self.evaluate_fn(initial_solution),
            generation=0
        )
        self.solutions.append(initial)

        best_solution = initial
        no_improvement_count = 0
        total_evaluations = 1

        for generation in range(1, self.max_generations + 1):
            # Generate new candidates
            new_solutions = await self._generate_candidates(
                best_solution,
                generation,
                strategy
            )

            # Evaluate new solutions
            for sol in new_solutions:
                sol.score = self.evaluate_fn(sol.content)
                total_evaluations += 1

            # Add to population
            self.solutions.extend(new_solutions)

            # Keep best solutions
            self.solutions = sorted(
                self.solutions,
                key=lambda s: s.score,
                reverse=True
            )[:self.population_size]

            # Track best
            current_best = self.solutions[0]
            self.best_history.append(current_best.score)

            # Check for improvement
            if current_best.score > best_solution.score + convergence_threshold:
                best_solution = current_best
                no_improvement_count = 0
            else:
                no_improvement_count += 1

            # Check convergence
            if no_improvement_count >= max_no_improvement:
                print(f"Converged after {generation} generations")
                break

            # Log progress
            if generation % 10 == 0:
                print(f"Generation {generation}: Best score = {best_solution.score:.4f}")

        converged = len(self.best_history) > 10 and (
            abs(self.best_history[-1] - self.best_history[-10]) < convergence_threshold
        )

        return RefinementResult(
            best_solution=best_solution,
            all_solutions=self.solutions,
            generations=generation,
            converged=converged,
            total_evaluations=total_evaluations
        )

    async def _generate_candidates(
        self,
        parent: Solution,
        generation: int,
        strategy: RefinementStrategy
    ) -> List[Solution]:
        """Generate new candidate solutions"""
        candidates = []

        num_candidates = max(1, self.population_size // 3)

        for i in range(num_candidates):
            mutation_type = self._select_mutation_type(strategy)

            if strategy == RefinementStrategy.RADICAL:
                # Generate from scratch occasionally
                mutated_content = self.mutate_fn(parent.content, "random")
                mutation_desc = "random"
            else:
                # Mutate from parent
                mutated_content = self.mutate_fn(parent.content, mutation_type)
                mutation_desc = mutation_type

            candidate = Solution(
                id=f"gen{generation}_{i}",
                content=mutated_content,
                generation=generation,
                parent_id=parent.id,
                mutations=[mutation_desc]
            )
            candidates.append(candidate)

        return candidates

    def _select_mutation_type(self, strategy: RefinementStrategy) -> str:
        """Select mutation type based on strategy"""
        mutations = {
            RefinementStrategy.GRADUAL: ["small_change", "perturb", "smooth"],
            RefinementStrategy.RADICAL: ["major_change", "rebuild", "transform"],
            RefinementStrategy.HYBRID: ["small_change", "perturb", "major_change"],
            RefinementStrategy.FOCUSED: ["refine", "detail", "improve"]
        }
        return random.choice(mutations[strategy])

    def _default_evaluate(self, solution: Any) -> float:
        """Default evaluation function"""
        if isinstance(solution, (int, float)):
            return float(solution)
        elif isinstance(solution, str):
            return len(solution) / 100.0
        elif isinstance(solution, list):
            return sum(solution) / len(solution) if solution else 0
        return 0.5

    def _default_mutate(self, solution: Any, mutation: str) -> Any:
        """Default mutation function"""
        if isinstance(solution, (int, float)):
            if mutation == "random":
                return solution + random.uniform(-50, 50)
            elif mutation == "small_change":
                return solution + random.uniform(-5, 5)
            elif mutation == "perturb":
                return solution * random.uniform(0.9, 1.1)
            return solution + random.uniform(-10, 10)

        elif isinstance(solution, str):
            if mutation == "random":
                return "".join(random.choices("abcdefghijklmnopqrstuvwxyz ", k=len(solution)))
            elif mutation == "small_change":
                chars = list(solution)
                if chars:
                    idx = random.randint(0, len(chars) - 1)
                    chars[idx] = random.choice("abcdefghijklmnopqrstuvwxyz ")
                return "".join(chars)
            return solution

        elif isinstance(solution, list):
            if mutation == "random":
                return [random.random() * 100 for _ in range(len(solution))]
            elif mutation == "small_change":
                return [x + random.uniform(-5, 5) for x in solution]
            return solution

        return solution


class SimulatedAnnealingRefiner(IterativeRefiner):
    """
    Simulated Annealing Refiner
    ===========================

    Uses simulated annealing for refinement.
    """

    def __init__(self, *args, initial_temp: float = 100.0, cooling_rate: float = 0.95, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.current_temp = initial_temp

    async def refine(self, initial_solution: Any, **kwargs) -> RefinementResult:
        """Refine using simulated annealing"""
        self.current_temp = self.initial_temp

        current = Solution(
            id="start",
            content=initial_solution,
            score=self.evaluate_fn(initial_solution)
        )

        best = current
        total_evaluations = 1

        for generation in range(1, self.max_generations + 1):
            # Generate neighbor
            neighbor_content = self.mutate_fn(current.content, "small_change")
            neighbor = Solution(
                id=f"gen{generation}",
                content=neighbor_content,
                score=self.evaluate_fn(neighbor_content),
                generation=generation
            )
            total_evaluations += 1

            # Calculate acceptance probability
            delta = neighbor.score - current.score

            if delta > 0 or random.random() < math.exp(delta / self.current_temp):
                current = neighbor

                if current.score > best.score:
                    best = current

            # Cool down
            self.current_temp *= self.cooling_rate

            if generation % 10 == 0:
                print(f"Generation {generation}: Temp = {self.current_temp:.2f}, Best = {best.score:.4f}")

        return RefinementResult(
            best_solution=best,
            all_solutions=[current, best],
            generations=generation,
            converged=self.current_temp < 0.1,
            total_evaluations=total_evaluations
        )


# Demo
async def main():
    print("=" * 60)
    print("Day 60: Iterative Refinement")
    print("=" * 60)

    # Test 1: Basic iterative refinement
    print("\n--- Test 1: Basic Iterative Refinement ---")

    initial = 25.0  # Starting value, target is to maximize

    # Custom evaluation: maximize value (find 100)
    def custom_eval(x):
        # Closer to 100 is better, with a peak at 100
        return max(0, 100 - abs(x - 100))

    refiner = IterativeRefiner(
        evaluate_fn=custom_eval,
        max_generations=50,
        population_size=5
    )

    result = await refiner.refine(initial, strategy=RefinementStrategy.HYBRID)

    print(f"Initial value: {initial}")
    print(f"Best solution: {result.best_solution.content:.4f}")
    print(f"Best score: {result.best_solution.score:.4f}")
    print(f"Generations: {result.generations}")
    print(f"Converged: {result.converged}")

    # Test 2: Simulated annealing
    print("\n--- Test 2: Simulated Annealing ---")

    sa_refiner = SimulatedAnnealingRefiner(
        evaluate_fn=custom_eval,
        initial_temp=100.0,
        cooling_rate=0.95,
        max_generations=50
    )

    sa_result = await sa_refiner.refine(initial)

    print(f"Initial value: {initial}")
    print(f"Best solution: {sa_result.best_solution.content:.4f}")
    print(f"Best score: {sa_result.best_solution.score:.4f}")
    print(f"Final temperature: {sa_refiner.current_temp:.4f}")

    # Test 3: String optimization
    print("\n--- Test 3: String Optimization ---")

    target = "hello world"
    initial_str = "xxxx xxxxxx"

    def string_eval(s):
        # Count matching characters at correct positions
        matches = sum(1 for a, b in zip(s, target) if a == b)
        return matches / len(target)

    def string_mutate(s, mutation):
        chars = list(s)
        for i in range(len(chars)):
            if random.random() < 0.3:
                chars[i] = random.choice("abcdefghijklmnopqrstuvwxyz ")
        return "".join(chars)

    str_refiner = IterativeRefiner(
        evaluate_fn=string_eval,
        mutate_fn=string_mutate,
        max_generations=100,
        population_size=10
    )

    str_result = await str_refiner.refine(initial_str, strategy=RefinementStrategy.HYBRID)

    print(f"Target: '{target}'")
    print(f"Initial: '{initial_str}'")
    print(f"Best: '{str_result.best_solution.content}'")
    print(f"Score: {str_result.best_solution.score:.2%}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())