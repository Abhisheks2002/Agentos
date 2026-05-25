"""
Day 40: Reflection and Debugging
=================================
Skill: Self-Improvement
Mini Project: AgentDebugger

Building self-reflective and debuggable agent systems.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import traceback
from collections import defaultdict


class ReflectionLevel(str, Enum):
    """Level of reflection"""
    NONE = "none"
    BASIC = "basic"      # What happened
    DEEP = "deep"        # Why it happened
    META = "meta"        # How to improve


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """A log entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    level: LogLevel = LogLevel.INFO
    source: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None


@dataclass
class ExecutionTrace:
    """A trace of execution"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str = ""
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    status: str = "running"
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)  # Child trace IDs


@dataclass
class Reflection:
    """A reflection entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    level: ReflectionLevel = ReflectionLevel.BASIC
    trigger: str = ""  # What triggered the reflection
    observation: str = ""  # What was observed
    analysis: str = ""  # Analysis of the observation
    insight: str = ""  # Key insight
    improvement: str = ""  # Proposed improvement
    action_taken: str = ""


class AgentLogger:
    """Comprehensive logging for agents"""

    def __init__(self, source: str = "agent"):
        self.source = source
        self.logs: List[LogEntry] = []
        self.traces: Dict[str, ExecutionTrace] = {}
        self.current_trace: Optional[str] = None
        self.max_logs = 10000

    def log(self, level: LogLevel, message: str, data: Dict = None, trace_id: str = None):
        """Log a message"""
        entry = LogEntry(
            level=level,
            source=self.source,
            message=message,
            data=data or {},
            trace_id=trace_id or self.current_trace
        )

        self.logs.append(entry)

        # Maintain max size
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]

        return entry

    def debug(self, message: str, data: Dict = None):
        return self.log(LogLevel.DEBUG, message, data)

    def info(self, message: str, data: Dict = None):
        return self.log(LogLevel.INFO, message, data)

    def warning(self, message: str, data: Dict = None):
        return self.log(LogLevel.WARNING, message, data)

    def error(self, message: str, data: Dict = None):
        return self.log(LogLevel.ERROR, message, data)

    def critical(self, message: str, data: Dict = None):
        return self.log(LogLevel.CRITICAL, message, data)

    def start_trace(self, operation: str, inputs: Dict = None) -> str:
        """Start an execution trace"""
        trace = ExecutionTrace(
            operation=operation,
            inputs=inputs or {}
        )
        self.traces[trace.id] = trace
        self.current_trace = trace.id
        return trace.id

    def end_trace(self, status: str = "completed", outputs: Dict = None, error: str = None):
        """End an execution trace"""
        if not self.current_trace:
            return

        trace = self.traces[self.current_trace]
        trace.end_time = datetime.now().isoformat()
        trace.status = status
        if outputs:
            trace.outputs = outputs
        if error:
            trace.errors.append(error)

        self.current_trace = None

    def get_logs(self, level: LogLevel = None, source: str = None,
                 limit: int = 100) -> List[LogEntry]:
        """Get logs with optional filtering"""
        results = self.logs

        if level:
            results = [l for l in results if l.level == level]

        if source:
            results = [l for l in results if l.source == source]

        return results[-limit:]

    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """Get a trace by ID"""
        return self.traces.get(trace_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        counts = defaultdict(int)
        for log in self.logs:
            counts[log.level.value] += 1

        return {
            "total_logs": len(self.logs),
            "by_level": dict(counts),
            "active_traces": sum(1 for t in self.traces.values() if t.status == "running"),
            "total_traces": len(self.traces)
        }


class Reflector:
    """Self-reflection system for agents"""

    def __init__(self, logger: AgentLogger = None):
        self.logger = logger
        self.reflections: List[Reflection] = []
        self.insights: Dict[str, List[str]] = defaultdict(list)
        self.max_reflections = 1000

    async def reflect(
        self,
        trigger: str,
        observation: str,
        level: ReflectionLevel = ReflectionLevel.BASIC
    ) -> Reflection:
        """Perform reflection"""
        reflection = Reflection(
            trigger=trigger,
            observation=observation,
            level=level
        )

        # Analyze based on level
        if level == ReflectionLevel.BASIC:
            reflection.analysis = f"Observed: {observation}"
            reflection.insight = "Basic understanding achieved"

        elif level == ReflectionLevel.DEEP:
            reflection.analysis = self._analyze_deep(observation)
            reflection.insight = self._extract_insight(reflection.analysis)

        elif level == ReflectionLevel.META:
            reflection.analysis = self._analyze_deep(observation)
            reflection.insight = self._extract_insight(reflection.analysis)
            reflection.improvement = self._suggest_improvement()

        self.reflections.append(reflection)

        # Maintain max size
        if len(self.reflections) > self.max_reflections:
            self.reflections = self.reflections[-self.max_reflections:]

        # Store insight
        if reflection.insight:
            self.insights[trigger].append(reflection.insight)

        if self.logger:
            self.logger.info(f"Reflection: {reflection.insight}")

        return reflection

    def _analyze_deep(self, observation: str) -> str:
        """Deep analysis of observation"""
        # Simple pattern-based analysis
        analysis_parts = []

        if "error" in observation.lower() or "fail" in observation.lower():
            analysis_parts.append("Error pattern detected")
            analysis_parts.append("Root cause likely in recent changes")

        if "success" in observation.lower() or "complete" in observation.lower():
            analysis_parts.append("Positive outcome")
            analysis_parts.append("Current approach is working")

        if not analysis_parts:
            analysis_parts.append("Neutral observation")
            analysis_parts.append("No significant patterns detected")

        return ". ".join(analysis_parts)

    def _extract_insight(self, analysis: str) -> str:
        """Extract key insight from analysis"""
        # Simple extraction
        sentences = analysis.split(". ")
        if sentences:
            return sentences[0]
        return analysis

    def _suggest_improvement(self) -> str:
        """Suggest improvement"""
        # Check recent insights
        recent = self.reflections[-5:]
        errors = sum(1 for r in recent if "error" in r.observation.lower())

        if errors > 2:
            return "Consider adding more error handling"
        elif errors > 0:
            return "Review error handling in recent operations"

        return "Continue current approach"

    def get_recent_reflections(self, count: int = 10) -> List[Reflection]:
        """Get recent reflections"""
        return self.reflections[-count:]

    def get_insights(self, trigger: str = None) -> Dict[str, List[str]]:
        """Get stored insights"""
        if trigger:
            return {trigger: self.insights.get(trigger, [])}
        return dict(self.insights)


class Debugger:
    """Debugging system for agents"""

    def __init__(self, logger: AgentLogger = None):
        self.logger = logger
        self.breakpoints: Dict[str, bool] = {}
        self.watch_vars: Dict[str, Any] = {}
        self.step_count = 0

    def set_breakpoint(self, condition: str, enabled: bool = True):
        """Set a breakpoint"""
        self.breakpoints[condition] = enabled

    def remove_breakpoint(self, condition: str):
        """Remove a breakpoint"""
        if condition in self.breakpoints:
            del self.breakpoints[condition]

    def watch(self, variable: str, value: Any):
        """Watch a variable"""
        self.watch_vars[variable] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "changes": []
        }

    def update_watch(self, variable: str, value: Any):
        """Update a watched variable"""
        if variable in self.watch_vars:
            old_value = self.watch_vars[variable]["value"]
            if old_value != value:
                self.watch_vars[variable]["changes"].append({
                    "old": old_value,
                    "new": value,
                    "timestamp": datetime.now().isoformat()
                })
            self.watch_vars[variable]["value"] = value

    def check_breakpoint(self, context: Dict) -> bool:
        """Check if any breakpoint is hit"""
        for condition, enabled in self.breakpoints.items():
            if not enabled:
                continue

            try:
                # Simple condition check
                if condition in str(context).lower():
                    return True
            except:
                pass

        return False

    def get_watch_vars(self) -> Dict[str, Any]:
        """Get watched variables"""
        return {
            k: {
                "current_value": v["value"],
                "change_count": len(v["changes"]),
                "last_change": v["changes"][-1] if v["changes"] else None
            }
            for k, v in self.watch_vars.items()
        }

    def step(self):
        """Increment step counter"""
        self.step_count += 1
        return self.step_count


