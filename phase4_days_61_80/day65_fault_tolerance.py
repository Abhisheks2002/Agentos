"""
Day 65: Fault Tolerance and Error Recovery
===========================================
Building resilient agents that can recover from failures.

Key Concepts:
- Error detection
- Retry strategies
- Circuit breakers
- Fallback mechanisms
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import random


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class ErrorEvent:
    """An error event"""
    error_id: str
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


class CircuitBreaker:
    """
    Circuit Breaker
    ===============

    Prevents cascading failures by opening circuit after threshold.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: Optional[datetime] = None

    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False

        # Half-open - allow one request
        return True

    def record_success(self):
        """Record a successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            self.failure_count = 0

    def record_failure(self):
        """Record a failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class FaultTolerantAgent:
    """
    Fault Tolerant Agent
    ====================

    Agent with fault tolerance and error recovery.
    """

    def __init__(
        self,
        agent_id: str,
        retry_config: RetryConfig = None,
        circuit_breaker: CircuitBreaker = None
    ):
        self.agent_id = agent_id
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.error_history: List[ErrorEvent] = []

    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        fallback: Callable = None,
        **kwargs
    ) -> Any:
        """Execute operation with retry logic"""
        last_error = None

        for attempt in range(self.retry_config.max_attempts):
            try:
                # Check circuit breaker
                if not self.circuit_breaker.can_execute():
                    if fallback:
                        return await fallback(*args, **kwargs)
                    raise Exception("Circuit breaker is open")

                # Execute operation
                result = await operation(*args, **kwargs)

                # Record success
                self.circuit_breaker.record_success()

                return result

            except Exception as e:
                last_error = e
                self.circuit_breaker.record_failure()

                # Log error
                self._log_error(
                    str(type(e).__name__),
                    str(e),
                    ErrorSeverity.MEDIUM,
                    {"attempt": attempt + 1}
                )

                # Wait before retry
                if attempt < self.retry_config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)

        # All retries failed
        if fallback:
            return await fallback(*args, **kwargs)

        raise last_error

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        delay = min(
            self.retry_config.initial_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )

        if self.retry_config.jitter:
            delay *= (0.5 + random.random())

        return delay

    def _log_error(
        self,
        error_type: str,
        message: str,
        severity: ErrorSeverity,
        context: Dict[str, Any]
    ):
        """Log an error event"""
        event = ErrorEvent(
            error_id=f"err_{len(self.error_history)}",
            error_type=error_type,
            message=message,
            severity=severity,
            timestamp=datetime.now(),
            context=context
        )
        self.error_history.append(event)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        by_severity = {}
        for event in self.error_history:
            key = event.severity.value
            by_severity[key] = by_severity.get(key, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "by_severity": by_severity,
            "circuit_state": self.circuit_breaker.get_state()
        }


# Demo
async def main():
    print("=" * 60)
    print("Day 65: Fault Tolerance and Error Recovery")
    print("=" * 60)

    agent = FaultTolerantAgent("agent_001")

    # Test operation that fails sometimes
    attempt_count = 0

    async def unstable_operation(x):
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise ValueError(f"Attempt {attempt_count} failed")

        return x * 2

    async def fallback_operation(x):
        return f"Fallback: {x * 3}"

    # Execute with retry
    print("\nExecuting with retry...")
    try:
        result = await agent.execute_with_retry(
            unstable_operation,
            5,
            fallback=fallback_operation
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Final error: {e}")

    # Circuit breaker demo
    print("\n" + "-" * 40)
    print("Circuit Breaker Demo:")

    cb = CircuitBreaker(failure_threshold=3)

    for i in range(10):
        can_exec = cb.can_execute()
        print(f"  Attempt {i+1}: {'Allowed' if can_exec else 'Blocked'} (State: {cb.state.value})")

        if can_exec:
            if i < 4:
                cb.record_failure()
            else:
                cb.record_success()

    # Error summary
    print("\n" + "-" * 40)
    summary = agent.get_error_summary()
    print(f"Total errors: {summary['total_errors']}")
    print(f"Circuit state: {summary['circuit_state']['state']}")


if __name__ == "__main__":
    asyncio.run(main())