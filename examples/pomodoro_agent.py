"""Pomodoro Agent - Example from Day 9 PDF

This agent demonstrates:
- Timer system (work/break cycles)
- Session management
- Notification system
- Task tracking

Run with: python -m examples.pomodoro_agent
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from core.agent import Agent, AgentResponse
from core.agent_builder import AgentBuilder
from core.models.models import AgentType
from core.reasoning.chain_of_thought import ReasoningType


class SessionType(Enum):
    """Types of Pomodoro sessions."""
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class TimerState(Enum):
    """Timer states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class PomodoroTimer:
    """Timer system for Pomodoro sessions."""

    # Default durations in minutes
    DEFAULT_WORK_DURATION = 25
    DEFAULT_SHORT_BREAK = 5
    DEFAULT_LONG_BREAK = 15
    SESSIONS_BEFORE_LONG_BREAK = 4

    def __init__(
        self,
        work_duration: int = DEFAULT_WORK_DURATION,
        short_break: int = DEFAULT_SHORT_BREAK,
        long_break: int = DEFAULT_LONG_BREAK
    ):
        self.work_duration = work_duration
        self.short_break = short_break
        self.long_break = long_break

        self.state = TimerState.IDLE
        self.current_session_type = SessionType.WORK
        self.remaining_seconds = work_duration * 60
        self.sessions_completed = 0

        self._timer_task: Optional[asyncio.Task] = None
        self._callbacks: List[callable] = []

    def add_callback(self, callback: callable):
        """Add a callback to be called on timer updates."""
        self._callbacks.append(callback)

    def _notify_callbacks(self):
        """Notify all callbacks of timer update."""
        for callback in self._callbacks:
            try:
                callback(self.get_status())
            except Exception as e:
                print(f"Callback error: {e}")

    def get_status(self) -> Dict:
        """Get current timer status."""
        return {
            "state": self.state.value,
            "session_type": self.current_session_type.value,
            "remaining_seconds": self.remaining_seconds,
            "sessions_completed": self.sessions_completed,
            "total_work_sessions": self.sessions_completed
        }

    async def start(self, session_type: SessionType = None):
        """Start the timer."""
        if session_type:
            self.current_session_type = session_type
            if session_type == SessionType.WORK:
                self.remaining_seconds = self.work_duration * 60
            elif session_type == SessionType.SHORT_BREAK:
                self.remaining_seconds = self.short_break * 60
            elif session_type == SessionType.LONG_BREAK:
                self.remaining_seconds = self.long_break * 60

        if self.state == TimerState.RUNNING:
            return

        self.state = TimerState.RUNNING
        self._timer_task = asyncio.create_task(self._run_timer())

    async def _run_timer(self):
        """Run the timer countdown."""
        while self.remaining_seconds > 0 and self.state == TimerState.RUNNING:
            await asyncio.sleep(1)
            self.remaining_seconds -= 1
            self._notify_callbacks()

        if self.remaining_seconds == 0:
            await self._on_session_complete()

    async def _on_session_complete(self):
        """Handle session completion."""
        self.state = TimerState.COMPLETED

        if self.current_session_type == SessionType.WORK:
            self.sessions_completed += 1
            self._notify_callbacks()

        # Auto-start next session type
        await self._schedule_next_session()

    async def _schedule_next_session(self):
        """Schedule the next session automatically."""
        if self.current_session_type == SessionType.WORK:
            # After work session, take a break
            if self.sessions_completed % self.SESSIONS_BEFORE_LONG_BREAK == 0:
                next_type = SessionType.LONG_BREAK
            else:
                next_type = SessionType.SHORT_BREAK
        else:
            # After break, back to work
            next_type = SessionType.WORK

        await self.start(next_type)

    async def pause(self):
        """Pause the timer."""
        if self.state == TimerState.RUNNING:
            self.state = TimerState.PAUSED
            if self._timer_task:
                self._timer_task.cancel()
                try:
                    await self._timer_task
                except asyncio.CancelledError:
                    pass

    async def resume(self):
        """Resume the timer."""
        if self.state == TimerState.PAUSED:
            await self.start()

    async def stop(self):
        """Stop the timer."""
        self.state = TimerState.IDLE
        if self._timer_task:
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass

    async def reset(self):
        """Reset the timer to initial state."""
        await self.stop()
        self.state = TimerState.IDLE
        self.current_session_type = SessionType.WORK
        self.remaining_seconds = self.work_duration * 60
        self.sessions_completed = 0
        self._notify_callbacks()

    def format_time(self) -> str:
        """Format remaining time as MM:SS."""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


