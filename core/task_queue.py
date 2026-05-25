"""
AgentOS - Task Queue System
Priority-based task queue with persistent storage for AI agents
"""

import uuid
import threading
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from queue import PriorityQueue, Empty
from dataclasses import dataclass, field
from datetime import datetime as dt


class TaskState(Enum):
    """Task execution states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    HIGH = 0      # Highest priority
    NORMAL = 1    # Default priority
    LOW = 2       # Lowest priority


@dataclass
class Task:
    """Task representation"""
    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    agent_id: str = ""
    task_type: str = ""
    payload: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.QUEUED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict] = None
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    timeout: int = 300  # Default 5 minutes

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "state": self.state.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result,
            "error": self.error,
            "depends_on": self.depends_on,
            "timeout": self.timeout
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create from dictionary"""
        task = cls()
        task.task_id = data.get("task_id", f"task_{uuid.uuid4().hex[:8]}")
        task.agent_id = data.get("agent_id", "")
        task.task_type = data.get("task_type", "")
        task.payload = data.get("payload", {})
        task.priority = TaskPriority(data.get("priority", 1))
        task.state = TaskState(data.get("state", "queued"))
        task.created_at = data.get("created_at", datetime.now().isoformat())
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.retry_count = data.get("retry_count", 0)
        task.max_retries = data.get("max_retries", 3)
        task.result = data.get("result")
        task.error = data.get("error")
        task.depends_on = data.get("depends_on", [])
        task.timeout = data.get("timeout", 300)
        return task


class TaskWorker(threading.Thread):
    """Worker thread for processing tasks"""

    def __init__(self, worker_id: str, task_queue: 'TaskQueue', handler: Callable):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.handler = handler
        self.running = False
        self.current_task = None

    def run(self):
        """Worker main loop"""
        self.running = True
        while self.running:
            try:
                # Get task with timeout
                task = self.task_queue.get_task(timeout=1)
                if task is None:
                    continue

                self.current_task = task
                self.task_queue.update_task_state(task.task_id, TaskState.PROCESSING)
                task.started_at = datetime.now().isoformat()

                # Execute task
                try:
                    result = self.handler(task)
                    task.result = result
                    task.completed_at = datetime.now().isoformat()
                    self.task_queue.update_task_state(task.task_id, TaskState.COMPLETED)

                    # Mark dependent tasks as ready
                    self.task_queue.mark_dependencies_complete(task.task_id)

                except Exception as e:
                    task.error = str(e)
                    task.completed_at = datetime.now().isoformat()

                    if task.retry_count < task.max_retries:
                        task.retry_count += 1
                        self.task_queue.update_task_state(task.task_id, TaskState.RETRY)
                        # Re-queue with delay
                        time.sleep(2 ** task.retry_count)  # Exponential backoff
                        self.task_queue.enqueue(task)
                    else:
                        self.task_queue.update_task_state(task.task_id, TaskState.FAILED)

                self.current_task = None

            except Empty:
                continue
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")

    def stop(self):
        """Stop worker"""
        self.running = False


