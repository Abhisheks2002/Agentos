"""
Day 79: Agent Behavior Prediction
===================================
Agent behavior prediction using Markov chains to forecast next actions.

Key Concepts:
- Markov chain modeling
- Transition probability matrix
- Sequence prediction
- Behavioral pattern analysis
- Action forecasting
- State prediction
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import random
import math


# Define possible agent actions
class AgentAction:
    """Represents an agent action"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    API_CALL = "api_call"
    DATABASE_QUERY = "database_query"
    SEND_NOTIFICATION = "send_notification"
    PROCESS_DATA = "process_data"
    EXECUTE_COMMAND = "execute_command"
    CALL_AGENT = "call_agent"
    WAIT = "wait"
    ERROR = "error"
    RETRY = "retry"
    COMPLETE = "complete"

    @classmethod
    def all_actions(cls) -> List[str]:
        return [
            cls.FILE_READ, cls.FILE_WRITE, cls.API_CALL,
            cls.DATABASE_QUERY, cls.SEND_NOTIFICATION, cls.PROCESS_DATA,
            cls.EXECUTE_COMMAND, cls.CALL_AGENT, cls.WAIT,
            cls.ERROR, cls.RETRY, cls.COMPLETE
        ]


@dataclass
class ActionState:
    """Represents a state in the Markov chain"""
    action: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionProbability:
    """Stores transition probabilities"""
    from_action: str
    to_action: str
    count: int = 0
    probability: float = 0.0


class MarkovChainPredictor:
    """
    Markov Chain Predictor
    =======================

    Uses Markov chains to predict next agent actions based on history.
    """

    def __init__(self, order: int = 1):
        """
        Initialize the predictor.

        Args:
            order: Order of the Markov chain (1 = first-order, 2 = second-order, etc.)
        """
        self.order = order
        self.transitions: Dict[Tuple, Counter] = defaultdict(Counter)
        self.action_counts: Counter = Counter()
        self.total_transitions: int = 0

    def add_sequence(self, actions: List[str]):
        """Add a sequence of actions to train the model"""
        # Pad sequence for order > 1
        padded_actions = [AgentAction.WAIT] * self.order + actions

        for i in range(len(padded_actions) - self.order):
            state = tuple(padded_actions[i:i + self.order])
            next_action = padded_actions[i + self.order]

            self.transitions[state][next_action] += 1
            self.action_counts[next_action] += 1
            self.total_transitions += 1

        # Also track single action counts
        for action in actions:
            self.action_counts[action] += 1

    def predict(self, context: List[str] = None) -> Optional[str]:
        """
        Predict the next action.

        Args:
            context: Recent actions to use as context

        Returns:
            Predicted next action or None
        """
        if context is None:
            context = [AgentAction.WAIT] * self.order
        else:
            # Pad or truncate context
            if len(context) < self.order:
                context = [AgentAction.WAIT] * (self.order - len(context)) + context
            elif len(context) > self.order:
                context = context[-self.order:]

        state = tuple(context)

        if state in self.transitions and self.transitions[state]:
            next_actions = self.transitions[state]
            # Return most likely action
            return next_actions.most_common(1)[0][0]

        # Fallback: return most common action
        if self.action_counts:
            return self.action_counts.most_common(1)[0][0]

        return None

    def get_probabilities(self, context: List[str] = None) -> Dict[str, float]:
        """Get probability distribution for next action"""
        if context is None:
            context = [AgentAction.WAIT] * self.order
        else:
            if len(context) < self.order:
                context = [AgentAction.WAIT] * (self.order - len(context)) + context
            elif len(context) > self.order:
                context = context[-self.order:]

        state = tuple(context)

        if state in self.transitions and self.transitions[state]:
            total = sum(self.transitions[state].values())
            return {
                action: count / total
                for action, count in self.transitions[state].items()
            }

        # Return uniform distribution over known actions
        if self.action_counts:
            total = sum(self.action_counts.values())
            return {
                action: count / total
                for action, count in self.action_counts.items()
            }

        return {}

    def get_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get full transition probability matrix"""
        matrix = defaultdict(dict)

        for state, transitions in self.transitions.items():
            from_action = state[0] if state else ""
            total = sum(transitions.values())

            for to_action, count in transitions.items():
                matrix[from_action][to_action] = count / total

        return dict(matrix)


class BehaviorPatternAnalyzer:
    """
    Behavior Pattern Analyzer
    ==========================

    Analyzes agent behavior patterns beyond simple prediction.
    """

    def __init__(self):
        self.action_sequences: List[List[str]] = []
        self.action_durations: Dict[str, List[float]] = defaultdict(list)
        self.error_patterns: List[List[str]] = []
        self.success_patterns: List[List[str]] = []

    def add_session(self, actions: List[str], duration: float = None):
        """Add a complete action session"""
        self.action_sequences.append(actions)

        if duration:
            # Estimate per-action duration
            per_action = duration / len(actions) if actions else 0
            for action in actions:
                self.action_durations[action].append(per_action)

    def get_common_sequences(self, min_length: int = 3, top_n: int = 5) -> List[Tuple[List[str], int]]:
        """Find common action sequences"""
        sequence_counts: Counter = Counter()

        for sequence in self.action_sequences:
            for length in range(min_length, len(sequence) + 1):
                for i in range(len(sequence) - length + 1):
                    seq_tuple = tuple(sequence[i:i + length])
                    sequence_counts[seq_tuple] += 1

        return sequence_counts.most_common(top_n)

    def detect_loops(self, max_length: int = 5) -> List[Tuple[List[str], int]]:
        """Detect looping behavior patterns"""
        loops = []

        for sequence in self.action_sequences:
            for length in range(2, min(max_length + 1, len(sequence) // 2 + 1)):
                for i in range(len(sequence) - length * 2 + 1):
                    pattern = sequence[i:i + length]
                    # Check if pattern repeats immediately
                    if sequence[i + length:i + length * 2] == pattern:
                        loops.append((pattern, 2))  # Appears 2+ times

        return loops

    def get_action_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each action"""
        stats = {}

        for action in AgentAction.all_actions():
            durations = self.action_durations.get(action, [])
            count = sum(1 for seq in self.action_sequences if action in seq)

            if durations:
                stats[action] = {
                    "count": count,
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                }
            else:
                stats[action] = {"count": count}

        return stats