class SessionManager:
    """Manages Pomodoro session history."""

    def __init__(self):
        self.sessions: List[Dict] = []
        self.current_session_id = 0

    def start_session(
        self,
        session_type: SessionType,
        task_name: str = None
    ) -> Dict:
        """Start a new session record."""
        self.current_session_id += 1
        session = {
            "id": self.current_session_id,
            "type": session_type.value,
            "task": task_name,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_minutes": 0,
            "completed": False
        }
        self.sessions.append(session)
        return session

    def complete_session(self, session_id: int) -> Dict:
        """Mark a session as completed."""
        for session in self.sessions:
            if session["id"] == session_id:
                session["end_time"] = datetime.now().isoformat()
                session["completed"] = True

                # Calculate duration
                start = datetime.fromisoformat(session["start_time"])
                end = datetime.fromisoformat(session["end_time"])
                session["duration_minutes"] = int((end - start).total_seconds() / 60)

                return session

        return {"error": "Session not found"}

    def get_session_history(
        self,
        days: int = 7,
        session_type: SessionType = None
    ) -> List[Dict]:
        """Get session history."""
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []

        for session in self.sessions:
            session_date = datetime.fromisoformat(session["start_time"])
            if session_date >= cutoff:
                if session_type is None or session["type"] == session_type.value:
                    filtered.append(session)

        return filtered

    def get_statistics(self) -> Dict:
        """Get session statistics."""
        completed_work = [
            s for s in self.sessions
            if s["completed"] and s["type"] == "work"
        ]

        total_minutes = sum(s["duration_minutes"] for s in completed_work)
        total_hours = total_minutes / 60

        return {
            "total_sessions": len(completed_work),
            "total_work_minutes": total_minutes,
            "total_work_hours": round(total_hours, 2),
            "average_session_length": (
                total_minutes // len(completed_work) if completed_work else 0
            )
        }


class TaskTracker:
    """Tracks tasks during Pomodoro sessions."""

    def __init__(self):
        self.tasks: Dict[int, Dict] = {}
        self.current_task_id = 0

    def add_task(self, name: str, estimated_pomodoros: int = 1) -> Dict:
        """Add a new task."""
        self.current_task_id += 1
        task = {
            "id": self.current_task_id,
            "name": name,
            "estimated_pomodoros": estimated_pomodoros,
            "completed_pomodoros": 0,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.tasks[self.current_task_id] = task
        return task

    def complete_pomodoro(self, task_id: int) -> Dict:
        """Mark a pomodoro as completed for a task."""
        if task_id not in self.tasks:
            return {"error": "Task not found"}

        task = self.tasks[task_id]
        task["completed_pomodoros"] += 1

        if task["completed_pomodoros"] >= task["estimated_pomodoros"]:
            task["status"] = "completed"

        return task

    def get_task(self, task_id: int) -> Dict:
        """Get a task by ID."""
        return self.tasks.get(task_id, {"error": "Task not found"})

    def list_tasks(self, status: str = None) -> List[Dict]:
        """List all tasks, optionally filtered by status."""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t["status"] == status]

        return sorted(tasks, key=lambda x: x["id"], reverse=True)

    def delete_task(self, task_id: int) -> Dict:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return {"success": True, "message": f"Task {task_id} deleted"}
        return {"error": "Task not found"}


