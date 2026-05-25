"""
Day 84: A/B Testing for Agents
===============================

Implementing A/B testing capabilities for agent systems to compare
different agent configurations, prompts, and strategies.

Key Concepts:
- Variant testing
- Statistical significance
- Metric comparison
- Agent behavior comparison
- Experiment design
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import random
import math
from collections import defaultdict


class ExperimentStatus(Enum):
    """A/B test status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TrafficAllocation(Enum):
    """Traffic allocation strategy"""
    FIXED = "fixed"  # Fixed 50/50 split
    ADAPTIVE = "adaptive"  # Adjusts based on performance
    EXPLORATION = "exploration"  # More exploration early


@dataclass
class Variant:
    """Represents a test variant (control or treatment)"""
    variant_id: str
    name: str
    description: str
    config: Dict[str, Any]
    weight: float = 0.5  # Traffic weight (0.0 to 1.0)


@dataclass
class Metric:
    """A metric to track in the experiment"""
    metric_id: str
    name: str
    description: str
    metric_type: str  # "counter", "gauge", "histogram"
    higher_is_better: bool = True


@dataclass
class MetricValue:
    """A recorded metric value"""
    metric_id: str
    variant_id: str
    session_id: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Results from an A/B test"""
    experiment_id: str
    variant_id: str
    sample_size: int
    mean: float
    std_dev: float
    confidence_interval: tuple
    conversion_rate: Optional[float] = None


@dataclass
class ABExperiment:
    """A/B test experiment definition"""
    experiment_id: str
    name: str
    description: str
    variants: List[Variant]
    metrics: List[Metric]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    traffic_allocation: TrafficAllocation = TrafficAllocation.FIXED
    min_sample_size: int = 100
    confidence_level: float = 0.95
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StatisticalAnalyzer:
    """
    Statistical Analyzer
    ====================

    Provides statistical analysis for A/B tests.
    """

    @staticmethod
    def calculate_mean(values: List[float]) -> float:
        """Calculate mean"""
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def calculate_std_dev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        mean = StatisticalAnalyzer.calculate_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    @staticmethod
    def calculate_confidence_interval(
        values: List[float],
        confidence_level: float = 0.95
    ) -> tuple:
        """Calculate confidence interval"""
        if not values:
            return (0.0, 0.0)

        n = len(values)
        mean = StatisticalAnalyzer.calculate_mean(values)
        std_err = StatisticalAnalyzer.calculate_std_dev(values) / math.sqrt(n)

        # Z-score for 95% confidence
        z_score = 1.96 if confidence_level == 0.95 else 2.576

        margin = z_score * std_err
        return (mean - margin, mean + margin)

    @staticmethod
    def t_test(
        control: List[float],
        treatment: List[float],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Perform t-test between two groups"""
        if not control or not treatment:
            return {"significant": False, "p_value": 1.0}

        n1, n2 = len(control), len(treatment)
        mean1 = StatisticalAnalyzer.calculate_mean(control)
        mean2 = StatisticalAnalyzer.calculate_mean(treatment)
        var1 = StatisticalAnalyzer.calculate_std_dev(control) ** 2
        var2 = StatisticalAnalyzer.calculate_std_dev(treatment) ** 2

        # Pooled variance
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        std_err = math.sqrt(pooled_var * (1/n1 + 1/n2))

        if std_err == 0:
            return {"significant": False, "p_value": 1.0}

        t_stat = (mean1 - mean2) / std_err

        # Approximate p-value (two-tailed)
        df = n1 + n2 - 2
        p_value = 2 * (1 - StatisticalAnalyzer._t_cdf(abs(t_stat), df))

        return {
            "significant": p_value < (1 - confidence_level),
            "p_value": p_value,
            "t_statistic": t_stat,
            "mean_control": mean1,
            "mean_treatment": mean2,
            "difference": mean2 - mean1,
            "relative_difference": (mean2 - mean1) / mean1 if mean1 != 0 else 0
        }

    @staticmethod
    def _t_cdf(t: float, df: int) -> float:
        """Approximate t-distribution CDF"""
        # Simplified approximation
        x = df / (df + t * t)
        return 1 - 0.5 * x ** (df / 2)
        # Note: This is a simplified version

    @staticmethod
    def calculate_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        confidence_level: float = 0.95,
        power: float = 0.8
    ) -> int:
        """Calculate required sample size"""
        alpha = 1 - confidence_level
        z_alpha = 1.96 if alpha == 0.05 else 2.576

        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        p_avg = (p1 + p2) / 2

        if p1 == 0 or p2 == 0 or p_avg == 0 or p1 == 1 or p2 == 1:
            return 100

        n = (2 * p_avg * (1 - p_avg) * (z_alpha ** 2)) / (
            (p1 - p2) ** 2
        )

        return int(math.ceil(n))

    @staticmethod
    def chi_square_test(
        control_success: int,
        control_total: int,
        treatment_success: int,
        treatment_total: int
    ) -> Dict[str, Any]:
        """Chi-square test for conversion rates"""
        if control_total == 0 or treatment_total == 0:
            return {"significant": False, "p_value": 1.0}

        # Expected values
        total = control_total + treatment_total
        pooled_rate = (control_success + treatment_success) / total

        expected_control_success = control_total * pooled_rate
        expected_treatment_success = treatment_total * pooled_rate

        # Chi-square statistic
        control_fail = control_total - control_success
        treatment_fail = treatment_total - treatment_success
        expected_control_fail = control_total * (1 - pooled_rate)
        expected_treatment_fail = treatment_total * (1 - pooled_rate)

        chi_sq = (
            (control_success - expected_control_success) ** 2 / expected_control_success +
            (treatment_success - expected_treatment_success) ** 2 / expected_treatment_success +
            (control_fail - expected_control_fail) ** 2 / expected_control_fail +
            (treatment_fail - expected_treatment_fail) ** 2 / expected_treatment_fail
        )

        # One degree of freedom, approximate p-value
        p_value = math.exp(-chi_sq / 2) if chi_sq > 0 else 1.0

        control_rate = control_success / control_total
        treatment_rate = treatment_success / treatment_total

        return {
            "significant": p_value < 0.05,
            "p_value": p_value,
            "chi_square": chi_sq,
            "control_rate": control_rate,
            "treatment_rate": treatment_rate,
            "lift": (treatment_rate - control_rate) / control_rate if control_rate > 0 else 0
        }


