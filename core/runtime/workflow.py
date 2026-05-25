"""Workflow Engine - Orchestrates multi-step agent workflows."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from ..models.models import Workflow
from ..runtime.runtime import get_runtime

logger = logging.getLogger(__name__)


class WorkflowStep:
    """A single step in a workflow."""

    def __init__(
        self,
        name: str,
        agent_id: str = None,
        tool_name: str = None,
        params: Dict = None,
        next_step: str = None
    ):
        self.name = name
        self.agent_id = agent_id
        self.tool_name = tool_name
        self.params = params or {}
        self.next_step = next_step


class WorkflowEngine:
    """
    Workflow engine for orchestrating multi-step processes.
    """

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.runtime = get_runtime()
        self.tools = None  # Will be set when needed

    def set_tools(self, tools):
        """Set the tool registry."""
        self.tools = tools

    async def create_workflow(
        self,
        name: str,
        description: str = None,
        steps: List[Dict] = None
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            id=f"wf_{uuid.uuid4().hex[:12]}",
            name=name,
            description=description,
            steps=steps or [],
            status="draft"
        )
        self.workflows[workflow.id] = workflow
        logger.info(f"Created workflow: {workflow.id}")
        return workflow

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self.workflows.get(workflow_id)

    async def execute_workflow(
        self,
        workflow_id: str,
        initial_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}

        workflow.status = "running"
        context = initial_input or {}
        results = []

        for i, step_def in enumerate(workflow.steps):
            step = WorkflowStep(**step_def)

            try:
                if step.agent_id:
                    # Execute with agent
                    task = await self.runtime.create_task(
                        agent_id=step.agent_id,
                        input_data={**step.params, **context}
                    )
                    result = await self.runtime.execute_task(task.id)
                    step_result = {
                        "step": step.name,
                        "success": result.success,
                        "output": result.data,
                        "error": result.error
                    }
                elif step.tool_name and self.tools:
                    # Execute with tool
                    tool_result = await self.tools.execute(
                        tool_name=step.tool_name,
                        parameters=step.params,
                        context=context
                    )
                    step_result = {
                        "step": step.name,
                        "success": tool_result.get("success", False),
                        "output": tool_result.get("result"),
                        "error": tool_result.get("error")
                    }
                else:
                    step_result = {
                        "step": step.name,
                        "error": "No agent or tool specified"
                    }

                results.append(step_result)

                # Update context with results
                if step_result.get("output"):
                    context[step.name] = step_result["output"]

                # Check if step failed and workflow should stop
                if not step_result.get("success"):
                    if not workflow.config.get("continue_on_error"):
                        break

            except Exception as e:
                logger.error(f"Step {step.name} failed: {e}")
                results.append({
                    "step": step.name,
                    "error": str(e)
                })
                if not workflow.config.get("continue_on_error"):
                    break

        workflow.status = "completed"
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "status": workflow.status,
            "results": results,
            "context": context
        }

    async def list_workflows(self) -> List[Workflow]:
        """List all workflows."""
        return list(self.workflows.values())

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False


# Global workflow engine
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine."""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