class TaskQueue:
    """Priority-based task queue with persistent storage"""

    def __init__(self, db=None, max_workers: int = 5):
        self.db = db
        self.max_workers = max_workers
        self.workers: List[TaskWorker] = []

        # Priority queue: (priority, timestamp, task)
        self._queue = PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._running = False
        self._handler: Optional[Callable] = None

        # Statistics
        self.stats = {
            "total_queued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retried": 0
        }

    def start(self, handler: Callable):
        """Start the task queue with a handler"""
        if self._running:
            return

        self._handler = handler
        self._running = True

        # Start worker threads
        for i in range(self.max_workers):
            worker = TaskWorker(f"worker_{i}", self, handler)
            worker.start()
            self.workers.append(worker)

        # Load pending tasks from database
        if self.db:
            self._load_pending_tasks()

    def stop(self):
        """Stop the task queue"""
        self._running = False
        for worker in self.workers:
            worker.stop()
        self.workers.clear()

    def _load_pending_tasks(self):
        """Load pending tasks from database"""
        try:
            pending = self.db.get_pending_tasks()
            for task_data in pending:
                task = Task.from_dict(task_data)
                if task.state in [TaskState.QUEUED, TaskState.RETRY]:
                    self._tasks[task.task_id] = task
                    self._queue.put((task.priority.value, time.time(), task))
                    self.stats["total_queued"] += 1
        except Exception as e:
            print(f"Error loading pending tasks: {e}")

    def enqueue(self, task: Task) -> str:
        """Add task to queue"""
        with self._lock:
            # Check dependencies
            if task.depends_on:
                for dep_id in task.depends_on:
                    if dep_id in self._tasks:
                        dep_task = self._tasks[dep_id]
                        if dep_task.state != TaskState.COMPLETED:
                            # Cannot enqueue yet
                            task.state = TaskState.QUEUED

            self._tasks[task.task_id] = task
            self._queue.put((task.priority.value, time.time(), task))
            self.stats["total_queued"] += 1

            # Persist to database
            if self.db:
                self.db.save_task(task.to_dict())

            return task.task_id

    def get_task(self, timeout: float = 1) -> Optional[Task]:
        """Get next task from queue"""
        try:
            _, _, task = self._queue.get(timeout=timeout)
            return task
        except Empty:
            return None

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self._tasks.get(task_id)

    def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """Get all tasks for an agent"""
        return [t for t in self._tasks.values() if t.agent_id == agent_id]

    def get_tasks_by_state(self, state: TaskState) -> List[Task]:
        """Get tasks by state"""
        return [t for t in self._tasks.values() if t.state == state]

    def update_task_state(self, task_id: str, state: TaskState):
        """Update task state"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.state = state

            if state == TaskState.COMPLETED:
                self.stats["total_completed"] += 1
            elif state == TaskState.FAILED:
                self.stats["total_failed"] += 1
            elif state == TaskState.RETRY:
                self.stats["total_retried"] += 1

            # Update in database
            if self.db:
                self.db.update_task_state(task_id, state.value)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.state in [TaskState.QUEUED, TaskState.RETRY]:
                task.state = TaskState.CANCELLED
                if self.db:
                    self.db.update_task_state(task_id, TaskState.CANCELLED.value)
                return True
        return False

    def mark_dependencies_complete(self, completed_task_id: str):
        """Mark tasks dependent on completed task"""
        for task in self._tasks.values():
            if completed_task_id in task.depends_on:
                # Check if all dependencies are met
                all_done = all(
                    self._tasks.get(dep_id) and
                    self._tasks[dep_id].state == TaskState.COMPLETED
                    for dep_id in task.depends_on
                )
                if all_done and task.state == TaskState.QUEUED:
                    # Re-queue the task
                    self._queue.put((task.priority.value, time.time(), task))

    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            "pending": len([t for t in self._tasks.values() if t.state == TaskState.QUEUED]),
            "processing": len([t for t in self._tasks.values() if t.state == TaskState.PROCESSING]),
            "completed": len([t for t in self._tasks.values() if t.state == TaskState.COMPLETED]),
            "failed": len([t for t in self._tasks.values() if t.state == TaskState.FAILED]),
            "retry": len([t for t in self._tasks.values() if t.state == TaskState.RETRY]),
            "total": len(self._tasks),
            "workers": len(self.workers),
            **self.stats
        }

    def clear_completed(self, older_than_hours: int = 24):
        """Clear completed tasks older than specified hours"""
        cutoff = datetime.now().timestamp() - (older_than_hours * 3600)
        to_remove = []

        for task_id, task in self._tasks.items():
            if task.state == TaskState.COMPLETED and task.completed_at:
                completed_time = datetime.fromisoformat(task.completed_at).timestamp()
                if completed_time < cutoff:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self._tasks[task_id]

        return len(to_remove)


# Default task handlers
def default_task_handler(task: Task) -> Dict:
    """Default task handler - can be overridden"""
    task_type = task.task_type

    handlers = {
        "file_read": lambda: {"type": "file_read", "status": "completed"},
        "file_write": lambda: {"type": "file_write", "status": "completed"},
        "process_data": lambda: {"type": "process_data", "status": "completed"},
        "send_notification": lambda: {"type": "notification", "status": "sent"},
    }

    handler = handlers.get(task_type, lambda: {"type": task_type, "status": "processed"})
    return handler()


# Singleton instance
task_queue = TaskQueue()