class ABTestingEngine:
    """
    A/B Testing Engine
    ===================

    Manages A/B experiments for agent systems.
    """

    def __init__(self):
        self.experiments: Dict[str, ABExperiment] = {}
        self.variant_assignments: Dict[str, str] = {}  # session_id -> variant_id
        self.metric_values: Dict[str, List[MetricValue]] = defaultdict(list)
        self.sessions: Dict[str, Dict] = {}
        self.analyzer = StatisticalAnalyzer()

    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Variant],
        metrics: List[Metric],
        traffic_allocation: TrafficAllocation = TrafficAllocation.FIXED,
        min_sample_size: int = 100,
        confidence_level: float = 0.95
    ) -> str:
        """Create a new A/B test"""
        experiment_id = str(uuid.uuid4())[:8]

        experiment = ABExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants=variants,
            metrics=metrics,
            traffic_allocation=traffic_allocation,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level
        )

        self.experiments[experiment_id] = experiment
        return experiment_id

    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()
        return True

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an experiment"""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.now()
        return True

    def assign_variant(self, experiment_id: str, session_id: str) -> Optional[str]:
        """Assign a variant to a session based on traffic allocation"""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]

        if experiment.status != ExperimentStatus.RUNNING:
            return None

        # Use consistent hashing for same session
        hash_val = hash(f"{experiment_id}:{session_id}") % 1000 / 1000

        cumulative_weight = 0
        for variant in experiment.variants:
            cumulative_weight += variant.weight
            if hash_val < cumulative_weight:
                self.variant_assignments[session_id] = variant.variant_id

                # Initialize session
                self.sessions[session_id] = {
                    "experiment_id": experiment_id,
                    "variant_id": variant.variant_id,
                    "created_at": datetime.now(),
                    "metrics": {}
                }

                return variant.variant_id

        return None

    def record_metric(
        self,
        session_id: str,
        metric_name: str,
        value: float,
        metadata: Optional[Dict] = None
    ):
        """Record a metric value for a session"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        experiment_id = session["experiment_id"]
        variant_id = session["variant_id"]

        # Find metric
        experiment = self.experiments[experiment_id]
        metric = next((m for m in experiment.metrics if m.name == metric_name), None)

        if not metric:
            return

        metric_value = MetricValue(
            metric_id=metric.metric_id,
            variant_id=variant_id,
            session_id=session_id,
            value=value,
            metadata=metadata or {}
        )

        self.metric_values[metric.metric_id].append(metric_value)

    def get_variant_config(
        self,
        experiment_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the configuration for a session's variant"""
        variant_id = self.variant_assignments.get(session_id)
        if not variant_id:
            return None

        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        variant = next((v for v in experiment.variants if v.variant_id == variant_id), None)
        return variant.config if variant else None

    def analyze_experiment(
        self,
        experiment_id: str,
        metric_name: str
    ) -> Dict[str, Any]:
        """Analyze experiment results for a metric"""
        if experiment_id not in self.experiments:
            return {}

        experiment = self.experiments[experiment_id]

        # Find metric
        metric = next((m for m in experiment.metrics if m.name == metric_name), None)
        if not metric:
            return {}

        metric_values = self.metric_values.get(metric.metric_id, [])

        # Group by variant
        variant_data: Dict[str, List[float]] = defaultdict(list)
        for mv in metric_values:
            variant_data[mv.variant_id].append(mv.value)

        results = {}
        variant_ids = list(variant_data.keys())

        # Calculate statistics for each variant
        for variant_id in variant_ids:
            values = variant_data[variant_id]
            results[variant_id] = {
                "sample_size": len(values),
                "mean": StatisticalAnalyzer.calculate_mean(values),
                "std_dev": StatisticalAnalyzer.calculate_std_dev(values),
                "confidence_interval": StatisticalAnalyzer.calculate_confidence_interval(
                    values, experiment.confidence_level
                )
            }

        # Perform statistical tests between variants
        if len(variant_ids) >= 2:
            control_id = variant_ids[0]
            for i in range(1, len(variant_ids)):
                treatment_id = variant_ids[i]
                test_result = StatisticalAnalyzer.t_test(
                    variant_data[control_id],
                    variant_data[treatment_id],
                    experiment.confidence_level
                )
                results[f"{control_id}_vs_{treatment_id}"] = test_result

        return results

    def get_winner(
        self,
        experiment_id: str,
        metric_name: str
    ) -> Optional[str]:
        """Determine the winning variant"""
        analysis = self.analyze_experiment(experiment_id, metric_name)

        if not analysis:
            return None

        # Find variant with best metric
        experiment = self.experiments[experiment_id]
        metric = next((m for m in experiment.metrics if m.name == metric_name), None)

        if not metric:
            return None

        best_variant = None
        best_value = float('-inf') if metric.higher_is_better else float('inf')

        for key, value in analysis.items():
            if "_vs_" in key:
                continue

            if isinstance(value, dict) and "mean" in value:
                mean = value["mean"]
                if metric.higher_is_better:
                    if mean > best_value:
                        best_value = mean
                        best_variant = key
                else:
                    if mean < best_value:
                        best_value = mean
                        best_variant = key

        return best_variant

    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment status"""
        if experiment_id not in self.experiments:
            return {}

        experiment = self.experiments[experiment_id]

        # Count sessions
        sessions = [
            s for s in self.sessions.values()
            if s["experiment_id"] == experiment_id
        ]

        # Get total samples per variant
        variant_samples = {}
        for variant in experiment.variants:
            variant_samples[variant.variant_id] = len([
                s for s in sessions if s["variant_id"] == variant.variant_id
            ])

        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "status": experiment.status.value,
            "total_sessions": len(sessions),
            "variant_samples": variant_samples,
            "min_sample_size": experiment.min_sample_size,
            "sample_size_met": len(sessions) >= experiment.min_sample_size
        }


class AgentVariantTester:
    """
    Agent Variant Tester
    ====================

    Tests different agent configurations using A/B testing.
    """

    def __init__(self, ab_engine: ABTestingEngine):
        self.ab_engine = ab_engine
        self.agents: Dict[str, Dict] = {}

    def create_agent_test(
        self,
        test_name: str,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        metrics: List[Metric]
    ) -> str:
        """Create an A/B test for agent configurations"""
        control = Variant(
            variant_id="control",
            name="Control",
            description="Original agent configuration",
            config=control_config,
            weight=0.5
        )

        treatment = Variant(
            variant_id="treatment",
            name="Treatment",
            description="New agent configuration",
            config=treatment_config,
            weight=0.5
        )

        return self.ab_engine.create_experiment(
            name=test_name,
            description=f"A/B test for agent: {test_name}",
            variants=[control, treatment],
            metrics=metrics,
            traffic_allocation=TrafficAllocation.FIXED
        )

    def run_agent_task(
        self,
        experiment_id: str,
        session_id: str,
        task_fn: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Run a task with the assigned agent variant"""
        # Get variant config
        config = self.ab_engine.get_variant_config(experiment_id, session_id)

        if not config:
            return None

        # Execute task and measure
        start_time = datetime.now()

        try:
            result = task_fn(*args, config=config, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Record metrics
        self.ab_engine.record_metric(session_id, "task_duration", duration)
        self.ab_engine.record_metric(session_id, "task_success", 1.0 if success else 0.0)

        return result


def main():
    """Demonstrate A/B Testing for Agents"""
    print("=" * 60)
    print("A/B Testing for Agents - Day 84")
    print("=" * 60)

    # Create A/B testing engine
    ab_engine = ABTestingEngine()

    # Define metrics
    metrics = [
        Metric(
            metric_id="task_duration",
            name="task_duration",
            description="Time to complete task",
            metric_type="histogram",
            higher_is_better=False
        ),
        Metric(
            metric_id="task_success",
            name="task_success",
            description="Task completion rate",
            metric_type="counter",
            higher_is_better=True
        ),
        Metric(
            metric_id="user_satisfaction",
            name="user_satisfaction",
            description="User satisfaction score",
            metric_type="gauge",
            higher_is_better=True
        )
    ]

    # Create A/B test for agent prompt strategies
    experiment_id = ab_engine.create_experiment(
        name="Prompt Strategy Test",
        description="Compare different prompt engineering strategies",
        variants=[
            Variant(
                variant_id="control",
                name="Detailed Prompts",
                description="Use detailed, explicit prompts",
                config={"prompt_style": "detailed", "examples": 5},
                weight=0.5
            ),
            Variant(
                variant_id="treatment",
                name="Minimal Prompts",
                description="Use minimal, concise prompts",
                config={"prompt_style": "minimal", "examples": 1},
                weight=0.5
            )
        ],
        metrics=metrics,
        min_sample_size=50
    )

    print(f"\n[Created Experiment: {experiment_id}]")

    # Start experiment
    ab_engine.start_experiment(experiment_id)

    # Simulate sessions
    print("\n[Running Simulation]")

    for i in range(100):
        session_id = f"session_{i}"

        # Assign variant
        variant = ab_engine.assign_variant(experiment_id, session_id)

        if variant == "control":
            # Simulate control behavior (detailed prompts)
            duration = random.gauss(5.0, 1.0)
            success = random.random() < 0.85
            satisfaction = random.gauss(4.0, 0.5)
        else:
            # Simulate treatment behavior (minimal prompts)
            duration = random.gauss(4.0, 1.5)  # Faster but more variable
            success = random.random() < 0.80
            satisfaction = random.gauss(3.8, 0.7)

        # Record metrics
        ab_engine.record_metric(session_id, "task_duration", duration)
        ab_engine.record_metric(session_id, "task_success", 1.0 if success else 0.0)
        ab_engine.record_metric(session_id, "user_satisfaction", max(1, min(5, satisfaction)))

    # Analyze results
    print("\n[Analyzing Results]")

    status = ab_engine.get_experiment_status(experiment_id)
    print(f"  Total Sessions: {status['total_sessions']}")
    print(f"  Sample Size Met: {status['sample_size_met']}")
    print(f"  Variant Distribution: {status['variant_samples']}")

    # Analyze task duration
    print("\n[Task Duration Analysis]")
    duration_analysis = ab_engine.analyze_experiment(experiment_id, "task_duration")
    for variant_id, stats in duration_analysis.items():
        if "_vs_" not in variant_id:
            print(f"  {variant_id}:")
            print(f"    Mean: {stats['mean']:.2f}s")
            print(f"    Std Dev: {stats['std_dev']:.2f}s")
            print(f"    Sample Size: {stats['sample_size']}")

    # Analyze success rate
    print("\n[Task Success Analysis]")
    success_analysis = ab_engine.analyze_experiment(experiment_id, "task_success")
    for variant_id, stats in success_analysis.items():
        if "_vs_" not in variant_id:
            print(f"  {variant_id}:")
            print(f"    Mean: {stats['mean']:.2%}")
            print(f"    Sample Size: {stats['sample_size']}")

    # Statistical comparison
    print("\n[Statistical Comparison]")
    comparison = duration_analysis.get("control_vs_treatment", {})
    if comparison:
        print(f"  Significant: {comparison.get('significant', False)}")
        print(f"  P-Value: {comparison.get('p_value', 0):.4f}")
        print(f"  Mean Difference: {comparison.get('difference', 0):.2f}s")
        print(f"  Relative Difference: {comparison.get('relative_difference', 0):.2%}")

    # Determine winner
    winner = ab_engine.get_winner(experiment_id, "task_duration")
    print(f"\n  Winning Variant: {winner}")

    # Calculate sample size needed
    required = StatisticalAnalyzer.calculate_sample_size(
        baseline_rate=0.5,
        minimum_detectable_effect=0.1
    )
    print(f"\n[Sample Size Calculation]")
    print(f"  Required sample size: {required}")

    print("\n" + "=" * 60)
    print("A/B Testing demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()