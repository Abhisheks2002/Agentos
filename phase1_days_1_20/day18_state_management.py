"""
Day 18: State Management - Finite State Machines
=================================================
Skill: Agent State Machines
Mini Project: Workflow State Tracker

Finite State Machines (FSMs) are crucial for managing complex agent
behaviors - from simple chatbots to multi-step workflows.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

# Note: This is a complete FSM framework


class AgentState(str, Enum):
    """Core agent states"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    TERMINATED = "terminated"


class Event(str, Enum):
    """Events that trigger state transitions"""
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    COMPLETE = "complete"
    FAIL = "fail"
    TIMEOUT = "timeout"
    USER_INPUT = "user_input"
    EXTERNAL_TRIGGER = "external_trigger"


@dataclass
class Transition:
    """State transition definition"""
    from_state: AgentState
    to_state: AgentState
    event: Event
    action: Optional[Callable] = None
    guard: Optional[Callable[[], bool]] = None


@dataclass
class AgentSnapshot:
    """Point-in-time snapshot of agent state"""
    state: AgentState
    context: Dict[str, Any]
    timestamp: str
    event_history: List[Dict[str, Any]]


class FiniteStateMachine:
    """
    Finite State Machine for Agent Management
    ===========================================

    Manages agent state transitions with:
    - Defined states and transitions
    - Guard conditions
    - Entry/exit actions
    - Event history
    """

    def __init__(self, initial_state: AgentState = AgentState.IDLE):
        self.current_state = initial_state
        self.initial_state = initial_state
        self.transitions: List[Transition] = []
        self.event_history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.listeners: Dict[AgentState, List[Callable]] = {
            state: [] for state in AgentState
        }

    def add_transition(self, transition: Transition):
        """Add a state transition"""
        self.transitions.append(transition)

    def add_transitions(self, transitions: List[Transition]):
        """Add multiple transitions"""
        self.transitions.extend(transitions)

    def on(self, state: AgentState, callback: Callable):
        """Register callback for state entry"""
        self.listeners[state].append(callback)

    def trigger(self, event: Event, data: Dict[str, Any] = None) -> bool:
        """
        Trigger an event and transition state if valid
        ==============================================
        Returns True if transition was successful
        """
        # Find valid transition
        for transition in self.transitions:
            if (transition.from_state == self.current_state and
                transition.event == event):

                # Check guard condition
                if transition.guard and not transition.guard():
                    self._log_event(event, "blocked_by_guard", data)
                    return False

                # Execute action if present
                if transition.action:
                    transition.action(self.context)

                # Transition to new state
                old_state = self.current_state
                self.current_state = transition.to_state

                # Log event
                self._log_event(event, f"{old_state} -> {transition.to_state}", data)

                # Notify listeners
                for callback in self.listeners[transition.to_state]:
                    callback(self.current_state, self.context)

                return True

        self._log_event(event, "no_valid_transition", data)
        return False

    def _log_event(self, event: Event, result: str, data: Dict[str, Any]):
        """Log event to history"""
        self.event_history.append({
            "event": event,
            "result": result,
            "from_state": self.current_state,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        })

    def reset(self):
        """Reset to initial state"""
        self.current_state = self.initial_state
        self.context = {}
        self.event_history = []

    def snapshot(self) -> AgentSnapshot:
        """Create state snapshot"""
        return AgentSnapshot(
            state=self.current_state,
            context=self.context.copy(),
            timestamp=datetime.now().isoformat(),
            event_history=self.event_history.copy()
        )


