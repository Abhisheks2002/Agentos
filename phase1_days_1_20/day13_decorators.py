"""
Day 13: Python Decorators & Design Patterns
=============================================
Skill: Code Cleanliness for AgentOS
Mini Project: Secure Execution Environment

Use decorators to "Log" every action an agent takes for governance.
"""

import functools
import csv
import json
from datetime import datetime
from typing import Callable, Any
from pathlib import Path

# Audit log file
AUDIT_LOG = "agentos_audit.csv"

class GovernanceLogger:
    """Logger for agent actions"""

    def __init__(self, log_file: str = AUDIT_LOG):
        self.log_file = log_file
        self._init_log()

    def _init_log(self):
        """Initialize log file with headers"""
        if not Path(self.log_file).exists():
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'agent_id', 'action', 'result', 'details'])

    def log(self, agent_id: str, action: str, result: str, details: dict = None):
        """Log an action"""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                agent_id,
                action,
                result,
                json.dumps(details or {})
            ])

def governance_check(agent_id: str = None, required_role: str = None):
    """
    Decorator that checks if an agent is authorized to execute a function.

    Usage:
        @governance_check(agent_id="AGENT-001", required_role="admin")
        def delete_file(path):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check authorization (simplified for demo)
            # In production, check against actual RBAC system

            # Log the attempt
            logger = GovernanceLogger()
            logger.log(
                agent_id=agent_id or "unknown",
                action=func.__name__,
                result="attempted",
                details={"args": str(args), "kwargs": str(kwargs)}
            )

            # Execute the function
            try:
                result = func(*args, **kwargs)
                logger.log(
                    agent_id=agent_id or "unknown",
                    action=func.__name__,
                    result="success",
                    details={}
                )
                return result
            except Exception as e:
                logger.log(
                    agent_id=agent_id or "unknown",
                    action=func.__name__,
                    result="error",
                    details={"error": str(e)}
                )
                raise

        return wrapper
    return decorator

def log_execution(func: Callable) -> Callable:
    """Simple decorator to log function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] {func.__name__} called at {datetime.now().isoformat()}")
        result = func(*args, **kwargs)
        print(f"[LOG] {func.__name__} completed")
        return result
    return wrapper

def rate_limit(max_calls: int = 10, window_seconds: int = 60):
    """Decorator to rate limit function calls"""
    calls = []

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = datetime.now().timestamp()

            # Remove old calls
            calls[:] = [t for t in calls if now - t < window_seconds]

            if len(calls) >= max_calls:
                raise Exception(f"Rate limit exceeded: {max_calls} calls per {window_seconds}s")

            calls.append(now)
            return func(*args, **kwargs)

        return wrapper
    return decorator

# Demo: Secure Execution Environment
class AgentExecutionEnvironment:
    """Safe environment where every function call is logged"""

    def __init__(self, agent_id: str, role: str = "user"):
        self.agent_id = agent_id
        self.role = role
        self.logger = GovernanceLogger()

    @governance_check(agent_id="AGENT-001", required_role="admin")
    def admin_operation(self):
        """Only admins can call this"""
        return "Admin operation completed"

    @log_execution
    @rate_limit(max_calls=5)
    def read_file(self, filepath: str):
        """Read a file with rate limiting"""
        with open(filepath, 'r') as f:
            return f.read()

    @governance_check(agent_id="AGENT-001")
    def execute_tool(self, tool_name: str, params: dict):
        """Execute a tool"""
        self.logger.log(self.agent_id, "execute_tool", "success", {"tool": tool_name})
        return {"tool": tool_name, "status": "executed"}

def demo():
    """Demo the Secure Execution Environment"""
    print("=" * 70)
    print("Secure Execution Environment - Decorator Demo")
    print("=" * 70)

    env = AgentExecutionEnvironment("AGENT-001", "admin")

    print("\n1. Testing @log_execution decorator:")
    print("-" * 50)
    try:
        content = env.read_file(__file__)
        print(f"  ✓ Successfully read {len(content)} characters")
    except FileNotFoundError:
        print("  ✗ File not found")

    print("\n2. Testing @governance_check decorator:")
    print("-" * 50)
    try:
        result = env.admin_operation()
        print(f"  ✓ {result}")
    except Exception as e:
        print(f"  ✗ {e}")

    print("\n3. Testing @rate_limit decorator:")
    print("-" * 50)
    for i in range(6):
        try:
            env.read_file(__file__)
            print(f"  Call {i+1}: OK")
        except Exception as e:
            print(f"  Call {i+1}: Rate limited! - {e}")

    print(f"\n4. Check '{AUDIT_LOG}' for logged actions")

if __name__ == "__main__":
    demo()