class AgentBehaviorPredictor:
    """
    Agent Behavior Predictor
    ========================

    Complete behavior prediction system for agents.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.predictor = MarkovChainPredictor(order=2)
        self.analyzer = BehaviorPatternAnalyzer()
        self.action_history: List[ActionState] = []
        self.session_start: datetime = datetime.now()
        self.current_session: List[str] = []

    def record_action(self, action: str, metadata: Dict[str, Any] = None):
        """Record an agent action"""
        state = ActionState(
            action=action,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.action_history.append(state)
        self.current_session.append(action)

        # Update predictor periodically
        if len(self.current_session) >= 5:
            self.predictor.add_sequence(self.current_session[-5:])

    def predict_next_action(self) -> Optional[str]:
        """Predict the next action"""
        recent = [s.action for s in self.action_history[-self.predictor.order:]]
        return self.predictor.predict(recent)

    def get_prediction_confidence(self) -> float:
        """Get confidence score for current prediction"""
        recent = [s.action for s in self.action_history[-self.predictor.order:]]
        probs = self.predictor.get_probabilities(recent)

        if not probs:
            return 0.0

        # Confidence = probability of most likely action
        max_prob = max(probs.values())
        return max_prob

    def get_top_predictions(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N predicted actions with probabilities"""
        recent = [s.action for s in self.action_history[-self.predictor.order:]]
        probs = self.predictor.get_probabilities(recent)

        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        return sorted_probs[:n]

    def analyze_session(self) -> Dict[str, Any]:
        """Analyze the current session"""
        if not self.current_session:
            return {"status": "no_actions"}

        # Get common patterns
        self.analyzer.add_session(self.current_session)
        common_sequences = self.analyzer.get_common_sequences()

        # Detect errors
        errors = [s for s in self.action_history if s.action == AgentAction.ERROR]
        retries = [s for s in self.action_history if s.action == AgentAction.RETRY]

        # Calculate success rate
        completed = sum(1 for s in self.action_history if s.action == AgentAction.COMPLETE)
        total = len(self.action_history)
        success_rate = completed / total if total > 0 else 0

        return {
            "session_duration": (datetime.now() - self.session_start).total_seconds(),
            "total_actions": len(self.action_history),
            "unique_actions": len(set(s.action for s in self.action_history)),
            "errors": len(errors),
            "retries": len(retries),
            "success_rate": success_rate,
            "common_sequences": [
                {"sequence": list(seq), "count": count}
                for seq, count in common_sequences[:5]
            ],
            "prediction_confidence": self.get_prediction_confidence(),
        }

    def get_behavior_summary(self) -> Dict[str, Any]:
        """Get overall behavior summary"""
        if len(self.action_history) < 2:
            return {"status": "insufficient_data"}

        # Build prediction model from full history
        all_actions = [s.action for s in self.action_history]
        self.predictor.add_sequence(all_actions[:-1])

        # Get transition matrix
        matrix = self.predictor.get_transition_matrix()

        # Most common actions
        action_counts = Counter(all_actions)
        common_actions = action_counts.most_common(5)

        return {
            "agent_id": self.agent_id,
            "total_actions": len(self.action_history),
            "most_common_actions": common_actions,
            "transition_matrix": matrix,
            "unique_states": len(self.predictor.transitions),
            "prediction_order": self.predictor.order,
        }