class AgentStateMachine(FiniteStateMachine):
    """
    Specialized FSM for AI Agents
    ==============================

    Pre-configured with common agent states and transitions
    """

    def __init__(self, agent_id: str):
        super().__init__(AgentState.IDLE)
        self.agent_id = agent_id
        self._setup_default_transitions()

    def _setup_default_transitions(self):
        """Setup standard agent state machine"""

        # Define transitions
        transitions = [
            # Initialization
            Transition(AgentState.IDLE, AgentState.INITIALIZING, Event.START),
            Transition(AgentState.INITIALIZING, AgentState.RUNNING, Event.COMPLETE),

            # Running states
            Transition(AgentState.RUNNING, AgentState.WAITING, Event.USER_INPUT),
            Transition(AgentState.WAITING, AgentState.RUNNING, Event.USER_INPUT),

            # Pause/Resume
            Transition(AgentState.RUNNING, AgentState.PAUSED, Event.PAUSE),
            Transition(AgentState.PAUSED, AgentState.RUNNING, Event.RESUME),

            # Completion
            Transition(AgentState.RUNNING, AgentState.COMPLETED, Event.COMPLETE),
            Transition(AgentState.WAITING, AgentState.COMPLETED, Event.COMPLETE),

            # Error handling
            Transition(AgentState.RUNNING, AgentState.ERROR, Event.FAIL),
            Transition(AgentState.WAITING, AgentState.ERROR, Event.FAIL),
            Transition(AgentState.INITIALIZING, AgentState.ERROR, Event.FAIL),

            # Termination (from any state)
            Transition(AgentState.PAUSED, AgentState.TERMINATED, Event.STOP),
            Transition(AgentState.ERROR, AgentState.TERMINATED, Event.STOP),
            Transition(AgentState.COMPLETED, AgentState.TERMINATED, Event.STOP),

            # Reset from terminated
            Transition(AgentState.TERMINATED, AgentState.IDLE, Event.START),
        ]

        self.add_transitions(transitions)

    def start(self, initial_data: Dict[str, Any] = None):
        """Start the agent"""
        if initial_data:
            self.context.update(initial_data)
        return self.trigger(Event.START, {"action": "start_agent"})

    def pause(self, reason: str = None):
        """Pause the agent"""
        return self.trigger(Event.PAUSE, {"reason": reason})

    def resume(self):
        """Resume the agent"""
        return self.trigger(Event.RESUME)

    def complete(self, result: Dict[str, Any] = None):
        """Mark agent task as complete"""
        if result:
            self.context["result"] = result
        return self.trigger(Event.COMPLETE)

    def fail(self, error: str):
        """Mark agent as failed"""
        self.context["error"] = error
        return self.trigger(Event.FAIL, {"error": error})

    def stop(self):
        """Stop/terminate the agent"""
        return self.trigger(Event.STOP)

    def wait_for_input(self):
        """Wait for user input"""
        return self.trigger(Event.USER_INPUT, {"status": "waiting"})

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "state": self.current_state.value,
            "context": self.context,
            "history_length": len(self.event_history)
        }


class WorkflowFSM(FiniteStateMachine):
    """
    Workflow Finite State Machine
    =============================

    Manages multi-step workflows with checkpoints
    """

    def __init__(self, workflow_id: str, steps: List[str]):
        super().__init__()
        self.workflow_id = workflow_id
        self.steps = steps
        self.current_step_index = 0
        self._setup_workflow_transitions()

    def _setup_workflow_transitions(self):
        """Setup workflow-specific transitions"""

        # Add transitions for each step
        for i, step in enumerate(self.steps):
            from_state = AgentState.RUNNING if i == 0 else AgentState.WAITING

            # Step completion triggers next step
            Transition(
                from_state,
                AgentState.WAITING,
                Event.COMPLETE,
                action=lambda ctx: self._advance_step()
            )

        # Final step -> Completed
        Transition(AgentState.WAITING, AgentState.COMPLETED, Event.COMPLETE)

        # Error handling
        Transition(AgentState.RUNNING, AgentState.ERROR, Event.FAIL)

    def _advance_step(self):
        """Advance to next step"""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.context["current_step"] = self.steps[self.current_step_index]
            self.context["progress"] = (
                self.current_step_index / len(self.steps)
            )

    def get_current_step(self) -> str:
        """Get current step name"""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return "completed"


