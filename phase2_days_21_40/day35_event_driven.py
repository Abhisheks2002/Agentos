"""
Day 35: Event-Driven Agent Systems
===================================
Skill: Event Handling
Mini Project: Event Bus

Building reactive agent systems with events.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class EventType(str, Enum):
    """Types of events"""
    TASK_SUBMITTED = "task_submitted"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_STATUS = "agent_status"
    AGENT_REGISTERED = "agent_registered"
    MESSAGE_RECEIVED = "message_received"
    RESOURCE_CHANGE = "resource_change"
    CUSTOM = "custom"


@dataclass
class Event:
    """An event in the system"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM
    source: str = ""
    data: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Central event bus for agent communication"""

    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.global_subscribers: List[Callable] = []

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any]
    ):
        """Subscribe to an event type"""
        self.subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[Event], Any]):
        """Subscribe to all events"""
        self.global_subscribers.append(handler)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable
    ):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(handler)

    async def publish(self, event: Event):
        """Publish an event"""
        self.event_history.append(event)

        # Notify type-specific subscribers
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result

        # Notify global subscribers
        for handler in self.global_subscribers:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result

    def get_events(
        self,
        event_type: EventType = None,
        source: str = None,
        limit: int = 100
    ) -> List[Event]:
        """Get events with optional filtering"""
        events = self.event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]


class ReactiveAgent:
    """Agent that reacts to events"""

    def __init__(self, agent_id: str, event_bus: EventBus):
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.reactions: Dict[EventType, Callable] = {}
        self.active = True

    def on(self, event_type: EventType, handler: Callable):
        """Register a reaction to an event"""
        self.reactions[event_type] = handler
        self.event_bus.subscribe(event_type, self._create_handler(event_type, handler))

    def _create_handler(self, event_type: EventType, handler: Callable) -> Callable:
        """Create a wrapped handler"""
        async def wrapped(event: Event):
            if self.active and event.source != self.agent_id:
                return await handler(event)
        return wrapped

    def stop(self):
        """Stop reacting to events"""
        self.active = False

    async def emit(
        self,
        event_type: EventType,
        data: Any = None,
        metadata: Dict = None
    ):
        """Emit an event"""
        event = Event(
            event_type=event_type,
            source=self.agent_id,
            data=data,
            metadata=metadata or {}
        )
        await self.event_bus.publish(event)


class EventDrivenWorkflow:
    """Workflow driven by events"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.states: Dict[str, Dict] = {}
        self.transitions: Dict[str, Dict[str, str]] = {}

    def add_state(self, state_name: str, is_final: bool = False):
        """Add a state"""
        self.states[state_name] = {
            "name": state_name,
            "is_final": is_final
        }

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        event_type: EventType,
        condition: Callable = None
    ):
        """Add a transition"""
        if from_state not in self.transitions:
            self.transitions[from_state] = {}

        self.transitions[from_state][event_type.value] = {
            "to": to_state,
            "condition": condition
        }

    async def handle_event(
        self,
        current_state: str,
        event: Event
    ) -> Optional[str]:
        """Handle an event and transition"""
        if current_state not in self.transitions:
            return current_state

        transitions = self.transitions[current_state]

        if event.event_type.value not in transitions:
            return current_state

        transition = transitions[event.event_type.value]

        # Check condition
        if transition["condition"]:
            if not transition["condition"](event):
                return current_state

        return transition["to"]


class EventFilter:
    """Filter events based on criteria"""

    def __init__(self):
        self.filters: List[Callable[[Event], bool]] = []

    def add_filter(self, filter_func: Callable[[Event], bool]):
        """Add a filter"""
        self.filters.append(filter_func)

    def apply(self, events: List[Event]) -> List[Event]:
        """Apply filters to events"""
        filtered = events

        for f in self.filters:
            filtered = [e for e in filtered if f(e)]

        return filtered


class EventAggregator:
    """Aggregate events over time windows"""

    def __init__(self, window_size: float = 1.0):
        self.window_size = window_size
        self.buckets: Dict[str, List[Event]] = defaultdict(list)

    async def add_event(self, key: str, event: Event):
        """Add event to aggregation"""
        self.buckets[key].append(event)

    def get_aggregated(self, key: str) -> Dict[str, Any]:
        """Get aggregated events"""
        events = self.buckets.get(key, [])

        return {
            "count": len(events),
            "types": list(set(e.event_type.value for e in events)),
            "sources": list(set(e.source for e in events))
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Event-Driven Agent Systems Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create event bus
        bus = EventBus()

        # Create reactive agents
        print("\n[1] Reactive Agents")
        print("-" * 40)

        agent1 = ReactiveAgent("Agent1", bus)
        agent2 = ReactiveAgent("Agent2", bus)

        # Define reactions
        async def on_task_completed(event: Event):
            print(f"  Agent1 learned: Task {event.data.get('id')} completed")

        agent1.on(EventType.TASK_COMPLETED, on_task_completed)

        # Emit events
        print("\n[2] Emit Events")
        print("-" * 40)

        await agent2.emit(
            EventType.TASK_COMPLETED,
            {"id": "task-123"},
            {"result": "success"}
        )

        await asyncio.sleep(0.1)  # Let event propagate

        # Event history
        print("\n[3] Event History")
        print("-" * 40)

        events = bus.get_events()
        print(f"  Total events: {len(events)}")
        if events:
            print(f"  Latest: {events[-1].event_type.value}")

        # Workflow
        print("\n[4] Event-Driven Workflow")
        print("-" * 40)

        workflow = EventDrivenWorkflow(bus)
        workflow.add_state("idle")
        workflow.add_state("processing")
        workflow.add_state("complete")

        workflow.add_transition("idle", "processing", EventType.TASK_SUBMITTED)
        workflow.add_transition("processing", "complete", EventType.TASK_COMPLETED)

        # Simulate state transitions
        current_state = "idle"
        print(f"  Initial state: {current_state}")

        event = Event(event_type=EventType.TASK_SUBMITTED, source="test")
        current_state = await workflow.handle_event(current_state, event)
        print(f"  After TASK_SUBMITTED: {current_state}")

        event = Event(event_type=EventType.TASK_COMPLETED, source="test")
        current_state = await workflow.handle_event(current_state, event)
        print(f"  After TASK_COMPLETED: {current_state}")

        # Event aggregation
        print("\n[5] Event Aggregation")
        print("-" * 40)

        aggregator = EventAggregator()
        await aggregator.add_event("tasks", Event(event_type=EventType.TASK_SUBMITTED, source="A"))
        await aggregator.add_event("tasks", Event(event_type=EventType.TASK_SUBMITTED, source="B"))
        await aggregator.add_event("tasks", Event(event_type=EventType.TASK_COMPLETED, source="A"))

        result = aggregator.get_aggregated("tasks")
        print(f"  Task events: {result['count']}")
        print(f"  Types: {result['types']}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()