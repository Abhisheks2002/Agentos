"""
Day 71: Workflow Engine
========================
Building a workflow engine for orchestrating complex agent tasks.

Key Concepts:
- Workflow definitions
- Task dependencies
- Parallel execution
- State management
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Workflow status"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowTask:
    """A task within a workflow"""
    task_id: str
    name: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    started_at: datetime = None
    completed_at: datetime = None


@dataclass
class Workflow:
    """A workflow definition"""
    workflow_id: str
    name: str
    description: str
    tasks: Dict[str, WorkflowTask] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None


class WorkflowEngine:
    """
    Workflow Engine
    ===============

    Executes workflows with dependency resolution and parallel execution.
    """

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.handlers: Dict[str, Callable] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def register_handler(self, action: str, handler: Callable):
        """Register a task handler"""
        self.handlers[action] = handler

    def create_workflow(
        self,
        name: str,
        description: str = "",
        tasks: List[Dict[str, Any]] = None
    ) -> Workflow:
        """Create a new workflow"""
        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description
        )

        # Add tasks
        if tasks:
            for task_data in tasks:
                task = WorkflowTask(
                    task_id=task_data.get("id", str(uuid.uuid4())),
                    name=task_data.get("name", ""),
                    action=task_data.get("action", ""),
                    params=task_data.get("params", {}),
                    depends_on=task_data.get("depends_on", [])
                )
                workflow.tasks[task.task_id] = task

        self.workflows[workflow.workflow_id] = workflow
        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}

        context = context or {}
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()

        try:
            # Build dependency graph
            ready_tasks = []
            completed = set()
            failed = set()

            # Find tasks with no dependencies
            for task_id, task in workflow.tasks.items():
                if not task.depends_on:
                    ready_tasks.append(task_id)

            while ready_tasks:
                # Execute tasks in parallel (all that are ready)
                tasks_to_run = ready_tasks.copy()
                ready_tasks.clear()

                # Run tasks concurrently
                results = await asyncio.gather(
                    *[self._execute_task(workflow, tid, context) for tid in tasks_to_run],
                    return_exceptions=True
                )

                # Process results
                for task_id, result in zip(tasks_to_run, results):
                    if isinstance(result, Exception):
                        failed.add(task_id)
                    else:
                        completed.add(task_id)
                        # Update context with result
                        context[task_id] = result

                        # Find newly ready tasks
                        for tid, task in workflow.tasks.items():
                            if tid not in completed and tid not in failed:
                                deps_met = all(d in completed for d in task.depends_on)
                                if deps_met:
                                    ready_tasks.append(tid)

                # Check for failures
                if failed:
                    workflow.status = WorkflowStatus.FAILED
                    break

            # Check if all completed
            if len(completed) == len(workflow.tasks):
                workflow.status = WorkflowStatus.COMPLETED

            workflow.completed_at = datetime.now()

            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "results": context
            }

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            return {"error": str(e)}

    async def _execute_task(
        self,
        workflow: Workflow,
        task_id: str,
        context: Dict[str, Any]
    ) -> Any:
        """Execute a single task"""
        task = workflow.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            # Get handler
            handler = self.handlers.get(task.action)
            if not handler:
                raise ValueError(f"No handler for action: {task.action}")

            # Prepare params (resolve from context)
            params = self._resolve_params(task.params, context)

            # Execute
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params, context)
            else:
                result = handler(params, context)

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            raise

    def _resolve_params(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve parameter references from context"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to another task's result
                ref_id = value[1:]
                resolved[key] = context.get(ref_id)
            else:
                resolved[key] = value
        return resolved

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "tasks": [
                {
                    "id": t.task_id,
                    "name": t.name,
                    "status": t.status.value,
                    "result": t.result,
                    "error": t.error
                }
                for t in workflow.tasks.values()
            ]
        }

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel running workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return False

        workflow.status = WorkflowStatus.CANCELLED

        # Cancel running tasks
        for task_id, task in self._running_tasks.items():
            if not task.done():
                task.cancel()

        return True


# Demo
async def main():
    print("=" * 60)
    print("Day 71: Workflow Engine")
    print("=" * 60)

    engine = WorkflowEngine()

    # Register handlers
    def fetch_data(params, context):
        print(f"  Fetching data: {params.get('source')}")
        return {"rows": 1000, "columns": 10}

    def transform_data(params, context):
        input_data = context.get(params.get("input_task"))
        print(f"  Transforming {input_data.get('rows')} rows")
        return {"processed": True, "rows": 800}

    def analyze_data(params, context):
        input_data = context.get(params.get("input_task"))
        print(f"  Analyzing {input_data.get('rows')} rows")
        return {"insights": ["pattern1", "pattern2"]}

    def generate_report(params, context):
        analysis = context.get(params.get("analysis_task"))
        print(f"  Generating report with {len(analysis.get('insights', []))} insights")
        return {"report_path": "/reports/analysis.pdf"}

    engine.register_handler("fetch", fetch_data)
    engine.register_handler("transform", transform_data)
    engine.register_handler("analyze", analyze_data)
    engine.register_handler("report", generate_report)

    # Create workflow
    workflow = engine.create_workflow(
        name="Data Analysis Pipeline",
        description="Complete data analysis workflow",
        tasks=[
            {
                "id": "fetch",
                "name": "Fetch Data",
                "action": "fetch",
                "params": {"source": "database"},
                "depends_on": []
            },
            {
                "id": "transform",
                "name": "Transform Data",
                "action": "transform",
                "params": {"input_task": "fetch"},
                "depends_on": ["fetch"]
            },
            {
                "id": "analyze",
                "name": "Analyze Data",
                "action": "analyze",
                "params": {"input_task": "transform"},
                "depends_on": ["transform"]
            },
            {
                "id": "report",
                "name": "Generate Report",
                "action": "report",
                "params": {"analysis_task": "analyze"},
                "depends_on": ["analyze"]
            }
        ]
    )

    print(f"\nCreated workflow: {workflow.name}")
    print(f"Tasks: {len(workflow.tasks)}")

    # Execute workflow
    print("\nExecuting workflow...")
    result = await engine.execute_workflow(workflow.workflow_id)
    print(f"\nWorkflow status: {result['status']}")

    # Get detailed status
    status = engine.get_workflow_status(workflow.workflow_id)
    print("\nTask statuses:")
    for task in status["tasks"]:
        print(f"  - {task['name']}: {task['status']}")


if __name__ == "__main__":
    asyncio.run(main())