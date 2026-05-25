"""
Day 65: Event-Driven Agent Architecture
========================================
Building agents with event-driven patterns.

Key Concepts:
- Event emitters
- Event listeners
- Event bubbling
- Async event handling
"""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio


class EventType(Enum):
    """Event types"""
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    TASK_RECEIVED = "task_received"
    TASK_COMPLETED = "task_completed"
    TOOL_INVOKED = "tool_invoked"
    ERROR = "error"
    MESSAGE = "message"


@dataclass
class Event:
    """An event in the system"""
    event_type: EventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


class EventEmitter:
    """
    Event Emitter
    =============

    Base class for event-driven components.
    """

    def __init__(self, name: str):
        self.name = name
        self.listeners: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []

    def on(self, event_type: EventType, callback: Callable):
        """Register an event listener"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable):
        """Remove an event listener"""
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)

    async def emit(self, event_type: EventType, data: Dict[str, Any] = None):
        """Emit an event"""
        event = Event(
            event_type=event_type,
            source=self.name,
            data=data or {}
        )

        self.event_history.append(event)

        # Call listeners
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)


class EventDrivenAgent(EventEmitter):
    """
    Event-Driven Agent
    ===================

    Agent that responds to events.
    """

    def __init__(self, agent_id: str, name: str):
        super().__init__(name)
        self.agent_id = agent_id
        self.state = "idle"
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

        # Register default handlers
        self.on(EventType.TASK_RECEIVED, self._handle_task)
        self.on(EventType.AGENT_STOP, self._handle_stop)

    async def start(self):
        """Start the agent"""
        self._running = True
        await self.emit(EventType.AGENT_START, {"agent_id": self.agent_id})

        # Start processing tasks
        asyncio.create_task(self._process_tasks())

    async def stop(self):
        """Stop the agent"""
        self._running = False
        await self.emit(EventType.AGENT_STOP, {"agent_id": self.agent_id})

    async def submit_task(self, task_data: Dict[str, Any]):
        """Submit a task for processing"""
        await self.emit(EventType.TASK_RECEIVED, {"task": task_data})
        await self.task_queue.put(task_data)

    async def _process_tasks(self):
        """Process tasks from queue"""
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue

    async def _execute_task(self, task: Dict[str, Any]):
        """Execute a task"""
        task_id = task.get("id", "unknown")

        try:
            # Simulate task execution
            await asyncio.sleep(0.1)

            await self.emit(EventType.TASK_COMPLETED, {
                "task_id": task_id,
                "result": f"Processed by {self.agent_id}"
            })

        except Exception as e:
            await self.emit(EventType.ERROR, {
                "task_id": task_id,
                "error": str(e)
            })

    async def _handle_task(self, event: Event):
        """Handle incoming task"""
        print(f"[{self.name}] Received task: {event.data.get('task', {})}")

    async def _handle_stop(self, event: Event):
        """Handle stop event"""
        print(f"[{self.name}] Stopping...")


class EventBus:
    """
    Event Bus
    ==========

    Central event distribution system.
    """

    def __init__(self):
        self.emitters: Dict[str, EventEmitter] = {}
        self.global_listeners: Dict[EventType, List[Callable]] = {}

    def register_emitter(self, emitter: EventEmitter):
        """Register an event emitter"""
        self.emitters[emitter.name] = emitter

        # Forward events to global listeners
        for event_type in EventType:
            original_listeners = emitter.listeners.get(event_type, []).copy()

            async def create_forwarder(et):
                async def forwarder(event):
                    if et in self.global_listeners:
                        for listener in self.global_listeners[et]:
                            if asyncio.iscoroutinefunction(listener):
                                await listener(event)
                            else:
                                listener(event)

                return forwarder

            emitter.on(event_type, await create_forwarder(event_type))

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type globally"""
        if event_type not in self.global_listeners:
            self.global_listeners[event_type] = []
        self.global_listeners[event_type].append(callback)


# Demo
async def main():
    print("=" * 60)
    print("Day 65: Event-Driven Agent Architecture")
    print("=" * 60)

    # Create event bus
    bus = EventBus()

    # Subscribe globally
    async def log_event(event: Event):
        print(f"  [GLOBAL] {event.event_type.value}: {event.data}")

    bus.subscribe(EventType.TASK_RECEIVED, log_event)
    bus.subscribe(EventType.TASK_COMPLETED, log_event)

    # Create agents
    agent1 = EventDrivenAgent("agent_001", "AnalysisAgent")
    agent2 = EventDrivenAgent("agent_002", "ProcessingAgent")

    bus.register_emitter(agent1)
    bus.register_emitter(agent2)

    # Start agents
    await agent1.start()
    await agent2.start()

    # Submit tasks
    print("\nSubmitting tasks...")
    await agent1.submit_task({"id": "task_1", "type": "analyze", "data": "test"})
    await agent2.submit_task({"id": "task_2", "type": "process", "data": "test"})

    # Wait for processing
    await asyncio.sleep(0.5)

    # Stop agents
    await agent1.stop()
    await agent2.stop()

    # Event history
    print("\n" + "-" * 40)
    print(f"Agent1 events: {len(agent1.event_history)}")
    print(f"Agent2 events: {len(agent2.event_history)}")


if __name__ == "__main__":
    asyncio.run(main())