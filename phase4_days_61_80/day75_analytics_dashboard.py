"""
Day 75: Analytics Dashboard
===========================
Comprehensive analytics and metrics visualization for AI agents.

Key Concepts:
- Real-time metrics
- Time-series data
- Performance analytics
- Usage patterns
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import time
import random


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimeSeriesData:
    """Time series metric data"""
    name: str
    points: List[MetricPoint] = field(default_factory=list)

    def add(self, value: float, tags: Dict[str, str] = None):
        """Add a data point"""
        self.points.append(MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {}
        ))

    def get_range(self, duration: timedelta) -> List[MetricPoint]:
        """Get points in time range"""
        cutoff = datetime.now() - duration
        return [p for p in self.points if p.timestamp >= cutoff]

    def get_average(self, duration: timedelta = None) -> float:
        """Get average value"""
        points = self.get_range(duration) if duration else self.points
        if not points:
            return 0.0
        return sum(p.value for p in points) / len(points)

    def get_rate(self, duration: timedelta = None) -> float:
        """Get rate (values per second)"""
        points = self.get_range(duration) if duration else self.points
        if len(points) < 2:
            return 0.0
        time_range = (points[-1].timestamp - points[0].timestamp).total_seconds()
        if time_range == 0:
            return 0.0
        return len(points) / time_range


class AnalyticsEngine:
    """
    Analytics Engine
    =================

    Collects and analyzes agent metrics.
    """

    def __init__(self):
        self.time_series: Dict[str, TimeSeriesData] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.aggregations: Dict[str, Dict[str, float]] = {}

    def record_metric(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] = None
    ):
        """Record a metric value"""
        if name not in self.time_series:
            self.time_series[name] = TimeSeriesData(name)
        self.time_series[name].add(value, tags)

        # Update aggregations
        self._update_aggregations(name)

    def increment_counter(self, name: str, amount: int = 1):
        """Increment a counter"""
        self.counters[name] += amount

    def set_gauge(self, name: str, value: float):
        """Set a gauge value"""
        self.gauges[name] = value

    def _update_aggregations(self, name: str):
        """Update aggregated statistics"""
        if name not in self.time_series:
            return

        ts = self.time_series[name]
        points = ts.points[-100:]  # Last 100 points

        if points:
            values = [p.value for p in points]
            self.aggregations[name] = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "p50": self._percentile(values, 50),
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99)
            }

    def _percentile(self, values: List[float], p: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_metric(self, name: str) -> Optional[TimeSeriesData]:
        """Get time series data"""
        return self.time_series.get(name)

    def get_aggregation(self, name: str) -> Dict[str, float]:
        """Get aggregations for metric"""
        return self.aggregations.get(name, {})

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics data"""
        return {
            "time_series": {
                name: {
                    "points": len(ts.points),
                    "latest": ts.points[-1].value if ts.points else None
                }
                for name, ts in self.time_series.items()
            },
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "aggregations": self.aggregations.copy()
        }

    def query(
        self,
        metric_name: str,
        duration: timedelta = None,
        aggregation: str = "avg"
    ) -> float:
        """Query metric with aggregation"""
        ts = self.time_series.get(metric_name)
        if not ts:
            return 0.0

        if duration:
            points = ts.get_range(duration)
        else:
            points = ts.points

        if not points:
            return 0.0

        values = [p.value for p in points]

        if aggregation == "avg":
            return sum(values) / len(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "count":
            return len(values)
        elif aggregation == "p50":
            return self._percentile(values, 50)
        elif aggregation == "p95":
            return self._percentile(values, 95)
        elif aggregation == "p99":
            return self._percentile(values, 99)

        return 0.0


class AgentAnalytics:
    """
    Agent Analytics
    ================

    Analytics specific to AI agents.
    """

    def __init__(self, agent_id: str, analytics: AnalyticsEngine):
        self.agent_id = agent_id
        self.analytics = analytics
        self.prefix = f"agent.{agent_id}"

    def record_request(self, duration_ms: float, success: bool = True):
        """Record request metrics"""
        self.analytics.record_metric(
            f"{self.prefix}.request.duration",
            duration_ms,
            {"success": str(success)}
        )
        if success:
            self.analytics.increment_counter(f"{self.prefix}.requests.success")
        else:
            self.analytics.increment_counter(f"{self.prefix}.requests.failed")

    def record_token_usage(self, prompt_tokens: int, completion_tokens: int):
        """Record token usage"""
        total = prompt_tokens + completion_tokens
        self.analytics.record_metric(f"{self.prefix}.tokens.prompt", prompt_tokens)
        self.analytics.record_metric(f"{self.prefix}.tokens.completion", completion_tokens)
        self.analytics.record_metric(f"{self.prefix}.tokens.total", total)

    def record_task(self, task_type: str, duration_ms: float, success: bool):
        """Record task execution"""
        self.analytics.record_metric(
            f"{self.prefix}.task.duration",
            duration_ms,
            {"type": task_type, "success": str(success)}
        )
        self.analytics.increment_counter(f"{self.prefix}.tasks.{task_type}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "agent_id": self.agent_id,
            "requests": {
                "total": self.analytics.counters.get(f"{self.prefix}.requests.success", 0) +
                        self.analytics.counters.get(f"{self.prefix}.requests.failed", 0),
                "success": self.analytics.counters.get(f"{self.prefix}.requests.success", 0),
                "failed": self.analytics.counters.get(f"{self.prefix}.requests.failed", 0),
                "latency_avg": self.analytics.query(
                    f"{self.prefix}.request.duration",
                    aggregation="avg"
                ),
                "latency_p95": self.analytics.query(
                    f"{self.prefix}.request.duration",
                    aggregation="p95"
                )
            },
            "tokens": {
                "total": self.analytics.query(
                    f"{self.prefix}.tokens.total",
                    aggregation="sum"
                )
            }
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Day 75: Analytics Dashboard")
    print("=" * 70)

    # Create analytics engine
    analytics = AnalyticsEngine()

    # Simulate agent metrics
    print("\n[1] Recording Agent Metrics")
    print("-" * 40)

    agent1 = AgentAnalytics("data_processor", analytics)
    agent2 = AgentAnalytics("file_manager", analytics)

    # Simulate requests
    for i in range(20):
        duration = 100 + random.randint(-20, 50)
        success = random.random() > 0.1
        agent1.record_request(duration, success)

    # Simulate token usage
    agent1.record_token_usage(1500, 500)
    agent1.record_token_usage(2000, 800)

    # Simulate tasks
    agent1.record_task("extract", 250, True)
    agent1.record_task("transform", 180, True)
    agent1.record_task("load", 120, True)

    print("  Recorded 20 requests for data_processor agent")
    print("  Recorded token usage and task metrics")

    # Get analytics
    print("\n[2] Performance Summary")
    print("-" * 40)

    summary = agent1.get_performance_summary()
    print(f"  Agent: {summary['agent_id']}")
    print(f"  Total Requests: {summary['requests']['total']}")
    print(f"  Success Rate: {summary['requests']['success'] / max(1, summary['requests']['total']) * 100:.1f}%")
    print(f"  Avg Latency: {summary['requests']['latency_avg']:.2f}ms")
    print(f"  P95 Latency: {summary['requests']['latency_p95']:.2f}ms")
    print(f"  Total Tokens: {summary['tokens']['total']}")

    # Get all metrics
    print("\n[3] All Metrics Overview")
    print("-" * 40)

    all_metrics = analytics.get_all_metrics()
    print(f"  Time Series Metrics: {len(all_metrics['time_series'])}")
    print(f"  Counters: {len(all_metrics['counters'])}")
    print(f"  Gauges: {len(all_metrics['gauges'])}")

    # Query specific metrics
    print("\n[4] Query Metrics")
    print("-" * 40)

    avg_duration = analytics.query("agent.data_processor.request.duration", aggregation="avg")
    p95_duration = analytics.query("agent.data_processor.request.duration", aggregation="p95")
    total_requests = analytics.query("agent.data_processor.requests.success", aggregation="sum")

    print(f"  Average Duration: {avg_duration:.2f}ms")
    print(f"  P95 Duration: {p95_duration:.2f}ms")
    print(f"  Total Success Requests: {int(total_requests)}")

    # Aggregations
    print("\n[5] Detailed Aggregations")
    print("-" * 40)

    aggs = analytics.get_aggregation("agent.data_processor.request.duration")
    if aggs:
        print(f"  Count: {aggs['count']}")
        print(f"  Avg: {aggs['avg']:.2f}ms")
        print(f"  Min: {aggs['min']:.2f}ms")
        print(f"  Max: {aggs['max']:.2f}ms")
        print(f"  P50: {aggs['p50']:.2f}ms")
        print(f"  P95: {aggs['p95']:.2f}ms")
        print(f"  P99: {aggs['p99']:.2f}ms")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()