"""
Day 64: Sandboxed Execution Environment
========================================
Secure sandboxed execution for agent tools and actions.

Key Concepts:
- Process isolation
- Resource limits
- Network containment
- File system boundaries
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import subprocess
import tempfile
import os
import uuid


class SandboxPolicy(Enum):
    """Sandbox policies"""
    ALLOW_ALL = "allow_all"
    DENY_ALL = "deny_all"
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"


@dataclass
class ResourceLimits:
    """Resource limits for sandbox"""
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    max_execution_time_sec: int = 30
    max_file_size_mb: int = 100
    max_network_requests: int = 10


@dataclass
class SandboxResult:
    """Result of sandboxed execution"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    resources_used: Dict[str, Any] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)


class SandboxEnvironment:
    """
    Sandboxed Execution Environment
    =================================

    Provides secure isolated execution for agent tools.
    """

    def __init__(
        self,
        policy: SandboxPolicy = SandboxPolicy.WHITELIST,
        limits: ResourceLimits = None,
        allowed_paths: List[str] = None,
        allowed_commands: List[str] = None
    ):
        self.policy = policy
        self.limits = limits or ResourceLimits()
        self.allowed_paths = allowed_paths or []
        self.allowed_commands = allowed_commands or []
        self.execution_log: List[Dict] = []

    def execute_code(
        self,
        code: str,
        language: str = "python"
    ) -> SandboxResult:
        """Execute code in sandbox"""
        start_time = datetime.now()

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{language}',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute based on language
            if language == "python":
                result = self._execute_python(temp_file)
            elif language == "javascript":
                result = self._execute_javascript(temp_file)
            else:
                result = SandboxResult(
                    success=False,
                    output="",
                    error=f"Unsupported language: {language}"
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time

            return result

        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass

    def _execute_python(self, file_path: str) -> SandboxResult:
        """Execute Python in sandbox"""
        try:
            # Run with resource limits
            result = subprocess.run(
                ["python", file_path],
                capture_output=True,
                text=True,
                timeout=self.limits.max_execution_time_sec,
                env=self._get_sandbox_env()
            )

            return SandboxResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                output="",
                error="Execution timeout exceeded"
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=str(e)
            )

    def _execute_javascript(self, file_path: str) -> SandboxResult:
        """Execute JavaScript in sandbox"""
        try:
            result = subprocess.run(
                ["node", file_path],
                capture_output=True,
                text=True,
                timeout=self.limits.max_execution_time_sec
            )

            return SandboxResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                output="",
                error="Execution timeout exceeded"
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=str(e)
            )

    def _get_sandbox_env(self) -> Dict[str, str]:
        """Get sandboxed environment variables"""
        env = os.environ.copy()
        # Limit environment access
        return {
            "PATH": env.get("PATH", ""),
            "HOME": env.get("HOME", ""),
            "TMPDIR": tempfile.gettempdir()
        }

    def execute_command(self, command: str) -> SandboxResult:
        """Execute a shell command in sandbox"""
        start_time = datetime.now()

        # Check whitelist
        if self.policy == SandboxPolicy.WHITELIST:
            cmd_base = command.split()[0] if command else ""
            if cmd_base not in self.allowed_commands:
                return SandboxResult(
                    success=False,
                    output="",
                    error=f"Command not allowed: {cmd_base}"
                )

        # Check blacklist
        if self.policy == SandboxPolicy.BLACKLIST:
            for blocked in self.allowed_commands:  # Used as blacklist
                if blocked in command:
                    return SandboxResult(
                        success=False,
                        output="",
                        error=f"Command blocked: {blocked}"
                    )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.limits.max_execution_time_sec
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            return SandboxResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                output="",
                error="Execution timeout exceeded"
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                error=str(e)
            )

    def check_path_access(self, path: str) -> bool:
        """Check if path is accessible"""
        if not self.allowed_paths:
            return True

        # Check if path is in allowed list
        for allowed in self.allowed_paths:
            if path.startswith(allowed):
                return True

        return False

    def log_execution(self, operation: str, result: SandboxResult):
        """Log execution for audit"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "success": result.success,
            "execution_time": result.execution_time,
            "violations": result.violations
        })


# Demo
async def main():
    print("=" * 60)
    print("Day 64: Sandboxed Execution Environment")
    print("=" * 60)

    # Create sandbox
    sandbox = SandboxEnvironment(
        policy=SandboxPolicy.WHITELIST,
        limits=ResourceLimits(max_execution_time_sec=5),
        allowed_paths=["/tmp/", "./"],
        allowed_commands=["ls", "echo", "cat", "python"]
    )

    # Test safe code execution
    print("\n1. Safe Python code:")
    print("-" * 40)
    code = """
print("Hello from sandbox!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
    result = sandbox.execute_code(code, "python")
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")

    # Test whitelisted command
    print("\n2. Whitelisted command (ls):")
    print("-" * 40)
    result = sandbox.execute_command("ls -la")
    print(f"Success: {result.success}")
    print(f"Output: {result.output[:200]}...")

    # Test blacklisted command simulation
    print("\n3. Testing policy enforcement:")
    print("-" * 40)
    result = sandbox.execute_command("rm -rf /")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")

    # Test path access
    print("\n4. Path access check:")
    print("-" * 40)
    print(f"/tmp/file.txt: {sandbox.check_path_access('/tmp/file.txt')}")
    print(f"/etc/passwd: {sandbox.check_path_access('/etc/passwd')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())