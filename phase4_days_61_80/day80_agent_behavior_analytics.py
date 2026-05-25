"""
Day 80: Agent Behavior Analytics
================================

Comprehensive behavior analytics for agent systems with metrics,
performance tracking, and reporting capabilities.

Key Concepts:
- Behavior metrics collection
- Performance analytics
- Anomaly detection
- Trend analysis
- Reporting dashboards
- Agent scoring
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import random
import statistics


class MetricType(Enum):
    """Types of metrics collected"""
    PERFORMANCE = "performance"
    ACCURACY = "accuracy"
    RELIABILITY = "reliability"
    EFFICIENCY = "efficiency"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    RESOURCE_USAGE = "resource_usage"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    metric_type: MetricType
    agent_id: str
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class BehaviorEvent:
    """Agent behavior event"""
    event_id: str
    agent_id: str
    action: str
    outcome: str
    duration: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentScore:
    """Overall agent performance score"""
    agent_id: str
    overall_score: float
    performance_score: float
    reliability_score: float
    efficiency_score: float
    last_updated: datetime
    trend: str  # improving, declining, stable


class MetricsCollector:
    """
    Metrics Collector
    =================

    Collects and aggregates agent behavior metrics.
    """

    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.events: deque = deque(maxlen=50000)

    def record_metric(self, metric: Metric):
        """Record a single metric"""
        key = f"{metric.agent_id}:{metric.name}"
        if key not in self.metrics:
            self.metrics[key] = deque(maxlen=10000)
        self.metrics[key].append(metric)

        # Prune old metrics
        self._prune_old_metrics()

    def record_event(self, event: BehaviorEvent):
        """Record a behavior event"""
        self.events.append(event)

    def _prune_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for key in self.metrics:
            metrics_list = list(self.metrics[key])
            self.metrics[key] = deque(
                (m for m in metrics_list if m.timestamp > cutoff),
                maxlen=10000
            )

    def get_metrics(
        self,
        agent_id: str,
        metric_name: str,
        since: Optional[datetime] = None
    ) -> List[Metric]:
        """Get metrics for a specific agent and metric name"""
        key = f"{agent_id}:{metric_name}"
        if key not in self.metrics:
            return []

        metrics = list(self.metrics[key])
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        return metrics

    def get_aggregated_metrics(
        self,
        agent_id: str,
        metric_name: str,
        interval_minutes: int = 60
    ) -> Dict[str, float]:
        """Get aggregated metrics (avg, min, max, count)"""
        metrics = self.get_metrics(agent_id, metric_name)
        if not metrics:
            return {}

        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0
        }


class AnomalyDetector:
    """
    Anomaly Detector
    ================

    Detects anomalous behavior patterns in agent metrics.
    """

    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity
        self.baselines: Dict[str, Dict[str, float]] = {}

    def update_baseline(
        self,
        agent_id: str,
        metric_name: str,
        value: float
    ):
        """Update baseline statistics for a metric"""
        key = f"{agent_id}:{metric_name}"
        if key not in self.baselines:
            self.baselines[key] = {
                "mean": value,
                "values": [value],
                "stdev": 0
            }
        else:
            baseline = self.baselines[key]
            baseline["values"].append(value)
            if len(baseline["values"]) > 100:
                baseline["values"] = baseline["values"][-100:]

            baseline["mean"] = statistics.mean(baseline["values"])
            if len(baseline["values"]) > 1:
                baseline["stdev"] = statistics.stdev(baseline["values"])

    def detect_anomaly(
        self,
        agent_id: str,
        metric_name: str,
        value: float
    ) -> Tuple[bool, float]:
        """Detect if a value is anomalous"""
        key = f"{agent_id}:{metric_name}"
        if key not in self.baselines:
            self.update_baseline(agent_id, metric_name, value)
            return False, 0.0

        baseline = self.baselines[key]
        if baseline["stdev"] == 0:
            return False, 0.0

        z_score = abs(value - baseline["mean"]) / baseline["stdev"]
        is_anomalous = z_score > self.sensitivity

        return is_anomalous, z_score


class TrendAnalyzer:
    """
    Trend Analyzer
    ==============

    Analyzes trends in agent behavior over time.
    """

    def __init__(self):
        self.history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def add_data_point(self, agent_id: str, metric_name: str, value: float):
        """Add a data point for trend analysis"""
        key = f"{agent_id}:{metric_name}"
        self.history[key].append({
            "value": value,
            "timestamp": datetime.now()
        })

    def analyze_trend(
        self,
        agent_id: str,
        metric_name: str,
        window_size: int = 20
    ) -> str:
        """Analyze the trend of a metric"""
        key = f"{agent_id}:{metric_name}"
        if key not in self.history or len(self.history[key]) < window_size:
            return "insufficient_data"

        data = list(self.history[key])[-window_size:]
        values = [d["value"] for d in data]

        # Calculate simple linear trend
        n = len(values)
        if n < 2:
            return "stable"

        # Calculate slope using least squares
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        # Normalize slope relative to mean
        if y_mean != 0:
            normalized_slope = abs(slope) / y_mean
        else:
            normalized_slope = 0

        if normalized_slope < 0.05:
            return "stable"
        elif slope > 0:
            return "improving"
        else:
            return "declining"


class BehaviorAnalytics:
    """
    Behavior Analytics
    ===================

    Main analytics engine for agent behavior analysis.
    """

    def __init__(self):
        self.collector = MetricsCollector()
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.agent_scores: Dict[str, AgentScore] = {}

    def track_action(
        self,
        agent_id: str,
        action: str,
        outcome: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track an agent action"""
        # Record the event
        event = BehaviorEvent(
            event_id=str(random.randint(100000, 999999)),
            agent_id=agent_id,
            action=action,
            outcome=outcome,
            duration=duration,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.collector.record_event(event)

        # Record metrics
        self.collector.record_metric(Metric(
            name="action_duration",
            value=duration,
            timestamp=datetime.now(),
            metric_type=MetricType.RESPONSE_TIME,
            agent_id=agent_id
        ))

        if outcome == "success":
            self.collector.record_metric(Metric(
                name="success_count",
                value=1,
                timestamp=datetime.now(),
                metric_type=MetricType.ACCURACY,
                agent_id=agent_id
            ))
        elif outcome == "error":
            self.collector.record_metric(Metric(
                name="error_count",
                value=1,
                timestamp=datetime.now(),
                metric_type=MetricType.ERROR_RATE,
                agent_id=agent_id
            ))

        # Update anomaly detector
        self.anomaly_detector.update_baseline(agent_id, "action_duration", duration)

        # Update trend analyzer
        self.trend_analyzer.add_data_point(agent_id, "action_duration", duration)

        # Check for anomalies
        is_anomalous, z_score = self.anomaly_detector.detect_anomaly(
            agent_id, "action_duration", duration
        )
        if is_anomalous:
            return {
                "status": "anomaly_detected",
                "z_score": z_score,
                "action": action,
                "duration": duration
            }

        return {"status": "normal"}

    def calculate_agent_score(self, agent_id: str) -> AgentScore:
        """Calculate overall agent performance score"""
        # Get performance metrics
        perf_metrics = self.collector.get_aggregated_metrics(
            agent_id, "action_duration"
        )

        # Get success/error metrics
        success_metrics = self.collector.get_aggregated_metrics(
            agent_id, "success_count"
        )
        error_metrics = self.collector.get_aggregated_metrics(
            agent_id, "error_count"
        )

        # Calculate individual scores (0-100)
        performance_score = 100.0
        if perf_metrics and "avg" in perf_metrics:
            # Lower is better for response time
            performance_score = max(0, 100 - (perf_metrics.get("avg", 0) / 10))

        reliability_score = 100.0
        if success_metrics and error_metrics:
            total = success_metrics.get("count", 0) + error_metrics.get("count", 0)
            if total > 0:
                reliability_score = (success_metrics["count"] / total) * 100

        # Efficiency score based on error rate
        efficiency_score = max(0, 100 - (error_metrics.get("count", 0) * 5))

        # Calculate overall score (weighted average)
        overall_score = (
            performance_score * 0.3 +
            reliability_score * 0.4 +
            efficiency_score * 0.3
        )

        # Get trend
        trend = self.trend_analyzer.analyze_trend(agent_id, "action_duration")

        score = AgentScore(
            agent_id=agent_id,
            overall_score=overall_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            efficiency_score=efficiency_score,
            last_updated=datetime.now(),
            trend=trend
        )

        self.agent_scores[agent_id] = score
        return score

    def generate_report(self, agent_id: str) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        score = self.calculate_agent_score(agent_id)

        # Get recent events
        recent_events = [
            e for e in self.collector.events
            if e.agent_id == agent_id
        ][-100:]

        # Calculate action distribution
        action_counts = defaultdict(int)
        outcome_counts = defaultdict(int)
        for event in recent_events:
            action_counts[event.action] += 1
            outcome_counts[event.outcome] += 1

        return {
            "agent_id": agent_id,
            "generated_at": datetime.now().isoformat(),
            "scores": {
                "overall": score.overall_score,
                "performance": score.performance_score,
                "reliability": score.reliability_score,
                "efficiency": score.efficiency_score,
                "trend": score.trend
            },
            "metrics": {
                "total_events": len(recent_events),
                "action_distribution": dict(action_counts),
                "outcome_distribution": dict(outcome_counts)
            },
            "recommendations": self._generate_recommendations(score, recent_events)
        }

    def _generate_recommendations(
        self,
        score: AgentScore,
        events: List[BehaviorEvent]
    ) -> List[str]:
        """Generate recommendations based on scores"""
        recommendations = []

        if score.performance_score < 70:
            recommendations.append(
                "Consider optimizing response time - performance score is below 70"
            )

        if score.reliability_score < 80:
            recommendations.append(
                "Improve reliability by reducing error rate"
            )

        if score.efficiency_score < 60:
            recommendations.append(
                "High error rate detected - review error handling"
            )

        if score.trend == "declining":
            recommendations.append(
                "Performance trend is declining - investigate recent changes"
            )

        # Check for error patterns
        error_events = [e for e in events if e.outcome == "error"]
        if len(error_events) > 10:
            error_actions = defaultdict(int)
            for e in error_events:
                error_actions[e.action] += 1

            top_error_action = max(error_actions.items(), key=lambda x: x[1])
            recommendations.append(
                f"Most errors ({top_error_action[1]}) occur during: {top_error_action[0]}"
            )

        if not recommendations:
            recommendations.append("Agent is performing optimally")

        return recommendations


def main():
    """Demonstrate Agent Behavior Analytics"""
    print("=" * 60)
    print("Agent Behavior Analytics - Day 80")
    print("=" * 60)

    # Initialize analytics
    analytics = BehaviorAnalytics()

    # Simulate agent actions
    agent_id = "agent_001"
    actions = [
        ("file_read", "success", 0.5),
        ("api_call", "success", 1.2),
        ("process_data", "success", 2.1),
        ("api_call", "error", 3.5),
        ("file_write", "success", 0.8),
        ("api_call", "success", 1.1),
        ("process_data", "success", 1.9),
        ("file_read", "success", 0.4),
        ("database_query", "success", 0.7),
        ("api_call", "success", 1.3),
    ]

    print("\n[Simulating Agent Actions]")
    for i, (action, outcome, duration) in enumerate(actions, 1):
        result = analytics.track_action(
            agent_id=agent_id,
            action=action,
            outcome=outcome,
            duration=duration
        )
        print(f"  Action {i}: {action} -> {outcome} ({duration}s)")

    # Calculate score
    print("\n[Calculating Agent Score]")
    score = analytics.calculate_agent_score(agent_id)
    print(f"  Overall Score: {score.overall_score:.1f}/100")
    print(f"  Performance: {score.performance_score:.1f}")
    print(f"  Reliability: {score.reliability_score:.1f}")
    print(f"  Efficiency: {score.efficiency_score:.1f}")
    print(f"  Trend: {score.trend}")

    # Generate report
    print("\n[Generating Analytics Report]")
    report = analytics.generate_report(agent_id)

    print(f"  Total Events: {report['metrics']['total_events']}")
    print(f"  Action Distribution:")
    for action, count in report['metrics']['action_distribution'].items():
        print(f"    - {action}: {count}")

    print(f"\n  Recommendations:")
    for rec in report['recommendations']:
        print(f"    - {rec}")

    print("\n" + "=" * 60)
    print("Analytics demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()