class AgentDebugger:
    """Complete debugging and reflection system"""

    def __init__(self, agent_name: str = "agent"):
        self.agent_name = agent_name
        self.logger = AgentLogger(source=agent_name)
        self.reflector = Reflector(self.logger)
        self.debugger = Debugger(self.logger)

    async def execute_with_debug(
        self,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with full debugging"""
        trace_id = self.logger.start_trace(operation, {"args": str(args), "kwargs": str(kwargs)})
        self.logger.info(f"Starting: {operation}", {"trace_id": trace_id})

        try:
            # Check breakpoints
            context = {"args": args, "kwargs": kwargs}
            if self.debugger.check_breakpoint(context):
                self.logger.warning("Breakpoint hit!", {"trace_id": trace_id})
                # In a real debugger, we'd pause here

            # Execute
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            self.logger.end_trace("completed", {"result": str(result)[:100]})
            self.logger.info(f"Completed: {operation}", {"trace_id": trace_id})

            # Reflect
            await self.reflector.reflect(
                trigger=operation,
                observation=f"Successfully completed {operation}",
                level=ReflectionLevel.BASIC
            )

            return result

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.logger.error(f"Failed: {operation}", {"error": error_msg, "trace": traceback.format_exc()})
            self.logger.end_trace("failed", error=error_msg)

            # Deep reflection on error
            await self.reflector.reflect(
                trigger=operation,
                observation=f"Error: {error_msg}",
                level=ReflectionLevel.DEEP
            )

            raise

    def get_debug_info(self) -> Dict[str, Any]:
        """Get all debug information"""
        return {
            "agent": self.agent_name,
            "logger_stats": self.logger.get_stats(),
            "recent_reflections": len(self.reflector.reflections),
            "watch_vars": self.debugger.get_watch_vars(),
            "step_count": self.debugger.step_count
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Reflection and Debugging Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        debugger = AgentDebugger("TestAgent")

        # Test logging
        print("\n[1] Logging")
        print("-" * 40)

        debugger.logger.info("Agent started")
        debugger.logger.debug("Debug message")
        debugger.logger.warning("Warning message")
        debugger.logger.error("Error message")

        stats = debugger.logger.get_stats()
        print(f"  Total logs: {stats['total_logs']}")
        print(f"  By level: {stats['by_level']}")

        # Test tracing
        print("\n[2] Execution Tracing")
        print("-" * 40)

        trace_id = debugger.logger.start_trace("test_operation", {"param": "value"})
        await asyncio.sleep(0.1)
        debugger.logger.end_trace("completed", {"result": "success"})

        trace = debugger.logger.get_trace(trace_id)
        print(f"  Trace: {trace.operation}")
        print(f"  Status: {trace.status}")

        # Test reflection
        print("\n[3] Reflection")
        print("-" * 40)

        await debugger.reflector.reflect(
            "task_completion",
            "Task completed successfully",
            ReflectionLevel.BASIC
        )

        await debugger.reflector.reflect(
            "error",
            "Error in data processing: null pointer",
            ReflectionLevel.DEEP
        )

        await debugger.reflector.reflect(
            "performance",
            "Operation took too long",
            ReflectionLevel.META
        )

        insights = debugger.reflector.get_insights()
        print(f"  Reflections: {len(debugger.reflector.reflections)}")
        print(f"  Insight triggers: {list(insights.keys())}")

        # Test debugging
        print("\n[4) Debugging")
        print("-" * 40)

        debugger.debugger.watch("counter", 0)
        debugger.debugger.watch("state", "initial")

        debugger.debugger.update_watch("counter", 1)
        debugger.debugger.update_watch("state", "running")

        debugger.debugger.set_breakpoint("error")

        watch_info = debugger.debugger.get_watch_vars()
        print(f"  Watch variables: {len(watch_info)}")
        print(f"  Breakpoints: {len(debugger.debugger.breakpoints)}")

        # Debug info
        print("\n[5] Debug Info")
        print("-" * 40)

        info = debugger.get_debug_info()
        print(f"  Agent: {info['agent']}")
        print(f"  Logger stats: {info['logger_stats']['total_logs']} logs")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()