"""
AgentOS - Agent Runtime
Agent lifecycle, task execution, tool registry, and session management
"""

import uuid
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Tuple, Tuple
from enum import Enum
from collections import defaultdict
import threading


class AgentState(Enum):
    """Agent lifecycle states"""
    CREATED = "created"
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"  # Waiting for tool execution


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class ToolDefinition:
    """Tool definition"""

    def __init__(self, name: str, description: str, parameters: Dict,
                 handler: Callable = None):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.usage_count = 0
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "usage_count": self.usage_count,
            "created_at": self.created_at
        }


class Task:
    """Task representation"""

    def __init__(self, task_type: str, payload: Dict,
                 priority: TaskPriority = TaskPriority.NORMAL):
        self.id = f"task_{uuid.uuid4().hex[:8]}"
        self.type = task_type
        self.payload = payload
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.agent_id = None
        self.tools_used = []
        self.metadata = {}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "agent_id": self.agent_id,
            "tools_used": self.tools_used,
            "metadata": self.metadata
        }


class ToolRegistry:
    """Registry for available tools"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories = defaultdict(list)
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register built-in tools"""
        # These will be connected to OS Bridge
        self.register("file_read", "Read file contents", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"]
        })

        self.register("file_write", "Write content to file", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        })

        self.register("list_directory", "List directory contents", {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path"}
            }
        })

        self.register("execute_command", "Execute shell command", {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "timeout": {"type": "number", "description": "Timeout in seconds"}
            },
            "required": ["command"]
        })

        self.register("web_request", "Make HTTP request", {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to request"},
                "method": {"type": "string", "description": "HTTP method"},
                "data": {"type": "object", "description": "Request body"}
            },
            "required": ["url"]
        })

        self.register("search_memory", "Search agent memory", {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "type": {"type": "string", "description": "Memory type: semantic, episodic"}
            },
            "required": ["query"]
        })

        self.register("store_knowledge", "Store knowledge in memory", {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "Fact to store"},
                "concepts": {"type": "array", "description": "Related concepts"}
            },
            "required": ["fact"]
        })

        # Day 8: Web Search Tool
        self.register("web_search", "Search the web for information", {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "limit": {"type": "integer", "description": "Maximum results to return", "default": 10}
            },
            "required": ["query"]
        }, category="information")

    def register(self, name: str, description: str, parameters: Dict,
                 handler: Callable = None, category: str = "general"):
        """Register a new tool"""
        tool = ToolDefinition(name, description, parameters, handler)
        self.tools[name] = tool
        self.categories[category].append(name)

    def unregister(self, name: str) -> bool:
        """Unregister a tool"""
        if name in self.tools:
            tool = self.tools[name]
            del self.tools[name]
            for cat in self.categories:
                if name in self.categories[cat]:
                    self.categories[cat].remove(name)
            return True
        return False

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self, category: str = None) -> List[Dict]:
        """List available tools"""
        if category:
            tool_names = self.categories.get(category, [])
            return [self.tools[name].to_dict() for name in tool_names
                   if name in self.tools]

        return [tool.to_dict() for tool in self.tools.values()]

    def validate_parameters(self, tool_name: str, params: Dict) -> Tuple[bool, str]:
        """Validate tool parameters"""
        tool = self.tools.get(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found"

        # Check required parameters
        required = tool.parameters.get("required", [])
        for req in required:
            if req not in params:
                return False, f"Missing required parameter: {req}"

        return True, "OK"


class TaskQueue:
    """Priority queue for tasks"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.tasks: List[Task] = []
        self.lock = threading.Lock()

    def add(self, task: Task) -> bool:
        """Add task to queue"""
        with self.lock:
            if len(self.tasks) >= self.max_size:
                return False

            self.tasks.append(task)
            # Sort by priority (highest first)
            self.tasks.sort(key=lambda t: t.priority.value, reverse=True)
            return True

    def get_next(self) -> Optional[Task]:
        """Get next task to execute"""
        with self.lock:
            for task in self.tasks:
                if task.status == TaskStatus.PENDING:
                    return task
            return None

    def get(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self.lock:
            for task in self.tasks:
                if task.id == task_id:
                    return task
            return None

    def cancel(self, task_id: str) -> bool:
        """Cancel a task"""
        with self.lock:
            for task in self.tasks:
                if task.id == task_id:
                    if task.status in [TaskStatus.PENDING, TaskStatus.WAITING]:
                        task.status = TaskStatus.CANCELLED
                        return True
            return False

    def get_pending_count(self) -> int:
        """Get pending task count"""
        with self.lock:
            return sum(1 for t in self.tasks
                      if t.status == TaskStatus.PENDING)

    def clear_completed(self, before_hours: int = 24):
        """Clear completed tasks"""
        with self.lock:
            cutoff = datetime.now().timestamp() - (before_hours * 3600)
            self.tasks = [
                t for t in self.tasks
                if t.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED,
                                    TaskStatus.CANCELLED]
                or (t.completed_at and t.completed_at.timestamp() > cutoff)
            ]


class AgentRuntime:
    """
    Agent Runtime
    Manages agent lifecycle, task execution, and tool usage
    """

    def __init__(self, memory_manager=None, os_bridge=None):
        self.agents: Dict[str, Dict] = {}
        self.task_queue = TaskQueue()
        self.tool_registry = ToolRegistry()
        self.memory_manager = memory_manager
        self.os_bridge = os_bridge
        self.event_handlers = defaultdict(list)
        self.running = False
        self._executor_thread = None

        # Agent configurations
        self.default_config = {
            "max_concurrent_tasks": 3,
            "task_timeout": 300,  # 5 minutes
            "tool_timeout": 30,
            "max_retries": 2,
            "auto_start_session": True
        }

    # ============== Agent Management ==============

    def create_agent(self, name: str, agent_type: str,
                     config: Dict = None, permissions: List[str] = None) -> str:
        """Create new agent"""
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        agent_config = {**self.default_config}
        if config:
            agent_config.update(config)

        agent = {
            "id": agent_id,
            "name": name,
            "type": agent_type,
            "config": agent_config,
            "permissions": permissions or ["file_read", "network_access"],
            "state": AgentState.CREATED,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tools_used": defaultdict(int),
            "current_task": None,
            "metadata": {}
        }

        self.agents[agent_id] = agent
        self._emit("agent_created", agent)

        return agent_id

    def start_agent(self, agent_id: str) -> bool:
        """Start an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        if agent["state"] not in [AgentState.CREATED, AgentState.IDLE,
                                   AgentState.STOPPED]:
            return False

        agent["state"] = AgentState.INITIALIZING
        self._emit("agent_starting", agent)

        # Initialize session if configured
        if agent["config"].get("auto_start_session") and self.memory_manager:
            session_id = self.memory_manager.start_session(agent_id, {
                "agent_name": agent["name"],
                "agent_type": agent["type"]
            })
            agent["metadata"]["session_id"] = session_id

        agent["state"] = AgentState.IDLE
        agent["started_at"] = datetime.now().isoformat()
        self._emit("agent_started", agent)

        return True

    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        if agent["state"] in [AgentState.STOPPING, AgentState.STOPPED]:
            return False

        agent["state"] = AgentState.STOPPING
        self._emit("agent_stopping", agent)

        # End session if exists
        if self.memory_manager:
            self.memory_manager.end_session(agent_id)

        agent["state"] = AgentState.STOPPED
        self._emit("agent_stopped", agent)

        return True

    def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent"""
        agent = self.agents.get(agent_id)
        if not agent or agent["state"] != AgentState.IDLE:
            return False

        agent["state"] = AgentState.PAUSED
        self._emit("agent_paused", agent)
        return True

    def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent"""
        agent = self.agents.get(agent_id)
        if not agent or agent["state"] != AgentState.PAUSED:
            return False

        agent["state"] = AgentState.IDLE
        self._emit("agent_resumed", agent)
        return True

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent info"""
        return self.agents.get(agent_id)

    def list_agents(self, state: AgentState = None) -> List[Dict]:
        """List all agents"""
        agents = []
        for agent in self.agents.values():
            if state is None or agent["state"] == state:
                agents.append({
                    "id": agent["id"],
                    "name": agent["name"],
                    "type": agent["type"],
                    "state": agent["state"].value,
                    "created_at": agent["created_at"],
                    "tasks_completed": agent["tasks_completed"]
                })
        return agents

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        if agent["state"] == AgentState.RUNNING:
            return False

        del self.agents[agent_id]
        self._emit("agent_deleted", {"id": agent_id})
        return True

    # ============== Task Management ==============

    def submit_task(self, agent_id: str, task_type: str, payload: Dict,
                   priority: TaskPriority = TaskPriority.NORMAL) -> Optional[str]:
        """Submit task to agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        if agent["state"] not in [AgentState.IDLE, AgentState.RUNNING]:
            return None

        task = Task(task_type, payload, priority)
        task.agent_id = agent_id

        if self.task_queue.add(task):
            self._emit("task_submitted", task.to_dict())
            return task.id

        return None

    def _execute_task(self, task: Task) -> Dict:
        """Execute a task"""
        agent = self.agents.get(task.agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        # Update agent state
        agent["state"] = AgentState.RUNNING
        agent["current_task"] = task.id
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        # Update memory
        if self.memory_manager:
            self.memory_manager.add_interaction(
                task.agent_id, "task_start",
                f"Starting task: {task.type}",
                {"task_id": task.id}
            )

        try:
            # Route based on task type
            if task.type == "execute":
                result = self._handle_execute_task(task, agent)
            elif task.type == "tool":
                result = self._handle_tool_task(task, agent)
            elif task.type == "workflow":
                result = self._handle_workflow_task(task, agent)
            else:
                result = {"success": False, "error": f"Unknown task type: {task.type}"}

            # Update task status
            if result.get("success", False):
                task.status = TaskStatus.COMPLETED
                task.result = result
                agent["tasks_completed"] += 1
            else:
                task.status = TaskStatus.FAILED
                task.error = result.get("error", "Unknown error")
                agent["tasks_failed"] += 1

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            agent["tasks_failed"] += 1

        finally:
            task.completed_at = datetime.now()
            agent["current_task"] = None
            agent["state"] = AgentState.IDLE

            # Update memory
            if self.memory_manager:
                self.memory_manager.add_interaction(
                    task.agent_id, "task_complete",
                    f"Task {task.id} {task.status.value}",
                    {"task_id": task.id, "status": task.status.value}
                )

        return task.to_dict()

    def _handle_execute_task(self, task: Task, agent: Dict) -> Dict:
        """Handle execution task"""
        command = task.payload.get("command")
        if not command:
            return {"success": False, "error": "No command provided"}

        # Check permission
        if "execute_commands" not in agent["permissions"]:
            return {"success": False, "error": "Permission denied: execute_commands"}

        # Use OS Bridge if available
        if self.os_bridge:
            return self.os_bridge.execute_command(
                command,
                timeout=task.payload.get("timeout", agent["config"]["tool_timeout"])
            )

        return {"success": False, "error": "OS Bridge not available"}

    def _handle_tool_task(self, task: Task, agent: Dict) -> Dict:
        """Handle tool execution task"""
        tool_name = task.payload.get("tool")
        params = task.payload.get("params", {})

        # Get tool
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}

        # Validate parameters
        valid, error = self.tool_registry.validate_parameters(tool_name, params)
        if not valid:
            return {"success": False, "error": error}

        # Check permission
        if tool_name not in agent["permissions"]:
            return {"success": False, "error": f"Permission denied: {tool_name}"}

        # Track tool usage
        agent["tools_used"][tool_name] += 1
        task.tools_used.append(tool_name)

        # Execute tool
        if tool.handler:
            try:
                result = tool.handler(params)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Built-in tool execution via OS Bridge
        if self.os_bridge:
            return self._execute_builtin_tool(tool_name, params, agent)

        return {"success": False, "error": "Cannot execute tool"}

    def _execute_builtin_tool(self, tool_name: str, params: Dict,
                              agent: Dict) -> Dict:
        """Execute built-in tool via OS Bridge"""
        # Map tools to OS Bridge methods
        tool_map = {
            "file_read": lambda: self.os_bridge.read_file(params["path"]),
            "file_write": lambda: self.os_bridge.write_file(
                params["path"], params.get("content", "")),
            "list_directory": lambda: self.os_bridge.list_directory(
                params.get("path")),
            "execute_command": lambda: self.os_bridge.execute_command(
                params["command"], timeout=params.get("timeout", 30)),
            "web_request": lambda: self.os_bridge.make_request(
                params["url"],
                method=params.get("method", "GET"),
                data=params.get("data"),
                headers=params.get("headers"),
                timeout=params.get("timeout", 30)
            ),
            "search_memory": lambda: self._search_memory(
                params["query"], params.get("type", "semantic")),
            "store_knowledge": lambda: self._store_knowledge(
                params["fact"], params.get("concepts", []))
        }

        handler = tool_map.get(tool_name)
        if handler:
            try:
                return handler()
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Tool not implemented: {tool_name}"}

    def _search_memory(self, query: str, mem_type: str) -> Dict:
        """Search memory"""
        if not self.memory_manager:
            return {"success": False, "error": "Memory manager not available"}

        if mem_type == "semantic":
            results = self.memory_manager.recall_knowledge(query)
        elif mem_type == "episodic":
            results = self.memory_manager.episodic.search_episodes(query)
        else:
            return {"success": False, "error": f"Unknown memory type: {mem_type}"}

        return {"success": True, "results": results}

    def _store_knowledge(self, fact: str, concepts: List[str]) -> Dict:
        """Store knowledge in memory"""
        if not self.memory_manager:
            return {"success": False, "error": "Memory manager not available"}

        fact_id = self.memory_manager.store_knowledge(fact, concepts)
        return {"success": True, "fact_id": fact_id}

    def _handle_workflow_task(self, task: Task, agent: Dict) -> Dict:
        """Handle workflow task"""
        # Placeholder for workflow execution
        return {"success": False, "error": "Workflow execution not implemented"}

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
        task = self.task_queue.get(task_id)
        return task.to_dict() if task else None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        return self.task_queue.cancel(task_id)

    # ============== Event Handling ==============

    def on(self, event: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event].append(handler)

    def _emit(self, event: str, data: Any):
        """Emit event to handlers"""
        for handler in self.event_handlers.get(event, []):
            try:
                handler(data)
            except Exception as e:
                print(f"Event handler error: {e}")

    # ============== Statistics ==============

    def get_stats(self) -> Dict:
        """Get runtime statistics"""
        state_counts = defaultdict(int)
        for agent in self.agents.values():
            state_counts[agent["state"].value] += 1

        return {
            "agents": {
                "total": len(self.agents),
                "by_state": dict(state_counts)
            },
            "tasks": {
                "pending": self.task_queue.get_pending_count(),
                "total_queued": len(self.task_queue.tasks)
            },
            "tools": {
                "registered": len(self.tool_registry.tools),
                "by_category": {k: len(v) for k, v in self.tool_registry.categories.items()}
            }
        }

    # ============== Lifecycle ==============

    def start(self):
        """Start the runtime"""
        if self.running:
            return

        self.running = True
        self._executor_thread = threading.Thread(target=self._executor_loop)
        self._executor_thread.daemon = True
        self._executor_thread.start()

    def stop(self):
        """Stop the runtime"""
        self.running = False
        if self._executor_thread:
            self._executor_thread.join(timeout=5)

    def _executor_loop(self):
        """Main task execution loop"""
        while self.running:
            task = self.task_queue.get_next()
            if task:
                self._execute_task(task)
            else:
                time.sleep(0.1)


# Health check
def health_check() -> Dict:
    """Health check for agent runtime"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "runtime": {
            "running": running,
            "total_agents": len(agents),
            "pending_tasks": task_queue.get_pending_count()
        }
    }


# Singleton instance
agent_runtime = AgentRuntime()