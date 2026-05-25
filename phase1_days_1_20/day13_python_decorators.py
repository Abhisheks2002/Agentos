"""
Day 13: Python Decorators & Design Patterns
============================================
Skill: Code Cleanliness for AgentOS
Mini Project: Secure Execution Environment

Use decorators to "Log" every action an agent takes for governance.
@governance_check decorator checks if a function is "authorized."
"""

import functools
import csv
import os
from datetime import datetime
from typing import Callable, Any, List

# Log file for audit
LOG_FILE = "agentos_audit_log.csv"

class AuditLogger:
    """Audit logger for AgentOS actions"""

    def __init__(self, log_file: str = LOG_FILE):
        self.log_file = log_file
        self._init_log()

    def _init_log(self):
        """Initialize log file with headers"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'agent_id', 'action', 'function', 'result', 'duration_ms'])

    def log(self, agent_id: str, action: str, function: str, result: str, duration_ms: float):
        """Log an action"""
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                agent_id,
                action,
                function,
                result,
                round(duration_ms, 2)
            ])

def governance_check(allowed_roles: List[str] = None):
    """
    Decorator to check if agent has permission to execute a function.

    Usage:
        @governance_check(allowed_roles=['admin', 'user'])
        def delete_file(filepath):
            ...
    """
    if allowed_roles is None:
        allowed_roles = ['admin']

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get agent info from context (simulated)
            agent_id = kwargs.get('agent_id', 'unknown')
            agent_role = kwargs.get('agent_role', 'guest')

            # Check role
            if agent_role not in allowed_roles:
                result = f"ACCESS DENIED: Role '{agent_role}' not allowed. Required: {allowed_roles}"
                print(f"[GOVERNANCE] {agent_id}: {result}")
                return {"success": False, "error": result}

            # Execute function
            return func(*args, **kwargs)

        return wrapper
    return decorator

def log_action(action_name: str = None):
    """
    Decorator to log all function calls.

    Usage:
        @log_action("read_file")
        def read_file(filepath):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            agent_id = kwargs.get('agent_id', 'system')
            action = action_name or func.__name__

            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000

                # Log success
                logger = AuditLogger()
                logger.log(agent_id, "SUCCESS", action, str(result)[:50], duration)

                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000

                # Log error
                logger = AuditLogger()
                logger.log(agent_id, "ERROR", action, str(e), duration)

                return {"success": False, "error": str(e)}

        return wrapper
    return decorator

# Demo functions using decorators
@log_action("agent_read")
@governance_check(allowed_roles=['admin', 'user', 'guest'])
def read_file(filepath: str, agent_id: str = "unknown", agent_role: str = "guest") -> dict:
    """Read a file (simulated)"""
    # In production, actually read the file
    return {
        "success": True,
        "filepath": filepath,
        "content": f"[Content of {filepath}]"
    }

@log_action("agent_delete")
@governance_check(allowed_roles=['admin'])
def delete_file(filepath: str, agent_id: str = "unknown", agent_role: str = "guest") -> dict:
    """Delete a file (requires admin)"""
    return {
        "success": True,
        "action": "deleted",
        "filepath": filepath
    }

@log_action("agent_exec")
@governance_check(allowed_roles=['admin', 'user'])
def execute_command(command: str, agent_id: str = "unknown", agent_role: str = "guest") -> dict:
    """Execute a command"""
    return {
        "success": True,
        "command": command,
        "output": "Command executed successfully"
    }

def demo():
    """Demo the Secure Execution Environment"""
    print("=" * 70)
    print("Secure Execution Environment - Decorator Demo")
    print("=" * 70)

    # Test with different roles
    test_cases = [
        {"agent_id": "agent_001", "agent_role": "admin", "action": "read_file", "filepath": "/data/file.txt"},
        {"agent_id": "agent_002", "agent_role": "user", "action": "read_file", "filepath": "/data/file.txt"},
        {"agent_id": "agent_003", "agent_role": "guest", "action": "delete_file", "filepath": "/data/file.txt"},
        {"agent_id": "agent_004", "agent_role": "admin", "action": "delete_file", "filepath": "/data/file.txt"},
    ]

    for tc in test_cases:
        print(f"\n{tc['agent_id']} ({tc['agent_role']}) attempting {tc['action']}")
        print("-" * 50)

        if tc['action'] == "read_file":
            result = read_file(tc['filepath'], agent_id=tc['agent_id'], agent_role=tc['agent_role'])
        elif tc['action'] == "delete_file":
            result = delete_file(tc['filepath'], agent_id=tc['agent_id'], agent_role=tc['agent_role'])

        print(f"Result: {result}")

    print("\n" + "=" * 70)
    print(f"Audit log written to: {LOG_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    demo()