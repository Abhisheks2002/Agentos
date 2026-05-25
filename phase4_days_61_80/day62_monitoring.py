"""
Day 62: Monitoring & Observability - Production Metrics
=========================================================
Skill: System Monitoring
Mini Project: Agent Metrics Dashboard

Monitor AI agent performance and health in production.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MetricsCollector:
    """Collect and store metrics"""

    def __init__(self):
        self.metrics: List[Metric] = []
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}

    def increment(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Increment counter"""
        key = f"{name}:{labels or {}}"

        if key not in self.counters:
            self.counters[key] = 0

        self.counters[key] += value

        self.metrics.append(Metric(
            name=name,
            value=self.counters[key],
            metric_type=MetricType.COUNTER,
            labels=labels or {}
        ))

    def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set gauge value"""
        key = f"{name}:{labels or {}}"
        self.gauges[key] = value

        self.metrics.append(Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            labels=labels or {}
        ))

    def histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record histogram value"""
        self.metrics.append(Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            labels=labels or {}
        ))

    def timer(self, name: str, func, labels: Dict[str, str] = None):
        """Time a function"""
        start = time.time()
        result = func()
        duration = time.time() - start

        self.histogram(f"{name}_duration", duration, labels)

        return result


class HealthChecker:
    """Check agent health"""

    def __init__(self):
        self.checks: Dict[str, callable] = {}

    def register_check(self, name: str, check: callable):
        """Register health check"""
        self.checks[name] = check

    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}

        for name, check in self.checks.items():
            try:
                start = time.time()
                is_healthy = await check() if asyncio.iscoroutinefunction(check) else check()
                duration = time.time() - start

                results[name] = {
                    "healthy": is_healthy,
                    "duration_ms": duration * 1000
                }
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": str(e)
                }

        overall = all(r.get("healthy", False) for r in results.values())

        return {
            "overall_healthy": overall,
            "checks": results,
            "timestamp": datetime.now().isoformat()
        }


class AlertManager:
    """Manage alerts"""

    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []

    def trigger(self, severity: str, message: str, metadata: Dict = None):
        """Trigger an alert"""
        alert = {
            "severity": severity,  # info, warning, critical
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        self.alerts.append(alert)

    def get_active(self) -> List[Dict[str, Any]]:
        """Get active alerts (last hour)"""
        cutoff = datetime.now() - timedelta(hours=1)

        return [
            a for a in self.alerts
            if datetime.fromisoformat(a["timestamp"]) > cutoff
        ]


import asyncio


# Demo
def run_demo():
    print("=" * 70)
    print("Monitoring & Observability Demo")
    print("=" * 70)

    # Metrics
    print("\n[1] Metrics Collection")
    print("-" * 40)

    collector = MetricsCollector()

    collector.increment("requests_total", labels={"endpoint": "/api/chat"})
    collector.increment("requests_total", labels={"endpoint": "/api/chat"})
    collector.increment("errors_total", labels={"type": "timeout"})

    collector.gauge("active_agents", 5)
    collector.gauge("queue_size", 12)

    collector.histogram("response_time_ms", 145)
    collector.histogram("response_time_ms", 230)

    print(f"  Total metrics: {len(collector.metrics)}")
    print(f"  Counters: {collector.counters}")
    print(f"  Gauges: {collector.gauges}")

    # Health checks
    print("\n[2] Health Checks")
    print("-" * 40)

    async def check_database():
        await asyncio.sleep(0.1)
        return True

    async def check_api():
        await asyncio.sleep(0.1)
        return True

    health = HealthChecker()
    health.register_check("database", check_database)
    health.register_check("api", check_api)

    result = asyncio.run(health.check_all())

    print(f"  Overall healthy: {result['overall_healthy']}")
    for check, status in result['checks'].items():
        print(f"    {check}: {status['healthy']}")

    # Alerts
    print("\n[3] Alert Manager")
    print("-" * 40)

    alerts = AlertManager()

    alerts.trigger("warning", "High response time", {"value_ms": 500})
    alerts.trigger("info", "New agent registered", {"agent_id": "agent_123"})

    active = alerts.get_active()
    print(f"  Active alerts: {len(active)}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()