class NotificationSystem:
    """Handles notifications for Pomodoro sessions."""

    def __init__(self):
        self.enabled = True

    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info"
    ) -> Dict:
        """Send a notification."""
        if not self.enabled:
            return {"success": False, "message": "Notifications disabled"}

        # In a real implementation, this would use system notifications
        # For now, we'll just print
        print(f"\n{'='*50}")
        print(f"[{notification_type.upper()}] {title}")
        print(f"{message}")
        print(f"{'='*50}\n")

        return {
            "success": True,
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

    async def notify_session_start(self, session_type: SessionType, task_name: str = None):
        """Notify session start."""
        if session_type == SessionType.WORK:
            title = "🍅 Focus Time!"
            message = f"Starting {task_name or 'work'} session. Stay focused!"
        elif session_type == SessionType.SHORT_BREAK:
            title = "☕ Short Break"
            message = "Time for a 5-minute break. Stretch and relax!"
        else:
            title = "🌟 Long Break"
            message = "Great work! Take a 15-minute break."

        await self.send_notification(title, message, "session")

    async def notify_session_complete(self, session_type: SessionType):
        """Notify session completion."""
        if session_type == SessionType.WORK:
            title = "✅ Session Complete!"
            message = "Great job! Time for a break."
        else:
            title = "⏰ Break Over"
            message = "Ready to get back to work?"

        await self.send_notification(title, message, "complete")


def create_pomodoro_agent() -> Agent:
    """Create a fully configured Pomodoro agent."""

    # Define Pomodoro tools
    pomodoro_tools = [
        {
            "name": "start_timer",
            "description": "Start a Pomodoro timer session",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_type": {
                        "type": "string",
                        "description": "Type of session: work, short_break, or long_break",
                        "enum": ["work", "short_break", "long_break"]
                    },
                    "task_name": {
                        "type": "string",
                        "description": "Name of the task to work on"
                    }
                }
            }
        },
        {
            "name": "pause_timer",
            "description": "Pause the current timer",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "resume_timer",
            "description": "Resume a paused timer",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "stop_timer",
            "description": "Stop the current timer",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "reset_timer",
            "description": "Reset the timer to initial state",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_timer_status",
            "description": "Get current timer status",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_session_history",
            "description": "Get session history",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "number",
                        "description": "Number of days to look back"
                    }
                }
            }
        },
        {
            "name": "get_statistics",
            "description": "Get productivity statistics",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "add_task",
            "description": "Add a new task to track",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Task name"
                    },
                    "estimated_pomodoros": {
                        "type": "number",
                        "description": "Estimated number of pomodoros"
                    }
                }
            }
        },
        {
            "name": "list_tasks",
            "description": "List all tasks",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending, in_progress, completed",
                        "enum": ["pending", "in_progress", "completed"]
                    }
                }
            }
        },
        {
            "name": "complete_task_pomodoro",
            "description": "Mark a pomodoro as complete for a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "number",
                        "description": "Task ID"
                    }
                }
            }
        }
    ]

    # Create the agent
    agent = (
        AgentBuilder("Pomodoro Assistant")
        .with_type(AgentType.TASK)
        .with_tools(pomodoro_tools)
        .with_reasoning(ReasoningType.REACT)
        .with_system_prompt("""You are a Pomodoro productivity assistant.

You help users manage their time using the Pomodoro Technique:

Capabilities:
- start_timer: Start a work (25min), short_break (5min), or long_break (15min) session
- pause_timer: Pause the current timer
- resume_timer: Resume a paused timer
- stop_timer: Stop and reset the timer
- reset_timer: Reset timer to initial state
- get_timer_status: Check current timer status
- get_session_history: View past sessions
- get_statistics: View productivity stats
- add_task: Add a task to track
- list_tasks: List all tasks
- complete_task_pomodoro: Mark a pomodoro complete for a task

Best practices:
1. Encourage users to use the timer
2. Remind them to take breaks
3. Track their tasks and progress
4. Provide motivational messages

Default timer: 25 min work, 5 min short break, 15 min long break (every 4 sessions)""")
        .build()
    )

    return agent


