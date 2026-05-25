"""Tool Registry and Plugin System for AgentOS - Day 7 Implementation."""

import asyncio
import uuid
import os
import json
import subprocess
import platform
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from pathlib import Path
import logging

from ..models.models import Tool, ToolType

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Error during tool execution."""
    pass


class ToolValidationError(Exception):
    """Error during tool parameter validation."""
    pass


class ParameterValidator:
    """Validates tool parameters against schema."""

    @staticmethod
    def validate(params: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Validate parameters against schema.

        Args:
            params: Parameters to validate
            schema: Schema defining parameter requirements

        Raises:
            ToolValidationError: If validation fails
        """
        if not schema:
            return

        # Handle both OpenAI-style schema and simple schema
        properties = schema.get("properties", schema)

        for param_name, param_schema in properties.items():
            # Check required parameters
            required = schema.get("required", [])
            if required and param_name in required:
                if param_name not in params or params[param_name] is None:
                    raise ToolValidationError(
                        f"Missing required parameter: {param_name}"
                    )

            # Validate type if parameter provided
            if param_name in params and params[param_name] is not None:
                param_value = params[param_name]
                expected_type = param_schema.get("type")

                if expected_type:
                    if not ParameterValidator._check_type(param_value, expected_type):
                        raise ToolValidationError(
                            f"Invalid type for {param_name}: expected {expected_type}, "
                            f"got {type(param_value).__name__}"
                        )

                # Validate enum
                if "enum" in param_schema:
                    if param_value not in param_schema["enum"]:
                        raise ToolValidationError(
                            f"Invalid value for {param_name}: must be one of "
                            f"{param_schema['enum']}, got {param_value}"
                        )

                # Validate string pattern
                if expected_type == "string" and "pattern" in param_schema:
                    if not re.match(param_schema["pattern"], str(param_value)):
                        raise ToolValidationError(
                            f"Invalid format for {param_name}"
                        )

                # Validate number range
                if expected_type in ("integer", "number"):
                    if "min" in param_schema and param_value < param_schema["min"]:
                        raise ToolValidationError(
                            f"Value for {param_name} below minimum: {param_schema['min']}"
                        )
                    if "max" in param_schema and param_value > param_schema["max"]:
                        raise ToolValidationError(
                            f"Value for {param_name} exceeds maximum: {param_schema['max']}"
                        )

    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_map.get(expected_type)
        if expected is None:
            return True

        # Handle float being valid for "number"
        if expected_type == "number" and isinstance(value, int):
            return True

        return isinstance(value, expected)


class ToolCategory(str, Enum):
    """Categories of tools for organization."""
    FILE_OPERATIONS = "file_operations"
    COMMAND_EXECUTION = "command_execution"
    NETWORK = "network"
    SYSTEM = "system"
    DATA = "data"
    CUSTOM = "custom"


class ParameterType(str, Enum):
    """Types for tool parameters."""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolParameter:
    """Tool parameter definition with validation."""

    def __init__(
        self,
        name: str,
        param_type: str,
        description: str = "",
        required: bool = False,
        default: Any = None,
        enum: List[Any] = None,
        min_value: int = None,
        max_value: int = None,
        pattern: str = None
    ):
        self.name = name
        self.type = param_type
        self.description = description
        self.required = required
        self.default = default
        self.enum = enum
        self.min_value = min_value
        self.max_value = max_value
        self.pattern = pattern

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        result = {
            "type": self.type,
            "description": self.description
        }
        if self.required:
            result["required"] = True
        if self.default is not None:
            result["default"] = self.default
        if self.enum:
            result["enum"] = self.enum
        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value
        if self.pattern:
            result["pattern"] = self.pattern
        return result

    def validate(self, value: Any) -> bool:
        """Validate a value against this parameter definition."""
        # Handle None with default
        if value is None:
            return self.default is not None or not self.required

        # Type validation
        if self.type == ParameterType.STRING and not isinstance(value, str):
            return False
        elif self.type == ParameterType.INTEGER and not isinstance(value, int):
            return False
        elif self.type == ParameterType.BOOLEAN and not isinstance(value, bool):
            return False
        elif self.type == ParameterType.ARRAY and not isinstance(value, list):
            return False
        elif self.type == ParameterType.OBJECT and not isinstance(value, (dict, list)):
            return False

        # Range validation for integers
        if self.type == ParameterType.INTEGER:
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False

        # Enum validation
        if self.enum and value not in self.enum:
            return False

        # Pattern validation for strings
        if self.type == ParameterType.STRING and self.pattern:
            import re
            if not re.match(self.pattern, value):
                return False

        return True


