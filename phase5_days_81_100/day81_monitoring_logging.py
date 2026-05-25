"""
Day 81: Monitoring & Logging - Observability
==============================================
Skill: Observability
Mini Project: Agent Monitoring Dashboard

Implement comprehensive monitoring and logging for AI agents.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Log entry"""
    timestamp: str
    level: LogLevel
    message: str
    agent_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


class Logger:
    """Agent logging system"""

    def __init__(self, agent_id: str = "system"):
        self.agent_id = agent_id
        self.entries: List[LogEntry] = []

    def log(self, level: LogLevel, message: str, context: Dict = None):
        """Log an entry"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            agent_id=self.agent_id,
            context=context or {}
        )
        self.entries.append(entry)

        # Also print to console
        print(f"[{level.value}] {self.agent_id}: {message}")

    def debug(self, message: str, **kwargs):
        self.log(LogLevel.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        self.log(LogLevel.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        self.log(LogLevel.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        self.log(LogLevel.ERROR, message, kwargs)

    def critical(self, message: str, **kwargs):
        self.log(LogLevel.CRITICAL, message, kwargs)


class MetricsCollector:
    """Collect agent metrics"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}

    def record(self, metric_name: str, value: float):
        """Record a metric value"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def increment(self, counter_name: str, amount: int = 1):
        """Increment a counter"""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
        self.counters[counter_name] += amount

    def get_average(self, metric_name: str) -> float:
        """Get average for metric"""
        values = self.metrics.get(metric_name, [])
        return sum(values) / len(values) if values else 0.0

    def get_rate(self, counter_name: str) -> int:
        """Get counter value"""
        return self.counters.get(counter_name, 0)

    def get_stats(self) -> Dict[str, Any]:
        """Get all statistics"""
        return {
            "metrics": {
                name: {
                    "count": len(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for name, values in self.metrics.items()
            },
            "counters": self.counters.copy()
        }


class HealthChecker:
    """Health check for agents"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.checks: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_func):
        """Register a health check"""
        self.checks[name] = {
            "func": check_func,
            "last_check": None,
            "last_result": None
        }

    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "healthy": True,
            "checks": {}
        }

        for name, check in self.checks.items():
            try:
                result = await check["func"]()
                check["last_result"] = result
                check["last_check"] = datetime.now().isoformat()

                results["checks"][name] = {
                    "status": "healthy" if result else "unhealthy",
                    "checked_at": check["last_check"]
                }

                if not result:
                    results["healthy"] = False

            except Exception as e:
                results["checks"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                results["healthy"] = False

        return results


class MonitoringDashboard:
    """Monitoring dashboard for agents"""

    def __init__(self):
        self.loggers: Dict[str, Logger] = {}
        self.metrics = MetricsCollector()
        self.health_checkers: Dict[str, HealthChecker] = {}

    def get_logger(self, agent_id: str) -> Logger:
        """Get or create logger for agent"""
        if agent_id not in self.loggers:
            self.loggers[agent_id] = Logger(agent_id)
        return self.loggers[agent_id]

    def get_health_checker(self, agent_id: str) -> HealthChecker:
        """Get or create health checker"""
        if agent_id not in self.health_checkers:
            self.health_checkers[agent_id] = HealthChecker(agent_id)
        return self.health_checkers[agent_id]

    def record_request(self, agent_id: str, duration_ms: float):
        """Record request metrics"""
        self.metrics.record("request_duration", duration_ms)
        self.metrics.increment("total_requests")

    def record_error(self, agent_id: str):
        """Record error"""
        self.metrics.increment(f"errors_{agent_id}")

    def get_overview(self) -> Dict[str, Any]:
        """Get dashboard overview"""
        stats = self.metrics.get_stats()

        return {
            "agents": list(self.loggers.keys()),
            "metrics": stats,
            "health": {
                agent_id: checker.checks
                for agent_id, checker in self.health_checkers.items()
            }
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Monitoring & Logging Demo")
    print("=" * 70)

    # Create dashboard
    dashboard = MonitoringDashboard()

    # Logger
    print("\n[1] Logging")
    print("-" * 40)

    logger = dashboard.get_logger("agent_001")
    logger.info("Agent started")
    logger.info("Processing request", request_id="req_123")
    logger.warning("Rate limit approaching", remaining=10)
    logger.error("Failed to process", error="Timeout")

    # Metrics
    print("\n[2] Metrics")
    print("-" * 40)

    import asyncio

    async def simulate_requests():
        for i in range(10):
            duration = 100 + i * 10  # Simulated duration
            dashboard.record_request("agent_001", duration)
            await asyncio.sleep(0.01)

    asyncio.run(simulate_requests())

    stats = dashboard.metrics.get_stats()
    print(f"  Request duration avg: {stats['metrics']['request_duration']['avg']:.2f}ms")
    print(f"  Total requests: {stats['counters']['total_requests']}")

    # Health checks
    print("\n[3] Health Checks")
    print("-" * 40)

    checker = dashboard.get_health_checker("agent_001")

    async def check_memory():
        return True  # Healthy

    async def check_api():
        return True  # Healthy

    checker.register_check("memory", check_memory)
    checker.register_check("api", check_api)

    health = asyncio.run(checker.check_all())
    print(f"  Overall: {health['healthy']}")
    print(f"  Checks: {list(health['checks'].keys())}")

    # Dashboard overview
    print("\n[4] Dashboard Overview")
    print("-" * 40)

    overview = dashboard.get_overview()
    print(f"  Agents: {len(overview['agents'])}")
    print(f"  Metrics tracked: {len(overview['metrics']['metrics'])}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()