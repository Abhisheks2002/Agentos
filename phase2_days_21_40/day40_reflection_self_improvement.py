"""
Day 40: Reflection & Self-Improvement
=====================================
Skill: Self-Analysis
Mini Project: Agent Reflection System

Building agents that can reflect and improve themselves.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid
from collections import defaultdict


class ReflectionType(str, Enum):
    """Types of reflection"""
    TASK_REVIEW = "task_review"
    STRATEGY_ANALYSIS = "strategy_analysis"
    ERROR_ANALYSIS = "error_analysis"
    PERFORMANCE_REVIEW = "performance_review"
    GOAL_ASSESSMENT = "goal_assessment"


class ImprovementAction(str, Enum):
    """Types of improvement actions"""
    ADJUST_STRATEGY = "adjust_strategy"
    LEARN_NEW_SKILL = "learn_new_skill"
    MODIFY_BEHAVIOR = "modify_behavior"
    UPDATE_GOALS = "update_goals"
    SEEK_HELP = "seek_help"


@dataclass
class Reflection:
    """A reflection entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reflection_type: ReflectionType = ReflectionType.TASK_REVIEW
    content: str = ""
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    related_task_id: Optional[str] = None
    success_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_duration: float = 0.0
    total_duration: float = 0.0
    retry_count: int = 0
    error_count: int = 0

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.get_success_rate(),
            "average_duration": self.average_duration,
            "retry_count": self.retry_count,
            "error_count": self.error_count
        }


class ReflectionEngine:
    """Engine for generating reflections"""

    def __init__(self):
        self.reflections: List[Reflection] = []

    def reflect_on_task(
        self,
        task_name: str,
        result: Any,
        error: Optional[str] = None,
        context: Dict = None
    ) -> Reflection:
        """Reflect on a completed task"""
        insights = []
        recommendations = []
        success_score = 1.0 if not error else 0.0

        # Analyze result
        if error:
            insights.append(f"Task failed with error: {error}")
            recommendations.append("Review error handling logic")
            recommendations.append("Consider adding retry mechanism")
            success_score = 0.0
        else:
            insights.append(f"Task completed successfully")
            if isinstance(result, dict) and result.get("quality"):
                insights.append(f"Quality score: {result.get('quality')}")

        reflection = Reflection(
            reflection_type=ReflectionType.TASK_REVIEW,
            content=f"Task '{task_name}' completed. Result: {result}",
            insights=insights,
            recommendations=recommendations,
            success_score=success_score,
            metadata=context or {}
        )

        self.reflections.append(reflection)
        return reflection

    def analyze_errors(self, errors: List[Dict]) -> Reflection:
        """Analyze errors and generate insights"""
        if not errors:
            return None

        error_types = defaultdict(int)
        for error in errors:
            error_types[error.get("type", "unknown")] += 1

        insights = []
        recommendations = []

        for error_type, count in error_types.items():
            insights.append(f"Error type '{error_type}' occurred {count} times")

        # Generate recommendations based on error patterns
        if error_types.get("timeout", 0) > 0:
            recommendations.append("Consider increasing timeout values")
            recommendations.append("Implement async retry logic")

        if error_types.get("permission", 0) > 0:
            recommendations.append("Review permission requirements")
            recommendations.append("Add permission checks before operations")

        if error_types.get("validation", 0) > 0:
            recommendations.append("Improve input validation")
            recommendations.append("Add detailed error messages")

        reflection = Reflection(
            reflection_type=ReflectionType.ERROR_ANALYSIS,
            content=f"Analysis of {len(errors)} errors",
            insights=insights,
            recommendations=recommendations,
            success_score=0.5
        )

        self.reflections.append(reflection)
        return reflection

    def review_performance(self, metrics: PerformanceMetrics) -> Reflection:
        """Review overall performance"""
        insights = []
        recommendations = []

        success_rate = metrics.get_success_rate()

        insights.append(f"Success rate: {success_rate:.1%}")
        insights.append(f"Total tasks: {metrics.total_tasks}")

        if success_rate >= 0.9:
            recommendations.append("Performance is excellent")
        elif success_rate >= 0.7:
            recommendations.append("Performance is good, minor improvements possible")
        else:
            recommendations.append("Performance needs improvement")
            recommendations.append("Review failed tasks for patterns")

        if metrics.retry_count > metrics.total_tasks * 0.2:
            recommendations.append("High retry rate - consider improving initial success")

        reflection = Reflection(
            reflection_type=ReflectionType.PERFORMANCE_REVIEW,
            content=f"Performance review: {success_rate:.1%} success rate",
            insights=insights,
            recommendations=recommendations,
            success_score=success_rate,
            metadata=metrics.to_dict()
        )

        self.reflections.append(reflection)
        return reflection

    def get_recent_reflections(self, count: int = 10) -> List[Reflection]:
        """Get recent reflections"""
        return self.reflections[-count:]

    def get_reflections_by_type(self, ref_type: ReflectionType) -> List[Reflection]:
        """Get reflections by type"""
        return [r for r in self.reflections if r.reflection_type == ref_type]