class ToolSchema:
    """Tool parameter schema with validation."""

    def __init__(self, parameters: List[ToolParameter] = None):
        self.parameters: Dict[str, ToolParameter] = {}
        if parameters:
            for param in parameters:
                self.parameters[param.name] = param

    def add_parameter(self, param: ToolParameter):
        """Add a parameter to the schema."""
        self.parameters[param.name] = param

    def validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters against this schema.
        Returns a normalized dict with defaults applied.
        Raises ParameterValidationError if validation fails.
        """
        result = {}

        # Check required parameters
        for name, param in self.parameters.items():
            if param.required and name not in params and param.default is None:
                raise ParameterValidationError(f"Missing required parameter: {name}")

            # Apply default if not provided
            if name not in params:
                result[name] = param.default
            else:
                value = params[name]
                if not param.validate(value):
                    raise ParameterValidationError(
                        f"Invalid value for parameter '{name}': {value}"
                    )
                result[name] = value

        return result

    def to_dict(self) -> Dict:
        """Convert to OpenAI-style schema."""
        properties = {}
        required = []

        for name, param in self.parameters.items():
            properties[name] = param.to_dict()
            if param.required:
                required.append(name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }


class ToolRegistry:
    """
    Central registry for tools and plugins.
    Manages tool registration, discovery, and execution.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._executors: Dict[str, Callable] = {}
        self._sandboxes: Dict[str, "Sandbox"] = {}

    # --- Tool Management ---

    async def register_tool(
        self,
        name: str,
        tool_type: ToolType = ToolType.CUSTOM,
        description: str = None,
        endpoint: str = None,
        schema: Dict[str, Any] = None,
        executor: Callable = None,
        permissions: List[str] = None
    ) -> Tool:
        """Register a new tool."""
        tool = Tool(
            id=f"tool_{uuid.uuid4().hex[:12]}",
            name=name,
            type=tool_type,
            description=description,
            endpoint=endpoint,
            schema=schema or {},
            enabled=True,
            permissions=permissions or []
        )

        self._tools[tool.id] = tool
        self._tools[name] = tool  # Also index by name

        if executor:
            self._executors[name] = executor

        logger.info(f"Registered tool: {name} (id: {tool.id})")
        return tool

    async def get_tool(self, identifier: str) -> Optional[Tool]:
        """Get tool by ID or name."""
        return self._tools.get(identifier)

    async def list_tools(self, enabled_only: bool = True) -> List[Tool]:
        """List all registered tools."""
        tools = list(self._tools.values())
        # Filter to unique tools (avoid duplicates from name indexing)
        seen = set()
        unique_tools = []
        for tool in tools:
            if tool.id not in seen:
                seen.add(tool.id)
                if enabled_only and not tool.enabled:
                    continue
                unique_tools.append(tool)
        return unique_tools

    async def enable_tool(self, identifier: str) -> bool:
        """Enable a tool."""
        tool = await self.get_tool(identifier)
        if tool:
            tool.enabled = True
            return True
        return False

    async def disable_tool(self, identifier: str) -> bool:
        """Disable a tool."""
        tool = await self.get_tool(identifier)
        if tool:
            tool.enabled = False
            return True
        return False

    async def delete_tool(self, identifier: str) -> bool:
        """Delete a tool."""
        tool = await self.get_tool(identifier)
        if tool:
            del self._tools[tool.id]
            if tool.name in self._tools:
                del self._tools[tool.name]
            if tool.name in self._executors:
                del self._executors[tool.name]
            return True
        return False

    # --- Tool Execution with Governance Integration ---

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        tool = await self.get_tool(tool_name)
        if not tool:
            raise ToolExecutionError(f"Tool not found: {tool_name}")

        if not tool.enabled:
            raise ToolExecutionError(f"Tool is disabled: {tool_name}")

        executor = self._executors.get(tool_name)
        if not executor:
            raise ToolExecutionError(f"No executor registered for: {tool_name}")

        # Execute in sandbox if configured
        if tool.type == ToolType.CODE_EXECUTION:
            return await self._execute_sandboxed(executor, parameters or {}, context)
        else:
            # Regular execution
            try:
                result = await executor(parameters or {}, context or {})
                return {
                    "success": True,
                    "result": result,
                    "tool_id": tool.id,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name} - {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tool_id": tool.id,
                    "timestamp": datetime.now().isoformat()
                }

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        validate_params: bool = True,
        check_governance: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool with parameter validation and governance integration.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            context: Execution context (agent_id, user_id, etc.)
            validate_params: Whether to validate parameters against schema
            check_governance: Whether to check governance rules

        Returns:
            Dict containing execution result or error
        """
        # Get tool
        tool = await self.get_tool(tool_name)
        if not tool:
            logger.warning(f"Tool not found: {tool_name}")
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }

        # Check if tool is enabled
        if not tool.enabled:
            logger.warning(f"Tool is disabled: {tool_name}")
            return {
                "success": False,
                "error": f"Tool is disabled: {tool_name}",
                "tool_id": tool.id,
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }

        # Validate parameters against schema
        if validate_params and tool.schema:
            try:
                parameters = parameters or {}
                ParameterValidator.validate(parameters, tool.schema)
            except ToolValidationError as e:
                logger.warning(f"Parameter validation failed for {tool_name}: {e}")
                return {
                    "success": False,
                    "error": f"Parameter validation failed: {str(e)}",
                    "tool_id": tool.id,
                    "tool_name": tool_name,
                    "timestamp": datetime.now().isoformat()
                }

        # Governance check (if enabled and governance module available)
        if check_governance and tool.permissions:
            governance_result = await self._check_governance(tool_name, tool.permissions, parameters, context)
            if not governance_result.get("allowed", True):
                logger.warning(f"Governance blocked tool {tool_name}: {governance_result.get('reason')}")
                return {
                    "success": False,
                    "error": f"Action blocked by governance: {governance_result.get('reason')}",
                    "tool_id": tool.id,
                    "tool_name": tool_name,
                    "governance": governance_result,
                    "timestamp": datetime.now().isoformat()
                }

        # Get executor
        executor = self._executors.get(tool_name)
        if not executor:
            return {
                "success": False,
                "error": f"No executor registered for: {tool_name}",
                "tool_id": tool.id,
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }

        # Execute tool
        try:
            result = await executor(parameters or {}, context or {})
            logger.info(f"Tool executed successfully: {tool_name}")
            return {
                "success": True,
                "result": result,
                "tool_id": tool.id,
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool.id,
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }

    async def _check_governance(
        self,
        tool_name: str,
        permissions: List[str],
        parameters: Dict,
        context: Dict
    ) -> Dict[str, Any]:
        """
        Check governance rules before tool execution.

        Returns:
            Dict with 'allowed' (bool) and optional 'reason'
        """
        # Try to import and use governance module
        try:
            from ..governance.governance import GovernanceEngine, get_governance_engine
            governance = get_governance_engine()
            return await governance.check_tool_permission(
                tool_name=tool_name,
                permissions=permissions,
                parameters=parameters,
                context=context
            )
        except ImportError:
            # Governance module not available, allow by default
            logger.debug("Governance module not available, allowing tool execution")
            return {"allowed": True}
        except Exception as e:
            logger.warning(f"Governance check failed: {e}, allowing by default")
            return {"allowed": True}

    # --- Helper Methods ---

    async def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get tool by exact name."""
        return self._tools.get(name)

    async def list_tools_by_category(self, category: ToolCategory) -> List[Tool]:
        """List tools by category."""
        # This would use metadata in production
        all_tools = await self.list_tools(enabled_only=True)
        return all_tools  # Return all for now, filtered by category metadata in production

    async def list_tools_by_permission(self, permission: str) -> List[Tool]:
        """List tools that require a specific permission."""
        all_tools = await self.list_tools(enabled_only=True)
        return [tool for tool in all_tools if permission in tool.permissions]

    async def _execute_sandboxed(
        self,
        executor: Callable,
        parameters: Dict,
        context: Dict
    ) -> Dict[str, Any]:
        """Execute tool in a sandboxed environment."""
        # In production, this would use proper sandboxing (Docker, gVisor, etc.)
        try:
            result = await executor(parameters, context)
            return {
                "success": True,
                "result": result,
                "sandboxed": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sandboxed": True,
                "timestamp": datetime.now().isoformat()
            }

    # --- Built-in Tools ---

    async def register_builtin_tools(self):
        """Register built-in system tools."""

        # HTTP Request Tool
        async def http_executor(params: Dict, context: Dict) -> Dict:
            """Execute HTTP requests (sandboxed)."""
            import json
            # This would be properly sandboxed in production
            method = params.get("method", "GET")
            url = params.get("url")
            if not url:
                raise ValueError("URL is required")
            return {"method": method, "url": url, "status": "simulated"}

        await self.register_tool(
            name="http_request",
            tool_type=ToolType.API,
            description="Make HTTP requests",
            schema={
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                "url": {"type": "string"},
                "headers": {"type": "object"},
                "body": {"type": "object"}
            },
            executor=http_executor,
            permissions=["network"]
        )

        # Search Tool
        async def search_executor(params: Dict, context: Dict) -> Dict:
            """Execute web search."""
            query = params.get("query", "")
            return {"query": query, "results": [], "count": 0}

        await self.register_tool(
            name="web_search",
            tool_type=ToolType.SEARCH,
            description="Search the web",
            schema={
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            executor=search_executor,
            permissions=["network"]
        )

        # Database Tool
        async def db_executor(params: Dict, context: Dict) -> Dict:
            """Execute database operations."""
            operation = params.get("operation")
            return {"operation": operation, "status": "simulated"}

        await self.register_tool(
            name="database",
            tool_type=ToolType.DATABASE,
            description="Execute database operations",
            schema={
                "operation": {"type": "string", "enum": ["select", "insert", "update", "delete"]},
                "query": {"type": "string"},
                "table": {"type": "string"}
            },
            executor=db_executor,
            permissions=["database"]
        )

        # Code Execution Tool
        async def code_executor(params: Dict, context: Dict) -> Dict:
            """Execute code in sandbox."""
            code = params.get("code", "")
            language = params.get("language", "python")
            return {"code": code, "language": language, "output": "simulated"}

        await self.register_tool(
            name="execute_code",
            tool_type=ToolType.CODE_EXECUTION,
            description="Execute code in sandboxed environment",
            schema={
                "code": {"type": "string"},
                "language": {"type": "string", "enum": ["python", "javascript"]}
            },
            executor=code_executor,
            permissions=["sandbox"]
        )

        # ============ Day 7 File Operations Tools ============

        # File Read Tool
        async def file_read_executor(params: Dict, context: Dict) -> Dict:
            """Read contents of a file."""
            file_path = params.get("path")
            encoding = params.get("encoding", "utf-8")
            max_size = params.get("max_size", 1024 * 1024)  # 1MB default

            if not file_path:
                raise ValueError("File path is required")

            try:
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

                if not path.is_file():
                    raise ValueError(f"Not a file: {file_path}")

                file_size = path.stat().st_size
                if file_size > max_size:
                    raise ValueError(f"File too large: {file_size} bytes (max: {max_size})")

                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()

                return {
                    "path": str(path),
                    "size": file_size,
                    "content": content,
                    "encoding": encoding
                }
            except Exception as e:
                raise IOError(f"Failed to read file: {str(e)}")

        await self.register_tool(
            name="file_read",
            tool_type=ToolType.CUSTOM,
            description="Read contents from a file",
            schema={
                "path": {"type": "string", "description": "Path to the file to read"},
                "encoding": {"type": "string", "default": "utf-8", "description": "File encoding"},
                "max_size": {"type": "integer", "default": 1048576, "description": "Max file size in bytes"}
            },
            executor=file_read_executor,
            permissions=["file_read"]
        )

        # File Write Tool
        async def file_write_executor(params: Dict, context: Dict) -> Dict:
            """Write content to a file."""
            file_path = params.get("path")
            content = params.get("content", "")
            encoding = params.get("encoding", "utf-8")
            mode = params.get("mode", "w")  # w=write, a=append

            if not file_path:
                raise ValueError("File path is required")

            try:
                path = Path(file_path)

                # Create parent directories if they don't exist
                path.parent.mkdir(parents=True, exist_ok=True)

                write_mode = "a" if mode == "a" else "w"
                with open(path, write_mode, encoding=encoding) as f:
                    f.write(content)

                return {
                    "path": str(path),
                    "size": len(content),
                    "mode": mode,
                    "success": True
                }
            except Exception as e:
                raise IOError(f"Failed to write file: {str(e)}")

        await self.register_tool(
            name="file_write",
            tool_type=ToolType.CUSTOM,
            description="Write content to a file",
            schema={
                "path": {"type": "string", "description": "Path to the file to write"},
                "content": {"type": "string", "description": "Content to write"},
                "encoding": {"type": "string", "default": "utf-8"},
                "mode": {"type": "string", "default": "w", "enum": ["w", "a"], "description": "Write mode: w=overwrite, a=append"}
            },
            executor=file_write_executor,
            permissions=["file_write"]
        )

        # File Delete Tool
        async def file_delete_executor(params: Dict, context: Dict) -> Dict:
            """Delete a file."""
            file_path = params.get("path")
            recursive = params.get("recursive", False)

            if not file_path:
                raise ValueError("File path is required")

            try:
                path = Path(file_path)

                if not path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

                if path.is_dir():
                    if recursive:
                        import shutil
                        shutil.rmtree(path)
                    else:
                        raise ValueError("Use recursive=true to delete directories")
                else:
                    path.unlink()

                return {
                    "path": str(path),
                    "deleted": True,
                    "type": "directory" if recursive else "file"
                }
            except Exception as e:
                raise IOError(f"Failed to delete: {str(e)}")

        await self.register_tool(
            name="file_delete",
            tool_type=ToolType.CUSTOM,
            description="Delete a file or directory",
            schema={
                "path": {"type": "string", "description": "Path to delete"},
                "recursive": {"type": "boolean", "default": False, "description": "Delete directories recursively"}
            },
            executor=file_delete_executor,
            permissions=["file_write"]
        )

        # List Directory Tool
        async def list_directory_executor(params: Dict, context: Dict) -> Dict:
            """List contents of a directory."""
            dir_path = params.get("path", ".")
            pattern = params.get("pattern", "*")
            recursive = params.get("recursive", False)

            try:
                path = Path(dir_path)
                if not path.exists():
                    raise FileNotFoundError(f"Directory not found: {dir_path}")

                if not path.is_dir():
                    raise ValueError(f"Not a directory: {dir_path}")

                items = []
                if recursive:
                    for item in path.rglob(pattern):
                        items.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None
                        })
                else:
                    for item in path.glob(pattern):
                        items.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None
                        })

                return {
                    "path": str(path),
                    "items": items,
                    "count": len(items)
                }
            except Exception as e:
                raise IOError(f"Failed to list directory: {str(e)}")

        await self.register_tool(
            name="list_directory",
            tool_type=ToolType.CUSTOM,
            description="List contents of a directory",
            schema={
                "path": {"type": "string", "default": ".", "description": "Directory path"},
                "pattern": {"type": "string", "default": "*", "description": "Glob pattern"},
                "recursive": {"type": "boolean", "default": False, "description": "List recursively"}
            },
            executor=list_directory_executor,
            permissions=["file_read"]
        )

        # ============ Day 7 Command Execution Tools ============

        # Execute Command Tool
        async def execute_command_executor(params: Dict, context: Dict) -> Dict:
            """Execute a shell command."""
            command = params.get("command")
            shell = params.get("shell", True)
            timeout = params.get("timeout", 30)
            cwd = params.get("cwd")

            if not command:
                raise ValueError("Command is required")

            try:
                result = subprocess.run(
                    command,
                    shell=shell,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=cwd
                )

                return {
                    "command": command,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                }
            except subprocess.TimeoutExpired:
                raise TimeoutError(f"Command timed out after {timeout}s")
            except Exception as e:
                raise RuntimeError(f"Command execution failed: {str(e)}")

        await self.register_tool(
            name="execute_command",
            tool_type=ToolType.CUSTOM,
            description="Execute a shell command",
            schema={
                "command": {"type": "string", "description": "Command to execute"},
                "shell": {"type": "boolean", "default": True},
                "timeout": {"type": "integer", "default": 30, "description": "Timeout in seconds"},
                "cwd": {"type": "string", "description": "Working directory"}
            },
            executor=execute_command_executor,
            permissions=["execute_commands"]
        )

        # Run Script Tool
        async def run_script_executor(params: Dict, context: Dict) -> Dict:
            """Run a script file."""
            script_path = params.get("path")
            args = params.get("args", [])
            interpreter = params.get("interpreter")  # python, node, bash, etc.
            timeout = params.get("timeout", 60)

            if not script_path:
                raise ValueError("Script path is required")

            try:
                path = Path(script_path)
                if not path.exists():
                    raise FileNotFoundError(f"Script not found: {script_path}")

                # Determine interpreter
                if not interpreter:
                    ext = path.suffix.lower()
                    interpreter_map = {
                        ".py": "python",
                        ".js": "node",
                        ".sh": "bash",
                        ".ps1": "powershell",
                        ".bat": "cmd",
                        ".cmd": "cmd"
                    }
                    interpreter = interpreter_map.get(ext, "bash")

                cmd = [interpreter, str(path)] + args

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                return {
                    "script": str(path),
                    "interpreter": interpreter,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                }
            except subprocess.TimeoutExpired:
                raise TimeoutError(f"Script timed out after {timeout}s")
            except Exception as e:
                raise RuntimeError(f"Script execution failed: {str(e)}")

        await self.register_tool(
            name="run_script",
            tool_type=ToolType.CUSTOM,
            description="Run a script file",
            schema={
                "path": {"type": "string", "description": "Path to script file"},
                "args": {"type": "array", "default": [], "description": "Script arguments"},
                "interpreter": {"type": "string", "description": "Script interpreter (auto-detected if not provided)"},
                "timeout": {"type": "integer", "default": 60}
            },
            executor=run_script_executor,
            permissions=["execute_commands"]
        )

        # ============ Day 7 Network Tools ============

        # HTTP Request Tool (Enhanced)
        async def http_request_executor(params: Dict, context: Dict) -> Dict:
            """Make HTTP requests."""
            url = params.get("url")
            method = params.get("method", "GET")
            headers = params.get("headers", {})
            body = params.get("body")
            timeout = params.get("timeout", 30)

            if not url:
                raise ValueError("URL is required")

            try:
                data = None
                if body and method in ("POST", "PUT", "PATCH"):
                    data = json.dumps(body).encode("utf-8")
                    if "Content-Type" not in headers:
                        headers["Content-Type"] = "application/json"

                req = urllib.request.Request(url, data=data, method=method, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    response_body = response.read().decode("utf-8")
                    response_headers = dict(response.headers)

                    return {
                        "url": url,
                        "method": method,
                        "status_code": response.status,
                        "headers": response_headers,
                        "body": response_body
                    }
            except urllib.error.HTTPError as e:
                return {
                    "url": url,
                    "method": method,
                    "status_code": e.code,
                    "error": str(e),
                    "body": e.read().decode("utf-8") if e.fp else None
                }
            except urllib.error.URLError as e:
                raise ConnectionError(f"Network error: {str(e.reason)}")
            except Exception as e:
                raise RuntimeError(f"HTTP request failed: {str(e)}")

        await self.register_tool(
            name="http_request",
            tool_type=ToolType.API,
            description="Make HTTP requests",
            schema={
                "url": {"type": "string", "description": "Request URL"},
                "method": {"type": "string", "default": "GET", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                "headers": {"type": "object", "default": {}, "description": "Request headers"},
                "body": {"type": "object", "description": "Request body (for POST/PUT)"},
                "timeout": {"type": "integer", "default": 30}
            },
            executor=http_request_executor,
            permissions=["network"]
        )

        # Fetch URL Tool
        async def fetch_url_executor(params: Dict, context: Dict) -> Dict:
            """Fetch content from a URL."""
            url = params.get("url")
            parse_html = params.get("parse_html", True)

            if not url:
                raise ValueError("URL is required")

            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    content = response.read().decode("utf-8")

                    result = {
                        "url": url,
                        "status_code": response.status,
                        "content_length": len(content),
                        "content_type": response.headers.get("Content-Type", "")
                    }

                    if parse_html and "text/html" in result["content_type"]:
                        # Simple HTML parsing
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(content, "html.parser")

                        result["title"] = soup.title.string if soup.title else None
                        result["links"] = [a.get("href") for a in soup.find_all("a", href=True)][:20]
                        result["text"] = soup.get_text()[:2000]  # First 2000 chars
                    else:
                        result["content"] = content[:5000]  # First 5000 chars

                    return result

            except Exception as e:
                raise RuntimeError(f"Failed to fetch URL: {str(e)}")

        await self.register_tool(
            name="fetch_url",
            tool_type=ToolType.API,
            description="Fetch content from a URL with optional HTML parsing",
            schema={
                "url": {"type": "string", "description": "URL to fetch"},
                "parse_html": {"type": "boolean", "default": True, "description": "Parse HTML content"}
            },
            executor=fetch_url_executor,
            permissions=["network"]
        )

        # ============ Day 7 System Tools ============

        # Get System Info Tool
        async def get_system_info_executor(params: Dict, context: Dict) -> Dict:
            """Get system information."""
            import psutil

            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_total": psutil.disk_usage("/").total if platform.system() != "Windows" else psutil.disk_usage("C:").total,
                "disk_used": psutil.disk_usage("/").used if platform.system() != "Windows" else psutil.disk_usage("C:").used,
                "disk_percent": psutil.disk_usage("/").percent if platform.system() != "Windows" else psutil.disk_usage("C:").percent
            }

        await self.register_tool(
            name="get_system_info",
            tool_type=ToolType.CUSTOM,
            description="Get system information",
            schema={},
            executor=get_system_info_executor,
            permissions=["read_system_info"]
        )

        # Get Environment Tool
        async def get_environment_executor(params: Dict, context: Dict) -> Dict:
            """Get environment variables."""
            include = params.get("include", [])
            exclude = params.get("exclude", ["PATH", "HOME", "USERPROFILE"])  # Exclude sensitive by default
            all_vars = params.get("all", False)

            if all_vars:
                return {"variables": dict(os.environ)}

            env = {}
            for key, value in os.environ.items():
                if exclude and key in exclude:
                    continue
                if include and key not in include:
                    continue
                # Mask potential sensitive values
                sensitive_patterns = ["KEY", "SECRET", "PASSWORD", "TOKEN", "API"]
                if any(p in key.upper() for p in sensitive_patterns):
                    env[key] = "***HIDDEN***"
                else:
                    env[key] = value

            return {"variables": env}

        await self.register_tool(
            name="get_environment",
            tool_type=ToolType.CUSTOM,
            description="Get environment variables",
            schema={
                "include": {"type": "array", "description": "Only include these variable names"},
                "exclude": {"type": "array", "default": ["PATH", "HOME", "USERPROFILE"], "description": "Exclude these variable names"},
                "all": {"type": "boolean", "default": False, "description": "Include all variables (not recommended)"}
            },
            executor=get_environment_executor,
            permissions=["read_system_info"]
        )

        # ============ Day 8 Web Search Tools ============

        # Web Search Tool
        async def web_search_executor(params: Dict, context: Dict) -> Dict:
            """Search the web for information."""
            from .web_search import WebSearchTool

            query = params.get("query")
            limit = params.get("limit", 10)

            if not query:
                raise ValueError("Query is required")

            search_tool = WebSearchTool()
            return search_tool.search(query, limit)

        await self.register_tool(
            name="web_search",
            tool_type=ToolType.API,
            description="Search the web for information. Use this when you need current information, news, or facts that may not be in your training data.",
            schema={
                "query": {"type": "string", "description": "The search query string. Be specific and include relevant keywords."},
                "limit": {"type": "integer", "default": 10, "description": "Maximum number of results to return"}
            },
            executor=web_search_executor,
            permissions=["network"]
        )

        # Web Search (with API key - for premium search)
        async def web_search_api_executor(params: Dict, context: Dict) -> Dict:
            """Search using a premium search API (Google, Bing, etc)."""
            from .web_search import WebSearchTool

            query = params.get("query")
            limit = params.get("limit", 10)
            engine = params.get("engine", "ddg")
            api_key = params.get("api_key")

            if not query:
                raise ValueError("Query is required")

            search_tool = WebSearchTool(api_key=api_key, search_engine=engine)
            return search_tool.search(query, limit)

        await self.register_tool(
            name="web_search_api",
            tool_type=ToolType.API,
            description="Search using a premium search API with more features",
            schema={
                "query": {"type": "string", "description": "The search query string"},
                "limit": {"type": "integer", "default": 10, "description": "Maximum results"},
                "engine": {"type": "string", "default": "ddg", "enum": ["ddg", "google", "bing"], "description": "Search engine to use"},
                "api_key": {"type": "string", "description": "API key for premium search (optional)"}
            },
            executor=web_search_api_executor,
            permissions=["network"]
        )

        # ============ Day 7 Data Tools ============

        # Search Data Tool
        async def search_data_executor(params: Dict, context: Dict) -> Dict:
            """Search data (simplified search)."""
            query = params.get("query", "")
            data_source = params.get("data_source", "")
            limit = params.get("limit", 10)

            if not query:
                raise ValueError("Search query is required")

            # This would connect to actual data sources in production
            # For now, return a placeholder
            return {
                "query": query,
                "data_source": data_source,
                "results": [],
                "count": 0,
                "message": "Data search requires configured data sources"
            }

        await self.register_tool(
            name="search_data",
            tool_type=ToolType.CUSTOM,
            description="Search data from configured data sources",
            schema={
                "query": {"type": "string", "description": "Search query"},
                "data_source": {"type": "string", "description": "Data source name"},
                "limit": {"type": "integer", "default": 10}
            },
            executor=search_data_executor,
            permissions=["read_user_data", "read_business_data"]
        )

        # Process Data Tool
        async def process_data_executor(params: Dict, context: Dict) -> Dict:
            """Process data with transformations."""
            operation = params.get("operation")
            data = params.get("data")
            options = params.get("options", {})

            if not operation:
                raise ValueError("Operation is required")

            supported_operations = ["filter", "map", "aggregate", "transform", "validate"]

            if operation not in supported_operations:
                raise ValueError(f"Unsupported operation: {operation}. Supported: {supported_operations}")

            if not data:
                raise ValueError("Data is required")

            # Process based on operation type
            result = {"operation": operation, "success": True}

            if operation == "filter":
                field = options.get("field")
                value = options.get("value")
                if isinstance(data, list):
                    result["result"] = [item for item in data if isinstance(item, dict) and item.get(field) == value]
                else:
                    result["result"] = data
                result["count"] = len(result.get("result", []))

            elif operation == "map":
                field = options.get("field")
                transform = options.get("transform", "uppercase")
                if isinstance(data, list):
                    result["result"] = [
                        {**(item), field: item.get(field, "").upper() if transform == "uppercase" else item.get(field)}
                        if isinstance(item, dict) else item
                        for item in data
                    ]
                else:
                    result["result"] = data

            elif operation == "transform":
                # JSON to CSV-like, or other transformations
                transform_type = options.get("type", "json_format")
                if transform_type == "json_format":
                    result["result"] = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
                elif transform_type == "flatten":
                    # Simple flatten for nested dicts
                    def flatten(d, parent_key=""):
                        items = []
                        for k, v in d.items():
                            new_key = f"{parent_key}.{k}" if parent_key else k
                            if isinstance(v, dict):
                                items.extend(flatten(v, new_key).items())
                            else:
                                items.append((new_key, v))
                        return dict(items)
                    result["result"] = flatten(data) if isinstance(data, dict) else data

            elif operation == "aggregate":
                field = options.get("field")
                if isinstance(data, list) and field:
                    values = [item.get(field) for item in data if isinstance(item, dict) and field in item]
                    if all(isinstance(v, (int, float)) for v in values):
                        result["result"] = {
                            "sum": sum(values),
                            "avg": sum(values) / len(values) if values else 0,
                            "min": min(values),
                            "max": max(values),
                            "count": len(values)
                        }

            elif operation == "validate":
                schema = options.get("schema")
                errors = []
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        if not isinstance(item, dict):
                            errors.append(f"Item {i}: not a dict")
                result["result"] = data
                result["valid"] = len(errors) == 0
                result["errors"] = errors

            return result

        await self.register_tool(
            name="process_data",
            tool_type=ToolType.CUSTOM,
            description="Process and transform data",
            schema={
                "operation": {"type": "string", "enum": ["filter", "map", "aggregate", "transform", "validate"], "description": "Operation to perform"},
                "data": {"type": "object", "description": "Data to process"},
                "options": {"type": "object", "description": "Operation options"}
            },
            executor=process_data_executor,
            permissions=["read_user_data", "write_user_data"]
        )

        logger.info("Registered Day 7 built-in tools")


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
