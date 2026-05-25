"""
Day 83: Chaos Engineering for Agent OS
=====================================

Implementing chaos engineering principles to test and improve
system resilience through controlled fault injection.

Key Concepts:
- Fault injection
- Chaos experiments
- Failure testing
- Resilience validation
- Game days
- Blast radius control
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import random
import time
import json


class ChaosAction(Enum):
    """Types of chaos actions"""
    KILL_AGENT = "kill_agent"
    DELAY_MESSAGE = "delay_message"
    DROP_MESSAGE = "drop_message"
    CORRUPT_MESSAGE = "corrupt_message"
    EXHAUST_MEMORY = "exhaust_memory"
    THROTTLE_CPU = "throttle_cpu"
    NETWORK_PARTITION = "network_partition"
    DATABASE_FAILURE = "database_failure"
    API_FAILURE = "api_failure"
    TIMEOUT = "timeout"


class ExperimentStatus(Enum):
    """Chaos experiment status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    STOPPED = "stopped"


class BlastRadius(Enum):
    """Blast radius levels"""
    CONTAINER = "container"
    POD = "pod"
    NODE = "node"
    CLUSTER = "cluster"


@dataclass
class ChaosExperiment:
    """Defines a chaos experiment"""
    experiment_id: str
    name: str
    description: str
    action: ChaosAction
    target: str  # agent_id, component, or pattern
    duration_seconds: int
    blast_radius: BlastRadius
    injection_rate: float = 1.0  # 0.0 to 1.0
    rollback_on_failure: bool = True
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Results from a chaos experiment"""
    experiment_id: str
    status: ExperimentStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    iterations: int = 0
    failures_injected: int = 0
    system_failures: int = 0
    recovered: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class FaultInjector(ABC):
    """Abstract base for fault injectors"""

    @abstractmethod
    def inject(self, target: Any, params: Dict[str, Any]) -> Any:
        """Inject fault"""
        pass

    @abstractmethod
    def recover(self, target: Any) -> None:
        """Recover from fault"""
        pass


class DelayInjector(FaultInjector):
    """Injects network delays"""

    def __init__(self, min_delay: float = 0.1, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay

    def inject(self, target: Any, params: Dict[str, Any]) -> Any:
        delay = params.get("delay", random.uniform(self.min_delay, self.max_delay))
        print(f"  [DelayInjector] Injecting {delay}s delay to {target}")
        time.sleep(delay)
        return delay

    def recover(self, target: Any) -> None:
        print(f"  [DelayInjector] Removing delay from {target}")


class FailureInjector(FaultInjector):
    """Injects random failures"""

    def __init__(self, failure_rate: float = 0.3):
        self.failure_rate = failure_rate

    def inject(self, target: Any, params: Dict[str, Any]) -> Any:
        if random.random() < self.failure_rate:
            error_type = params.get("error_type", "simulated_error")
            print(f"  [FailureInjector] Injecting {error_type} to {target}")
            raise Exception(f"Injected failure: {error_type}")
        return None

    def recover(self, target: Any) -> None:
        print(f"  [FailureInjector] Recovered {target}")


class CorruptionInjector(FaultInjector):
    """Injects data corruption"""

    def inject(self, target: Any, params: Dict[str, Any]) -> Any:
        corruption_type = params.get("type", "random")
        print(f"  [CorruptionInjector] Corrupting {target} with {corruption_type}")
        if corruption_type == "random":
            return str(target) + "_CORRUPTED"
        elif corruption_type == "truncate":
            return str(target)[:len(target)//2]
        elif corruption_type == "null":
            return None
        return target

    def recover(self, target: Any) -> None:
        print(f"  [CorruptionInjector] Restored {target}")


class ResourceExhaustionInjector(FaultInjector):
    """Injects resource exhaustion"""

    def __init__(self):
        self.consumed = {}

    def inject(self, target: Any, params: Dict[str, Any]) -> Any:
        resource = params.get("resource", "memory")
        amount = params.get("amount", 100)  # MB
        print(f"  [ResourceInjector] Consuming {amount}MB of {resource} for {target}")
        self.consumed[target] = amount
        return amount

    def recover(self, target: Any) -> None:
        print(f"  [ResourceInjector] Released resources for {target}")
        if target in self.consumed:
            del self.consumed[target]


class ChaosEngine:
    """
    Chaos Engine
    =============

    Manages chaos experiments and fault injection.
    """

    def __init__(self):
        self.experiments: Dict[str, ChaosExperiment] = {}
        self.results: Dict[str, ExperimentResult] = {}
        self.injectors: Dict[ChaosAction, FaultInjector] = {
            ChaosAction.DELAY_MESSAGE: DelayInjector(),
            ChaosAction.DROP_MESSAGE: FailureInjector(1.0),
            ChaosAction.CORRUPT_MESSAGE: CorruptionInjector(),
            ChaosAction.EXHAUST_MEMORY: ResourceExhaustionInjector(),
            ChaosAction.TIMEOUT: FailureInjector(0.5),
        }
        self.active_experiments: List[str] = []

    def register_experiment(self, experiment: ChaosExperiment) -> str:
        """Register a new chaos experiment"""
        self.experiments[experiment.experiment_id] = experiment
        return experiment.experiment_id

    def create_experiment(
        self,
        name: str,
        action: ChaosAction,
        target: str,
        duration_seconds: int,
        blast_radius: BlastRadius = BlastRadius.CONTAINER,
        injection_rate: float = 1.0,
        description: str = "",
        rollback_on_failure: bool = True
    ) -> str:
        """Create and register a new experiment"""
        experiment = ChaosExperiment(
            experiment_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            action=action,
            target=target,
            duration_seconds=duration_seconds,
            blast_radius=blast_radius,
            injection_rate=injection_rate,
            rollback_on_failure=rollback_on_failure
        )
        return self.register_experiment(experiment)

    def run_experiment(
        self,
        experiment_id: str,
        agent_system: Any = None,
        before_hook: Optional[Callable] = None,
        after_hook: Optional[Callable] = None
    ) -> ExperimentResult:
        """Run a chaos experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment = self.experiments[experiment_id]

        if not experiment.enabled:
            raise ValueError(f"Experiment {experiment_id} is disabled")

        # Create result tracker
        result = ExperimentResult(
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
            started_at=datetime.now()
        )
        self.results[experiment_id] = result

        self.active_experiments.append(experiment_id)
        print(f"\n{'='*60}")
        print(f"Starting Chaos Experiment: {experiment.name}")
        print(f"  Action: {experiment.action.value}")
        print(f"  Target: {experiment.target}")
        print(f"  Duration: {experiment.duration_seconds}s")
        print(f"  Blast Radius: {experiment.blast_radius.value}")
        print(f"{'='*60}\n")

        # Run before hook
        if before_hook:
            before_hook(experiment)

        injector = self.injectors.get(experiment.action)

        if not injector:
            result.errors.append(f"No injector for action {experiment.action}")
            result.status = ExperimentStatus.FAILED
            return result

        start_time = time.time()
        iteration = 0

        try:
            while time.time() - start_time < experiment.duration_seconds:
                iteration += 1
                result.iterations = iteration

                # Apply injection rate
                if random.random() < experiment.injection_rate:
                    try:
                        params = experiment.metadata.copy()
                        params["delay"] = params.get("delay", 2.0)
                        params["error_type"] = params.get("error_type", "timeout")

                        injector.inject(experiment.target, params)
                        result.failures_injected += 1

                        # Simulate system response
                        if agent_system:
                            # Attempt recovery
                            recovered = agent_system.recover_from_failure(
                                experiment.target,
                                experiment.action
                            )
                            result.recovered += 1
                        else:
                            # Simulate recovery
                            time.sleep(0.1)
                            result.recovered += 1

                    except Exception as e:
                        result.system_failures += 1
                        result.errors.append(str(e))
                        print(f"  [!] System failure: {e}")

                # Record metrics
                result.metrics["duration"] = time.time() - start_time
                result.metrics["injection_rate"] = (
                    result.failures_injected / max(1, iteration)
                )

                time.sleep(1)  # Check every second

        except KeyboardInterrupt:
            result.status = ExperimentStatus.STOPPED
        finally:
            result.ended_at = datetime.now()

            # Run after hook
            if after_hook:
                after_hook(experiment, result)

            # Cleanup injector state
            injector.recover(experiment.target)

            if experiment_id in self.active_experiments:
                self.active_experiments.remove(experiment_id)

        # Determine final status
        if result.system_failures > result.recovered:
            result.status = ExperimentStatus.FAILED
        else:
            result.status = ExperimentStatus.PASSED

        self.results[experiment_id] = result
        return result

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment"""
        if experiment_id in self.active_experiments:
            experiment = self.experiments[experiment_id]
            injector = self.injectors.get(experiment.action)
            if injector:
                injector.recover(experiment.target)
            self.active_experiments.remove(experiment_id)

            if experiment_id in self.results:
                self.results[experiment_id].status = ExperimentStatus.STOPPED
                self.results[experiment_id].ended_at = datetime.now()
            return True
        return False

    def get_experiment_status(self, experiment_id: str) -> Optional[Dict]:
        """Get experiment status"""
        if experiment_id not in self.results:
            return None

        result = self.results[experiment_id]
        return {
            "experiment_id": experiment_id,
            "status": result.status.value,
            "iterations": result.iterations,
            "failures_injected": result.failures_injected,
            "system_failures": result.system_failures,
            "recovered": result.recovered,
            "metrics": result.metrics
        }

    def get_resilience_score(self) -> float:
        """Calculate overall resilience score"""
        if not self.results:
            return 0.0

        total = 0
        weighted_score = 0

        for result in self.results.values():
            if result.status in [ExperimentStatus.PASSED, ExperimentStatus.FAILED]:
                total += 1

                # Calculate score for this experiment
                if result.iterations > 0:
                    recovery_rate = result.recovered / result.iterations
                    failure_tolerance = 1.0 - (result.system_failures / max(1, result.failures_injected))
                    score = (recovery_rate * 0.6 + max(0, failure_tolerance) * 0.4)
                    weighted_score += score

        if total == 0:
            return 0.0

        return weighted_score / total


class GameDayScheduler:
    """
    Game Day Scheduler
    ==================

    Schedules and coordinates game days (planned chaos experiments).
    """

    def __init__(self, chaos_engine: ChaosEngine):
        self.chaos_engine = chaos_engine
        self.scheduled_experiments: List[Dict] = []
        self.game_days: List[Dict] = []

    def schedule_game_day(
        self,
        name: str,
        date: datetime,
        experiments: List[str],
        participants: List[str],
        description: str = ""
    ) -> str:
        """Schedule a game day"""
        game_day_id = str(uuid.uuid4())[:8]
        game_day = {
            "game_day_id": game_day_id,
            "name": name,
            "date": date,
            "experiments": experiments,
            "participants": participants,
            "description": description,
            "status": "scheduled"
        }
        self.game_days.append(game_day)
        return game_day_id

    def run_game_day(self, game_day_id: str) -> Dict[str, ExperimentResult]:
        """Execute all experiments in a game day"""
        game_day = None
        for gd in self.game_days:
            if gd["game_day_id"] == game_day_id:
                game_day = gd
                break

        if not game_day:
            raise ValueError(f"Game day {game_day_id} not found")

        print(f"\n{'#'*60}")
        print(f"GAME DAY: {game_day['name']}")
        print(f"Date: {game_day['date']}")
        print(f"Participants: {', '.join(game_day['participants'])}")
        print(f"{'#'*60}\n")

        results = {}
        for exp_id in game_day["experiments"]:
            result = self.chaos_engine.run_experiment(exp_id)
            results[exp_id] = result
            print()

        # Calculate summary
        total_failures = sum(r.system_failures for r in results.values())
        total_recovered = sum(r.recovered for r in results.values())

        print(f"\n{'#'*60}")
        print("GAME DAY SUMMARY")
        print(f"  Total Experiments: {len(results)}")
        print(f"  Total Failures: {total_failures}")
        print(f"  Total Recovered: {total_recovered}")
        print(f"  Resilience Score: {self.chaos_engine.get_resilience_score():.2%}")
        print(f"{'#'*60}\n")

        return results


# Demo Agent System for testing
class DemoAgentSystem:
    """Demo agent system for chaos testing"""

    def __init__(self):
        self.agents: Dict[str, Dict] = {}
        self.message_queue: List[Dict] = []

    def add_agent(self, agent_id: str, agent_type: str = "default"):
        self.agents[agent_id] = {
            "agent_id": agent_id,
            "type": agent_type,
            "status": "active",
            "messages_processed": 0,
            "failures_recovered": 0
        }

    def recover_from_failure(self, target: str, action: ChaosAction) -> bool:
        """Simulate recovery from failure"""
        if target in self.agents:
            self.agents[target]["failures_recovered"] += 1

            # Simulate recovery time
            time.sleep(random.uniform(0.05, 0.2))

            # Most failures are recoverable
            return random.random() < 0.9

        return False

    def process_message(self, message: Dict) -> bool:
        """Process a message (for chaos testing)"""
        self.message_queue.append(message)
        return True


def main():
    """Demonstrate Chaos Engineering"""
    print("=" * 60)
    print("Chaos Engineering for Agent OS - Day 83")
    print("=" * 60)

    # Create demo system
    agent_system = DemoAgentSystem()
    agent_system.add_agent("agent_001", "research")
    agent_system.add_agent("agent_002", "analysis")
    agent_system.add_agent("agent_003", "execution")

    # Create chaos engine
    chaos = ChaosEngine()

    # Create experiments
    print("\n[Creating Chaos Experiments]")

    exp1 = chaos.create_experiment(
        name="Message Delay Test",
        action=ChaosAction.DELAY_MESSAGE,
        target="agent_001",
        duration_seconds=10,
        blast_radius=BlastRadius.CONTAINER,
        injection_rate=0.5,
        description="Test system behavior under delayed messages"
    )
    print(f"  Created: {exp1}")

    exp2 = chaos.create_experiment(
        name="Agent Failure Test",
        action=ChaosAction.TIMEOUT,
        target="agent_002",
        duration_seconds=10,
        blast_radius=BlastRadius.POD,
        injection_rate=0.3,
        description="Test agent recovery from timeout failures"
    )
    print(f"  Created: {exp2}")

    exp3 = chaos.create_experiment(
        name="Message Corruption Test",
        action=ChaosAction.CORRUPT_MESSAGE,
        target="agent_003",
        duration_seconds=8,
        blast_radius=BlastRadius.CONTAINER,
        injection_rate=0.4,
        description="Test message validation and error handling"
    )
    print(f"  Created: {exp3}")

    # Run first experiment
    print("\n[Running Experiment 1: Message Delay Test]")
    result1 = chaos.run_experiment(exp1, agent_system)
    print(f"\n  Result: {result1.status.value}")
    print(f"  Failures Injected: {result1.failures_injected}")
    print(f"  System Failures: {result1.system_failures}")
    print(f"  Recovered: {result1.recovered}")

    # Run second experiment
    print("\n[Running Experiment 2: Agent Failure Test]")
    result2 = chaos.run_experiment(exp2, agent_system)
    print(f"\n  Result: {result2.status.value}")
    print(f"  Failures Injected: {result2.failures_injected}")
    print(f"  System Failures: {result2.system_failures}")
    print(f"  Recovered: {result2.recovered}")

    # Run game day
    print("\n[Running Game Day]")
    game_day = GameDayScheduler(chaos)
    gd_id = game_day.schedule_game_day(
        name="Q1 Resilience Test",
        date=datetime.now(),
        experiments=[exp1, exp2, exp3],
        participants=["ops_team", "dev_team", "sre_team"],
        description="Quarterly chaos game day"
    )

    # Calculate resilience score
    print("\n[Resilience Analysis]")
    score = chaos.get_resilience_score()
    print(f"  System Resilience Score: {score:.2%}")

    if score >= 0.8:
        print("  Status: EXCELLENT - System handles failures well")
    elif score >= 0.6:
        print("  Status: GOOD - Minor improvements needed")
    elif score >= 0.4:
        print("  Status: FAIR - Significant improvements needed")
    else:
        print("  Status: POOR - Critical fixes required")

    print("\n" + "=" * 60)
    print("Chaos Engineering demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()