class SelfImprovementEngine:
    """Engine for self-improvement actions"""

    def __init__(self):
        self.improvements: List[Dict] = []
        self.skills: Dict[str, Callable] = {}
        self.strategies: Dict[str, Callable] = {}

    def register_skill(self, name: str, function: Callable):
        """Register a skill"""
        self.skills[name] = function

    def register_strategy(self, name: str, function: Callable):
        """Register a strategy"""
        self.strategies[name] = function

    def analyze_improvements(
        self,
        reflections: List[Reflection]
    ) -> List[Dict]:
        """Analyze reflections and determine improvements"""
        improvements = []

        # Count recommendations
        recommendation_counts = defaultdict(int)
        for ref in reflections:
            for rec in ref.recommendations:
                recommendation_counts[rec] += 1

        # Generate improvement actions
        for rec, count in recommendation_counts.items():
            if count >= 2:  # Repeated recommendation
                if "retry" in rec.lower():
                    improvements.append({
                        "type": ImprovementAction.ADJUST_STRATEGY,
                        "description": "Implement retry mechanism",
                        "priority": count
                    })

                if "timeout" in rec.lower():
                    improvements.append({
                        "type": ImprovementAction.ADJUST_STRATEGY,
                        "description": "Increase timeout values",
                        "priority": count
                    })

                if "permission" in rec.lower():
                    improvements.append({
                        "type": ImprovementAction.MODIFY_BEHAVIOR,
                        "description": "Add permission checks",
                        "priority": count
                    })

                if "validation" in rec.lower():
                    improvements.append({
                        "type": ImprovementAction.MODIFY_BEHAVIOR,
                        "description": "Improve input validation",
                        "priority": count
                    })

        # Apply improvements
        for improvement in improvements:
            self.improvements.append(improvement)

        return improvements

    def apply_improvement(self, improvement: Dict):
        """Apply an improvement"""
        improvement["applied_at"] = datetime.now().isoformat()
        self.improvements.append(improvement)

    def get_improvements(self) -> List[Dict]:
        """Get all improvements"""
        return self.improvements


class ReflectiveAgent:
    """An agent with reflection capabilities"""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.reflection_engine = ReflectionEngine()
        self.improvement_engine = SelfImprovementEngine()
        self.metrics = PerformanceMetrics()
        self.task_history: List[Dict] = []

    async def execute_task(self, task_name: str, task_fn: Callable, context: Dict = None) -> Any:
        """Execute a task with reflection"""
        start_time = datetime.now()

        try:
            # Execute task
            if context:
                result = await task_fn(context) if asyncio.iscoroutinefunction(task_fn) else task_fn(context)
            else:
                result = await task_fn() if asyncio.iscoroutinefunction(task_fn) else task_fn()

            # Update metrics
            self.metrics.successful_tasks += 1

            # Reflect on success
            self.reflection_engine.reflect_on_task(task_name, result, context=context)

            return result

        except Exception as e:
            # Update metrics
            self.metrics.failed_tasks += 1
            self.metrics.error_count += 1

            # Reflect on failure
            self.reflection_engine.reflect_on_task(task_name, None, str(e), context=context)

            raise

        finally:
            # Update duration metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics.total_tasks += 1
            self.metrics.total_duration += duration
            self.metrics.average_duration = self.metrics.total_duration / self.metrics.total_tasks

            # Store in history
            self.task_history.append({
                "task_name": task_name,
                "timestamp": datetime.now().isoformat(),
                "duration": duration
            })

    def reflect(self):
        """Perform reflection"""
        # Review performance
        self.reflection_engine.review_performance(self.metrics)

        # Analyze improvements
        reflections = self.reflection_engine.get_recent_reflections()
        improvements = self.improvement_engine.analyze_improvements(reflections)

        return improvements

    def get_reflection_summary(self) -> Dict:
        """Get summary of reflections"""
        recent = self.reflection_engine.get_recent_reflections(5)
        return {
            "total_reflections": len(self.reflection_engine.reflections),
            "recent_reflections": [
                {
                    "type": r.reflection_type.value,
                    "insights": r.insights[:2],
                    "score": r.success_score
                }
                for r in recent
            ],
            "performance": self.metrics.to_dict()
        }