class PomodoroAgent:
    """Pomodoro Agent with integrated timer and task tracking."""

    def __init__(self):
        self.timer = PomodoroTimer()
        self.session_manager = SessionManager()
        self.task_tracker = TaskTracker()
        self.notifications = NotificationSystem()
        self.current_task_id = None

        # Create the agent
        self.agent = create_pomodoro_agent()

        # Setup timer callback
        self.timer.add_callback(self._on_timer_tick)

        # Tool handlers
        self.tool_handlers = {
            "start_timer": self._start_timer,
            "pause_timer": self._pause_timer,
            "resume_timer": self._resume_timer,
            "stop_timer": self._stop_timer,
            "reset_timer": self._reset_timer,
            "get_timer_status": self._get_timer_status,
            "get_session_history": self._get_session_history,
            "get_statistics": self._get_statistics,
            "add_task": self._add_task,
            "list_tasks": self._list_tasks,
            "complete_task_pomodoro": self._complete_task_pomodoro
        }

        # Override tool execution
        self._setup_tool_execution()

    def _setup_tool_execution(self):
        """Setup custom tool execution."""
        original_execute = getattr(self.agent, '_execute_tool', None)

        async def execute_with_handler(tool_name: str, params: Dict):
            handler = self.tool_handlers.get(tool_name)
            if handler:
                try:
                    return await handler(params)
                except Exception as e:
                    return {"error": str(e)}
            if original_execute:
                return await original_execute(tool_name, params)
            return {"error": "Tool not found"}

        self.agent._execute_tool = execute_with_handler

    def _on_timer_tick(self, status: Dict):
        """Handle timer tick."""
        pass  # Could add real-time updates here

    # Tool handlers
    async def _start_timer(self, params: Dict) -> Dict:
        session_type_str = params.get("session_type", "work")
        task_name = params.get("task_name")

        if session_type_str == "work":
            session_type = SessionType.WORK
        elif session_type_str == "short_break":
            session_type = SessionType.SHORT_BREAK
        elif session_type_str == "long_break":
            session_type = SessionType.LONG_BREAK
        else:
            session_type = SessionType.WORK

        # Start session in manager
        session = self.session_manager.start_session(session_type, task_name)

        # Add task if provided
        if task_name:
            task = self.task_tracker.add_task(task_name)
            self.current_task_id = task["id"]

        # Start timer
        await self.timer.start(session_type)

        # Send notification
        await self.notifications.notify_session_start(session_type, task_name)

        status = self.timer.get_status()
        status["session_id"] = session["id"]
        status["message"] = f"Started {session_type.value} session"
        return status

    async def _pause_timer(self, params: Dict) -> Dict:
        await self.timer.pause()
        return {
            "success": True,
            "message": "Timer paused",
            "remaining_time": self.timer.format_time()
        }

    async def _resume_timer(self, params: Dict) -> Dict:
        await self.timer.resume()
        return {
            "success": True,
            "message": "Timer resumed",
            "remaining_time": self.timer.format_time()
        }

    async def _stop_timer(self, params: Dict) -> Dict:
        await self.timer.stop()
        return {
            "success": True,
            "message": "Timer stopped"
        }

    async def _reset_timer(self, params: Dict) -> Dict:
        await self.timer.reset()
        return {
            "success": True,
            "message": "Timer reset",
            "status": self.timer.get_status()
        }

    async def _get_timer_status(self, params: Dict) -> Dict:
        status = self.timer.get_status()
        status["formatted_time"] = self.timer.format_time()
        return status

    async def _get_session_history(self, params: Dict) -> Dict:
        days = params.get("days", 7)
        sessions = self.session_manager.get_session_history(days)
        return {
            "sessions": sessions,
            "count": len(sessions)
        }

    async def _get_statistics(self, params: Dict) -> Dict:
        return self.session_manager.get_statistics()

    async def _add_task(self, params: Dict) -> Dict:
        name = params.get("name")
        estimated_pomodoros = params.get("estimated_pomodoros", 1)

        if not name:
            return {"error": "Task name is required"}

        task = self.task_tracker.add_task(name, estimated_pomodoros)
        return task

    async def _list_tasks(self, params: Dict) -> Dict:
        status = params.get("status")
        tasks = self.task_tracker.list_tasks(status)
        return {
            "tasks": tasks,
            "count": len(tasks)
        }

    async def _complete_task_pomodoro(self, params: Dict) -> Dict:
        task_id = params.get("task_id")

        if not task_id:
            return {"error": "Task ID is required"}

        task = self.task_tracker.complete_pomodoro(task_id)
        return task

    async def start(self):
        """Start the agent."""
        await self.agent.start()

    async def stop(self):
        """Stop the agent."""
        await self.timer.stop()
        await self.agent.stop()

    async def handle_message(self, message: str) -> str:
        """Handle a user message."""
        response = await self.agent.run(message)
        return response.output

    async def run_interactive(self):
        """Run interactive Pomodoro session."""
        print("=" * 50)
        print("Pomodoro Agent - Interactive Mode")
        print("=" * 50)
        print("\nCommands:")
        print("- start work <task_name>")
        print("- start break")
        print("- pause / resume / stop")
        print("- status")
        print("- tasks")
        print("- stats")
        print("- quit")
        print()

        await self.start()

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Stay productive!")
                break

            if not user_input:
                continue

            # Handle quick commands
            if user_input.lower() == "status":
                status = await self._get_timer_status({})
                print(f"\nTimer: {status}")
                continue

            if user_input.lower() == "stats":
                stats = await self._get_statistics({})
                print(f"\nStatistics: {stats}")
                continue

            if user_input.lower() == "tasks":
                result = await self._list_tasks({})
                print(f"\nTasks: {result}")
                continue

            if user_input.lower() == "pause":
                result = await self._pause_timer({})
                print(f"\n{result}")
                continue

            if user_input.lower() == "resume":
                result = await self._resume_timer({})
                print(f"\n{result}")
                continue

            if user_input.lower() == "stop":
                result = await self._stop_timer({})
                print(f"\n{result}")
                continue

            response = await self.handle_message(user_input)
            print(f"\nAgent: {response}\n")

        await self.stop()


async def run_pomodoro_demo():
    """Run a demonstration of the Pomodoro agent."""
    print("=" * 50)
    print("Pomodoro Agent Demo")
    print("=" * 50)

    agent = PomodoroAgent()
    await agent.start()

    # Demo interactions
    test_scenarios = [
        "Start a work session for writing",
        "What's my timer status?",
        "Add a task to review the document",
        "Show me my tasks",
        "What's my productivity stats?"
    ]

    for scenario in test_scenarios:
        print(f"\n--- User: {scenario} ---")
        response = await agent.handle_message(scenario)
        print(f"Agent: {response}")

    # Show timer status
    status = await agent._get_timer_status({})
    print(f"\nFinal Timer Status: {status}")

    await agent.stop()

    print("\n" + "=" * 50)
    print("Demo complete!")
    print("=" * 50)


if __name__ == "__main__":
    # Option 1: Run demo
    asyncio.run(run_pomodoro_demo())

    # Option 2: Run interactive mode (uncomment below)
    # agent = PomodoroAgent()
    # asyncio.run(agent.run_interactive())