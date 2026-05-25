"""
Day 96: Self-Modifying Agent Code
==================================

Implementing agents that can modify their own code and behavior at runtime
for continuous improvement and adaptation.

Key Concepts:
- Runtime Code Generation
- Genetic Programming
- Self-Improvement Loops
- Adaptive Behavior
- Meta-Learning
"""

from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import random
import hashlib
import inspect
import re


class ModificationType(Enum):
    """Types of code modification"""
    PARAMETER_TUNING = "parameter_tuning"
    STRATEGY_SWITCH = "strategy_switch"
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_CHANGE = "architecture_change"
    LEARNING_RATE = "learning_rate"


class CodeComponent(Enum):
    """Code components that can be modified"""
    BEHAVIOR = "behavior"
    DECISION_LOGIC = "decision_logic"
    MEMORY_MANAGEMENT = "memory_management"
    COMMUNICATION = "communication"
    RESOURCE_ALLOCATION = "resource_allocation"


@dataclass
class Modification:
    """Code Modification"""
    modification_id: str
    component: CodeComponent
    modification_type: ModificationType
    old_code: str
    new_code: str
    timestamp: datetime
    success: bool
    performance_delta: float = 0.0


@dataclass
class AgentGene:
    """Genetic representation of agent behavior"""
    gene_id: str
    component: CodeComponent
    value: Any
    fitness_score: float = 0.0
    mutation_rate: float = 0.1


@dataclass
class SelfModificationPlan:
    """Plan for self-modification"""
    plan_id: str
    target_component: CodeComponent
    objective: str
    modifications: List[Modification]
    estimated_improvement: float
    risk_level: str


class CodeTemplate:
    """Template for code generation"""

    BEHAVIOR_TEMPLATES = {
        "reactive": """
    def execute_{component}(self, context):
        # Reactive behavior
        if {condition}:
            return {action}
        return None
""",
        "deliberative": """
    def execute_{component}(self, context):
        # Deliberative behavior
        plan = self.plan({goal})
        return self.execute_plan(plan)
""",
        "hybrid": """
    def execute_{component}(self, context):
        # Hybrid behavior
        if self.should_react({situation}):
            return self.react({stimulus})
        return self.deliberate({goal})
"""
    }

    DECISION_TEMPLATES = {
        "decision_tree": """
    def decide_{component}(self, state):
        if state.{condition1}:
            return {action1}
        elif state.{condition2}:
            return {action2}
        return {default_action}
""",
        "utility_based": """
    def decide_{component}(self, state):
        options = self.get_options()
        utilities = {{opt: self.utility(opt, state) for opt in options}}
        return max(utilities, key=utilities.get)
""",
        "rule_based": """
    def decide_{component}(self, state):
        for rule in self.rules:
            if rule.matches(state):
                return rule.action
        return self.default_action
"""
    }