# Helper for async
import asyncio


class SelfImprovingAgent(ReflectiveAgent):
    """An agent that can self-improve"""

    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name)
        self.learned_strategies: Dict[str, Any] = {}
        self.learned_skills: List[str] = []

    def learn_from_reflection(self, reflection: Reflection):
        """Learn from a reflection"""
        for rec in reflection.recommendations:
            if "retry" in rec.lower():
                self.learned_strategies["retry"] = {"max_retries": 3, "backoff": True}

            if "timeout" in rec.lower():
                self.learned_strategies["timeout"] = {"default_timeout": 60}

            if "validation" in rec.lower():
                self.learned_strategies["validation"] = {"strict": True}

            if "cache" in rec.lower():
                self.learned_strategies["caching"] = {"enabled": True}

    def apply_learned_improvements(self):
        """Apply all learned improvements"""
        improvements = self.improvement_engine.get_improvements()

        for imp in improvements:
            if imp.get("applied_at"):
                continue

            # Apply the improvement
            self.improvement_engine.apply_improvement(imp)

            # Learn from it
            for ref in self.reflection_engine.get_recent_reflections():
                self.learn_from_reflection(ref)


# Demo
def run_demo():
    print("=" * 70)
    print("Reflection & Self-Improvement Demo")
    print("=" * 70)

    # Test Reflection Engine
    print("\n[1] Reflection Engine")
    print("-" * 40)

    engine = ReflectionEngine()

    # Reflect on successful task
    ref1 = engine.reflect_on_task("fetch_data", {"rows": 100})
    print(f"  Success reflection: {ref1.success_score}")

    # Reflect on failed task
    ref2 = engine.reflect_on_task("process_data", None, "Timeout error")
    print(f"  Failure reflection: {ref2.success_score}")

    # Error analysis
    errors = [
        {"type": "timeout", "message": "Request timeout"},
        {"type": "timeout", "message": "DB timeout"},
        {"type": "validation", "message": "Invalid input"}
    ]
    error_ref = engine.analyze_errors(errors)
    print(f"  Error insights: {len(error_ref.insights)}")

    # Performance review
    metrics = PerformanceMetrics(
        total_tasks=100,
        successful_tasks=85,
        failed_tasks=15,
        retry_count=20
    )
    perf_ref = engine.review_performance(metrics)
    print(f"  Performance: {perf_ref.insights[0]}")

    # Test Reflective Agent
    print("\n[2] Reflective Agent")
    print("-" * 40)

    agent = ReflectiveAgent("agent-1", "Reflective Bot")

    async def sample_task(ctx):
        await asyncio.sleep(0.1)
        return {"result": "success"}

    # Execute tasks
    import asyncio
    asyncio.run(agent.execute_task("task1", sample_task))
    asyncio.run(agent.execute_task("task2", sample_task))

    # Reflect
    agent.metrics.total_tasks = 10
    agent.metrics.successful_tasks = 8
    agent.metrics.failed_tasks = 2

    improvements = agent.reflect()
    print(f"  Improvements found: {len(improvements)}")

    # Summary
    print("\n[3] Reflection Summary")
    print("-" * 40)

    summary = agent.get_reflection_summary()
    print(f"  Total reflections: {summary['total_reflections']}")
    print(f"  Performance: {summary['performance']['success_rate']:.0%}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()