class PredictiveScheduler:
    """
    Predictive Scheduler
    =====================

    Uses behavior prediction for intelligent scheduling.
    """

    def __init__(self, predictor: AgentBehaviorPredictor):
        self.predictor = predictor
        self.schedule: Dict[str, List[str]] = defaultdict(list)
        self.prediction_threshold: float = 0.7

    def predict_and_schedule(self, current_action: str) -> Optional[str]:
        """Predict next action and pre-schedule resources"""
        self.predictor.record_action(current_action)

        next_action = self.predictor.predict_next_action()
        confidence = self.predictor.get_prediction_confidence()

        if confidence >= self.prediction_threshold and next_action:
            # Pre-schedule resources for predicted action
            self.schedule[next_action].append(datetime.now())
            return next_action

        return None

    def get_resource_predictions(self) -> Dict[str, float]:
        """Predict resource needs based on action history"""
        predictions = self.predictor.get_top_predictions(5)

        # Map actions to resource weights
        resource_weights = {
            AgentAction.FILE_READ: 0.3,
            AgentAction.FILE_WRITE: 0.4,
            AgentAction.API_CALL: 0.5,
            AgentAction.DATABASE_QUERY: 0.6,
            AgentAction.PROCESS_DATA: 0.8,
            AgentAction.EXECUTE_COMMAND: 0.7,
        }

        total_weight = 0
        resource_score = 0.0

        for action, prob in predictions:
            weight = resource_weights.get(action, 0.5)
            resource_score += prob * weight
            total_weight += 1

        return {
            "cpu_prediction": resource_score * 100,
            "memory_prediction": resource_score * 80,
            "io_prediction": resource_score * 60,
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Day 79: Agent Behavior Prediction")
    print("=" * 70)

    # Create agent predictor
    print("\n[1] Agent Behavior Predictor")
    print("-" * 40)

    predictor = AgentBehaviorPredictor("agent-001")

    # Simulate agent action sequences
    # Pattern 1: Read -> Process -> Write -> API Call -> Complete
    # Pattern 2: Read -> API Call -> Database Query -> Process -> Complete

    action_sequences = [
        [
            AgentAction.FILE_READ,
            AgentAction.PROCESS_DATA,
            AgentAction.FILE_WRITE,
            AgentAction.API_CALL,
            AgentAction.COMPLETE,
        ],
        [
            AgentAction.FILE_READ,
            AgentAction.API_CALL,
            AgentAction.DATABASE_QUERY,
            AgentAction.PROCESS_DATA,
            AgentAction.COMPLETE,
        ],
        [
            AgentAction.FILE_READ,
            AgentAction.PROCESS_DATA,
            AgentAction.FILE_WRITE,
            AgentAction.API_CALL,
            AgentAction.COMPLETE,
        ],
        [
            AgentAction.API_CALL,
            AgentAction.WAIT,
            AgentAction.RETRY,
            AgentAction.API_CALL,
            AgentAction.COMPLETE,
        ],
        [
            AgentAction.DATABASE_QUERY,
            AgentAction.PROCESS_DATA,
            AgentAction.FILE_WRITE,
            AgentAction.SEND_NOTIFICATION,
            AgentAction.COMPLETE,
        ],
    ]

    # Train with sequences
    for sequence in action_sequences:
        for action in sequence:
            predictor.record_action(action)

    print(f"  Recorded {len(predictor.action_history)} actions")
    print(f"  Current session: {[s.action for s in predictor.action_history]}")

    # Make predictions
    print("\n[2] Prediction Examples")
    print("-" * 40)

    # Predict after FILE_READ
    context = [AgentAction.FILE_READ]
    predictor2 = AgentBehaviorPredictor("agent-002")
    for seq in action_sequences:
        for action in seq:
            predictor2.record_action(action)

    predictor2.predictor.add_sequence([
        AgentAction.FILE_READ,
        AgentAction.PROCESS_DATA,
        AgentAction.FILE_WRITE,
    ])

    next_action = predictor2.predict_next_action()
    print(f"  After [FILE_READ, PROCESS_DATA, FILE_WRITE]:")
    print(f"    Predicted next: {next_action}")

    # Get probabilities
    probs = predictor2.predictor.get_probabilities([
        AgentAction.FILE_READ,
        AgentAction.PROCESS_DATA,
        AgentAction.FILE_WRITE,
    ])
    print(f"    Probabilities: {dict(sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3])}")

    # Get confidence
    print(f"    Confidence: {predictor2.get_prediction_confidence():.2%}")

    # Top predictions
    print("\n[3] Top Predictions")
    print("-" * 40)

    top_preds = predictor2.get_top_predictions(3)
    print("  Top 3 predicted actions:")
    for action, prob in top_preds:
        print(f"    {action}: {prob:.1%}")

    # Behavior analysis
    print("\n[4] Session Analysis")
    print("-" * 40)

    session = predictor2.analyze_session()
    print(f"  Session duration: {session.get('session_duration', 0):.2f}s")
    print(f"  Total actions: {session.get('total_actions', 0)}")
    print(f"  Unique actions: {session.get('unique_actions', 0)}")
    print(f"  Errors: {session.get('errors', 0)}")
    print(f"  Retries: {session.get('retries', 0)}")
    print(f"  Success rate: {session.get('success_rate', 0):.1%}")

    if 'common_sequences' in session:
        print("  Common sequences:")
        for seq in session['common_sequences'][:3]:
            print(f"    {' -> '.join(seq['sequence'])} (x{seq['count']})")

    # Transition matrix
    print("\n[5] Transition Probability Matrix")
    print("-" * 40)

    summary = predictor2.get_behavior_summary()
    matrix = summary.get('transition_matrix', {})

    # Show key transitions
    print("  Key transitions:")
    for from_action, transitions in matrix.items():
        if transitions:
            top_transition = max(transitions.items(), key=lambda x: x[1])
            print(f"    {from_action} -> {top_transition[0]}: {top_transition[1]:.1%}")

    # Predictive scheduling
    print("\n[6] Predictive Scheduler")
    print("-" * 40)

    scheduler = PredictiveScheduler(predictor2)

    # Simulate scheduling
    predicted = scheduler.predict_and_schedule(AgentAction.FILE_READ)
    print(f"  After FILE_READ, pre-scheduled: {predicted}")

    predicted = scheduler.predict_and_schedule(AgentAction.PROCESS_DATA)
    print(f"  After PROCESS_DATA, pre-scheduled: {predicted}")

    # Resource predictions
    resources = scheduler.get_resource_predictions()
    print(f"\n  Resource predictions:")
    print(f"    CPU: {resources['cpu_prediction']:.1f}%")
    print(f"    Memory: {resources['memory_prediction']:.1f}%")
    print(f"    I/O: {resources['io_prediction']:.1f}%")

    # Real-time prediction demo
    print("\n[7] Real-time Prediction Demo")
    print("-" * 40)

    realtime_predictor = AgentBehaviorPredictor("realtime-agent")

    # Real-time sequence
    realtime_sequence = [
        AgentAction.FILE_READ,
        AgentAction.API_CALL,
        AgentAction.DATABASE_QUERY,
    ]

    for action in realtime_sequence:
        realtime_predictor.record_action(action)

    print(f"  Actions so far: {realtime_sequence}")
    print(f"  Next prediction: {realtime_predictor.predict_next_action()}")
    print(f"  Confidence: {realtime_predictor.get_prediction_confidence():.1%}")

    # Continue sequence
    realtime_predictor.record_action(AgentAction.PROCESS_DATA)
    print(f"\n  After adding PROCESS_DATA:")
    print(f"  Next prediction: {realtime_predictor.predict_next_action()}")
    print(f"  Confidence: {realtime_predictor.get_prediction_confidence():.1%}")

    # Loop detection
    print("\n[8] Loop Detection")
    print("-" * 40)

    loop_predictor = AgentBehaviorPredictor("loop-detector")

    # Add sequences with loops
    loop_sequences = [
        [AgentAction.API_CALL, AgentAction.WAIT, AgentAction.RETRY, AgentAction.API_CALL, AgentAction.WAIT, AgentAction.RETRY],
        [AgentAction.FILE_READ, AgentAction.WAIT, AgentAction.WAIT, AgentAction.RETRY, AgentAction.WAIT],
    ]

    for seq in loop_sequences:
        loop_predictor.analyzer.add_session(seq)

    loops = loop_predictor.analyzer.detect_loops()
    if loops:
        print("  Detected loops:")
        for pattern, count in loops:
            print(f"    {' -> '.join(pattern)} (x{count})")
    else:
        print("  No significant loops detected")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()