class GeneticCodeModifier:
    """
    Genetic Code Modifier
    =====================

    Uses genetic programming to modify agent code.
    """

    def __init__(self):
        self.genes: Dict[str, AgentGene] = {}
        self.population: List[List[AgentGene]] = []
        self.generation = 0

    def create_gene(
        self,
        component: CodeComponent,
        initial_value: Any
    ) -> AgentGene:
        """Create new gene"""
        gene = AgentGene(
            gene_id=str(uuid.uuid4()),
            component=component,
            value=initial_value
        )
        self.genes[gene.gene_id] = gene
        return gene

    def initialize_population(self, population_size: int = 50):
        """Initialize gene population"""
        self.population = []
        for i in range(population_size):
            individual = []

            for component in CodeComponent:
                gene = self.create_gene(component, random.random())
                individual.append(gene)

            self.population.append(individual)

    def crossover(self, parent1: List[AgentGene], parent2: List[AgentGene]) -> List[AgentGene]:
        """Crossover two individuals"""
        child = []
        crossover_point = random.randint(1, len(parent1) - 1)

        for i in range(len(parent1)):
            if i < crossover_point:
                child.append(parent1[i])
            else:
                child.append(parent2[i])

        return child

    def mutate(self, gene: AgentGene) -> AgentGene:
        """Mutate a gene"""
        if random.random() < gene.mutation_rate:
            # Apply mutation based on type
            if isinstance(gene.value, float):
                gene.value = max(0, min(1, gene.value + random.uniform(-0.1, 0.1)))
            elif isinstance(gene.value, int):
                gene.value = max(0, gene.value + random.randint(-1, 1))
            elif isinstance(gene.value, str):
                # String mutation
                chars = list(gene.value)
                if chars:
                    idx = random.randint(0, len(chars) - 1)
                    chars[idx] = chr(ord(chars[idx]) + random.randint(-1, 1))
                gene.value = ''.join(chars)

        return gene

    def evaluate_population(self, fitness_function: Callable) -> float:
        """Evaluate population fitness"""
        total_fitness = 0

        for individual in self.population:
            fitness = fitness_function([g.value for g in individual])
            for gene in individual:
                gene.fitness_score = fitness
            total_fitness += fitness

        return total_fitness / len(self.population) if self.population else 0

    def evolve_generation(self, fitness_function: Callable, elite_size: int = 5):
        """Evolve one generation"""
        # Evaluate
        self.evaluate_population(fitness_function)

        # Sort by fitness
        sorted_pop = sorted(
            self.population,
            key=lambda ind: sum(g.fitness_score for g in ind),
            reverse=True
        )

        # Create new population
        new_population = sorted_pop[:elite_size]

        while len(new_population) < len(self.population):
            # Tournament selection
            parent1 = random.choice(sorted_pop[:len(sorted_pop)//2])
            parent2 = random.choice(sorted_pop[:len(sorted_pop)//2])

            # Crossover
            child = self.crossover(parent1, parent2)

            # Mutation
            child = [self.mutate(g) for g in child]

            new_population.append(child)

        self.population = new_population
        self.generation += 1


class RuntimeCodeGenerator:
    """
    Runtime Code Generator
    ======================

    Generates code at runtime.
    """

    def __init__(self):
        self.generated_code: Dict[str, str] = {}

    def generate_behavior(
        self,
        component: str,
        strategy: str = "reactive"
    ) -> str:
        """Generate behavior code"""
        template = CodeTemplate.BEHHAVIOR_TEMPLATES.get(strategy, CodeTemplate.BEHHAVIOR_TEMPLATES["reactive"])

        code = template.format(
            component=component,
            condition="context.get('trigger', False)",
            action="self.perform_action(context)",
            goal="context.get('goal')",
            situation="context.get('situation')",
            goal="context.get('goal')",
            stimulus="context.get('stimulus')"
        )

        code_id = str(uuid.uuid4())
        self.generated_code[code_id] = code

        return code

    def generate_decision_logic(
        self,
        component: str,
        logic_type: str = "decision_tree"
    ) -> str:
        """Generate decision logic code"""
        template = CodeTemplate.DECISION_TEMPLATES.get(logic_type, CodeTemplate.DECISION_TEMPLATES["decision_tree"])

        code = template.format(
            component=component,
            condition1="triggered > 0.5",
            action1="Action.PRIMARY",
            condition2="priority > 0.8",
            action2="Action.SECONDARY",
            default_action="Action.DEFAULT"
        )

        code_id = str(uuid.uuid4())
        self.generated_code[code_id] = code

        return code

    def generate_parameter_tuning(
        self,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate parameter tuning code"""
        code_lines = ["# Auto-generated parameter tuning", ""]

        for name, value in parameters.items():
            code_lines.append(f"self.{name} = {value}")

        code = "\n".join(code_lines)
        code_id = str(uuid.uuid4())
        self.generated_code[code_id] = code

        return code


class SelfModifyingAgent:
    """
    Self-Modifying Agent
    =====================

    Agent capable of modifying its own code at runtime.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.genetic_modifier = GeneticCodeModifier()
        self.code_generator = RuntimeCodeGenerator()
        self.modifications: List[Modification] = []
        self.performance_history: List[float] = []
        self.current_strategy = "reactive"

        # Initialize genes with default values
        for component in CodeComponent:
            self.genetic_modifier.create_gene(component, random.random())

        # Agent parameters
        self.parameters = {
            "learning_rate": 0.01,
            "exploration_rate": 0.1,
            "memory_size": 1000,
            "decision_threshold": 0.5,
            "response_timeout": 5.0
        }

    async def analyze_performance(self) -> Dict[str, float]:
        """Analyze current performance"""
        current = self.performance_history[-1] if self.performance_history else 0.5

        # Simulate performance metrics
        metrics = {
            "efficiency": current + random.uniform(-0.1, 0.1),
            "accuracy": current + random.uniform(-0.05, 0.15),
            "speed": current + random.uniform(-0.1, 0.1),
            "resource_usage": 1.0 - current + random.uniform(-0.1, 0.1)
        }

        return metrics

    async def create_modification_plan(
        self,
        objective: str
    ) -> SelfModificationPlan:
        """Create plan for self-modification"""
        plan_id = str(uuid.uuid4())

        # Analyze current state
        metrics = await self.analyze_performance()

        # Determine target component
        worst_metric = min(metrics.items(), key=lambda x: x[1])
        component_map = {
            "efficiency": CodeComponent.RESOURCE_ALLOCATION,
            "accuracy": CodeComponent.DECISION_LOGIC,
            "speed": CodeComponent.BEHAVIOR,
            "resource_usage": CodeComponent.MEMORY_MANAGEMENT
        }

        target_component = component_map.get(worst_metric[0], CodeComponent.BEHAVIOR)

        # Generate modifications
        modifications = []

        if target_component == CodeComponent.BEHHAVIOR:
            new_strategy = random.choice(["reactive", "deliberative", "hybrid"])
            old_code = f"def execute_behavior(self): return self.{self.current_strategy}_execute()"
            new_code = self.code_generator.generate_behavior("main", new_strategy)

            mod = Modification(
                modification_id=str(uuid.uuid4()),
                component=target_component,
                modification_type=ModificationType.STRATEGY_SWITCH,
                old_code=old_code,
                new_code=new_code,
                timestamp=datetime.now(),
                success=False
            )
            modifications.append(mod)

        elif target_component == CodeComponent.DECISION_LOGIC:
            new_logic = random.choice(["decision_tree", "utility_based", "rule_based"])
            old_code = "# Old decision logic"
            new_code = self.code_generator.generate_decision_logic("action", new_logic)

            mod = Modification(
                modification_id=str(uuid.uuid4()),
                component=target_component,
                modification_type=ModificationType.CODE_GENERATION,
                old_code=old_code,
                new_code=new_code,
                timestamp=datetime.now(),
                success=False
            )
            modifications.append(mod)

        elif target_component in [CodeComponent.MEMORY_MANAGEMENT, CodeComponent.RESOURCE_ALLOCATION]:
            # Parameter tuning
            old_params = self.parameters.copy()
            if target_component == CodeComponent.MEMORY_MANAGEMENT:
                self.parameters["memory_size"] = int(self.parameters["memory_size"] * random.uniform(0.8, 1.2))
            else:
                self.parameters["learning_rate"] = self.parameters["learning_rate"] * random.uniform(0.9, 1.1)

            old_code = f"# Old params: {old_params}"
            new_code = self.code_generator.generate_parameter_tuning(self.parameters)

            mod = Modification(
                modification_id=str(uuid.uuid4()),
                component=target_component,
                modification_type=ModificationType.PARAMETER_TUNING,
                old_code=old_code,
                new_code=new_code,
                timestamp=datetime.now(),
                success=False
            )
            modifications.append(mod)

        plan = SelfModificationPlan(
            plan_id=plan_id,
            target_component=target_component,
            objective=objective,
            modifications=modifications,
            estimated_improvement=abs(worst_metric[1] - 0.8),
            risk_level="medium"
        )

        return plan

    async def apply_modification(self, plan: SelfModificationPlan) -> bool:
        """Apply self-modification plan"""
        print(f"[SelfModifyingAgent] Applying modification plan {plan.plan_id[:8]}...")

        # Simulate testing modification
        old_performance = self.performance_history[-1] if self.performance_history else 0.5
        test_performance = old_performance + plan.estimated_improvement * random.uniform(0.5, 1.5)

        # Apply modifications
        for mod in plan.modifications:
            mod.success = True
            mod.performance_delta = test_performance - old_performance
            self.modifications.append(mod)

        self.performance_history.append(test_performance)
        self.current_strategy = "deliberative" if random.random() > 0.5 else self.current_strategy

        print(f"[SelfModifyingAgent] Modification applied")
        print(f"  Component: {plan.target_component.value}")
        print(f"  Performance delta: {plan.modifications[0].performance_delta:.4f}")

        return True

    async def continuous_improvement(self, iterations: int = 5):
        """Continuous self-improvement loop"""
        print(f"[SelfModifyingAgent] Starting continuous improvement for {iterations} iterations...")

        for i in range(iterations):
            # Analyze performance
            metrics = await self.analyze_performance()
            avg_performance = sum(metrics.values()) / len(metrics)
            self.performance_history.append(avg_performance)

            # Create and apply modification plan
            objective = f"improve_metrics"
            plan = await self.create_modification_plan(objective)

            success = await self.apply_modification(plan)

            if success:
                print(f"[Iteration {i+1}] Performance: {avg_performance:.4f}")
            else:
                print(f"[Iteration {i+1}] Modification failed, reverting")

        print(f"[SelfModifyingAgent] Improvement complete")

    def get_modification_history(self) -> Dict[str, Any]:
        """Get modification history"""
        return {
            "total_modifications": len(self.modifications),
            "successful": sum(1 for m in self.modifications if m.success),
            "failed": sum(1 for m in self.modifications if not m.success),
            "by_component": {
                comp.value: sum(1 for m in self.modifications if m.component == comp)
                for comp in CodeComponent
            },
            "performance_trend": self.performance_history[-5:] if len(self.performance_history) > 5 else self.performance_history
        }


class MetaLearningAgent:
    """
    Meta-Learning Agent
    ====================

    Agent that learns how to learn.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.strategies: Dict[str, Callable] = {}
        self.current_strategy = "default"
        self.strategy_performance: Dict[str, List[float]] = {}
        self.meta_parameters = {
            "learning_rate_schedule": "exponential",
            "adaptation_steps": 10,
            "freeze_layers": 0
        }

    def register_strategy(self, name: str, strategy: Callable):
        """Register learning strategy"""
        self.strategies[name] = strategy
        self.strategy_performance[name] = []

    async def select_strategy(self, task_complexity: float) -> str:
        """Select best strategy based on task"""
        # Meta-learning: choose strategy based on task characteristics
        if task_complexity < 0.3:
            strategy = "fast_adapt"
        elif task_complexity < 0.7:
            strategy = "balanced"
        else:
            strategy = "thorough"

        self.current_strategy = strategy
        return strategy

    async def meta_learn(self, tasks: List[Dict[str, Any]]):
        """Meta-learn across tasks"""
        print(f"[MetaLearning] Meta-learning across {len(tasks)} tasks...")

        for i, task in enumerate(tasks):
            # Get task characteristics
            complexity = task.get("complexity", 0.5)
            size = task.get("size", 100)

            # Select and apply strategy
            strategy = await self.select_strategy(complexity)

            # Simulate learning
            performance = complexity * random.uniform(0.7, 1.0)
            self.strategy_performance[strategy].append(performance)

            print(f"[Task {i+1}] Strategy: {strategy}, Performance: {performance:.4f}")

        # Analyze strategy performance
        best_strategy = max(
            self.strategy_performance.items(),
            key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
        )

        print(f"[MetaLearning] Best strategy: {best_strategy[0]}")


async def main():
    """Demonstrate Self-Modifying Agent Code"""
    print("=" * 60)
    print("Self-Modifying Agent Code - Day 96")
    print("=" * 60)

    # Create self-modifying agent
    agent = SelfModifyingAgent("self-mod-001")

    # Initial performance
    print("\n[1] Initial State")
    print("-" * 40)
    print(f"  Agent ID: {agent.agent_id}")
    print(f"  Parameters: {agent.parameters}")

    # Performance analysis
    print("\n[2] Performance Analysis")
    print("-" * 40)

    metrics = await agent.analyze_performance()
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

    # Create modification plan
    print("\n[3] Modification Planning")
    print("-" * 40)

    plan = await agent.create_modification_plan("improve_accuracy")
    print(f"  Plan ID: {plan.plan_id[:8]}...")
    print(f"  Target: {plan.target_component.value}")
    print(f"  Estimated improvement: {plan.estimated_improvement:.4f}")
    print(f"  Risk: {plan.risk_level}")

    # Apply modifications
    print("\n[4] Applying Modifications")
    print("-" * 40)

    success = await agent.apply_modification(plan)
    print(f"  Success: {success}")

    # Continuous improvement
    print("\n[5] Continuous Improvement")
    print("-" * 40)

    await agent.continuous_improvement(iterations=5)

    # Modification history
    print("\n[6] Modification History")
    print("-" * 40)

    history = agent.get_modification_history()
    print(f"  Total modifications: {history['total_modifications']}")
    print(f"  Successful: {history['successful']}")
    print(f"  Performance trend: {history['performance_trend']}")

    # Genetic modifier
    print("\n[7] Genetic Programming")
    print("-" * 40)

    gmodifier = GeneticCodeModifier()
    gmodifier.initialize_population(20)

    def fitness_function(genes):
        return sum(genes) / len(genes)

    print(f"  Initial population: {len(gmodifier.population)}")

    for _ in range(5):
        avg_fitness = gmodifier.evaluate_population(fitness_function)
        gmodifier.evolve_generation(fitness_function)
        print(f"  Generation {gmodifier.generation}: Avg fitness = {avg_fitness:.4f}")

    # Code generation
    print("\n[8] Runtime Code Generation")
    print("-" * 40)

    generator = RuntimeCodeGenerator()

    behavior_code = generator.generate_behavior("navigation", "deliberative")
    print(f"  Generated behavior code ({len(behavior_code)} chars)")

    decision_code = generator.generate_decision_logic("priority", "utility_based")
    print(f"  Generated decision code ({len(decision_code)} chars)")

    param_code = generator.generate_parameter_tuning({"lr": 0.01, "batch": 32})
    print(f"  Generated param code ({len(param_code)} chars)")

    # Meta-learning
    print("\n[9] Meta-Learning")
    print("-" * 40)

    meta_agent = MetaLearningAgent("meta-001")

    tasks = [
        {"complexity": 0.2, "size": 50},
        {"complexity": 0.5, "size": 100},
        {"complexity": 0.8, "size": 200},
    ]

    await meta_agent.meta_learn(tasks)

    print("\n" + "=" * 60)
    print("Self-Modifying Agent Code complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())