class HandoffFSM(FiniteStateMachine):
    """
    Agent Handoff State Machine
    ===========================

    Manages agent-to-agent handoffs in multi-agent systems
    """

    def __init__(self, from_agent: str, to_agent: str):
        super().__init__(AgentState.IDLE)
        self.from_agent = from_agent
        self.to_agent = to_agent
        self._setup_handoff_transitions()

    def _setup_handoff_transitions(self):
        """Setup handoff transitions"""

        # Handoff flow: IDLE -> PREPARING -> TRANSFERRING -> COMPLETED
        transitions = [
            Transition(AgentState.IDLE, AgentState.INITIALIZING, Event.START),
            Transition(AgentState.INITIALIZING, AgentState.RUNNING, Event.COMPLETE),
            Transition(AgentState.RUNNING, AgentState.WAITING, Event.USER_INPUT),
            Transition(AgentState.WAITING, AgentState.COMPLETED, Event.COMPLETE),
        ]

        self.add_transitions(transitions)

    def initiate_handoff(self, context: Dict[str, Any]) -> bool:
        """Start the handoff process"""
        self.context["handoff_context"] = context
        self.context["from"] = self.from_agent
        self.context["to"] = self.to_agent
        return self.trigger(Event.START)

    def transfer_context(self, data: Dict[str, Any]) -> bool:
        """Transfer context data to target agent"""
        self.context["transfer_data"] = data
        return self.trigger(Event.COMPLETE)

    def complete_handoff(self) -> Dict[str, Any]:
        """Complete handoff and return context"""
        self.trigger(Event.COMPLETE)
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "context": self.context
        }


# Demo runner
def run_fsm_demo():
    """Demonstrate FSM capabilities"""

    print("=" * 70)
    print("AgentOS State Management - FSM Demo")
    print("=" * 70)

    # Test Agent State Machine
    print("\n[1] Agent State Machine")
    print("-" * 40)

    agent = AgentStateMachine("agent_001")

    print(f"Initial state: {agent.current_state.value}")

    # Start agent
    result = agent.start({"task": "process_data"})
    print(f"Start result: {result}, State: {agent.current_state.value}")

    # Pause
    result = agent.pause("user_requested")
    print(f"Pause result: {result}, State: {agent.current_state.value}")

    # Resume
    result = agent.resume()
    print(f"Resume result: {result}, State: {agent.current_state.value}")

    # Complete
    result = agent.complete({"status": "success"})
    print(f"Complete result: {result}, State: {agent.current_state.value}")

    print(f"Status: {agent.get_status()}")

    # Test Workflow FSM
    print("\n[2] Workflow State Machine")
    print("-" * 40)

    workflow = WorkflowFSM("workflow_001", [
        "fetch_data",
        "process_data",
        "validate_results",
        "send_notification"
    ])

    print(f"Steps: {workflow.steps}")
    print(f"Initial: {workflow.current_state.value}")

    # Simulate workflow progression
    workflow.trigger(Event.START)
    print(f"After start: {workflow.current_state.value}, Step: {workflow.get_current_step()}")

    workflow.trigger(Event.COMPLETE)
    print(f"After complete: {workflow.current_state.value}, Step: {workflow.get_current_step()}")

    # Test Handoff FSM
    print("\n[3] Agent Handoff FSM")
    print("-" * 40)

    handoff = HandoffFSM("agent_alpha", "agent_beta")

    print(f"Handoff: {handoff.from_agent} -> {handoff.to_agent}")

    handoff.initiate_handoff({"user_id": "123", "task": "help"})
    print(f"After initiate: {handoff.current_state.value}")

    handoff.transfer_context({"session_data": "xyz"})
    print(f"After transfer: {handoff.current_state.value}")

    result = handoff.complete_handoff()
    print(f"Complete: {result['to_agent']} received context")

    print("\n" + "=" * 70)
    print("FSM demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    run_fsm_demo()