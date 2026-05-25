"""
Day 25: Tool Use Patterns - Building Agent Capabilities
=========================================================
Skill: Tool Integration
Mini Project: Tool-Enabled Agent

Learn patterns for integrating tools with AI agents.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import inspect


class ToolResultStatus(str, Enum):
    """Tool execution status"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    required_params: List[str] = None

    def __post_init__(self):
        if not self.required_params:
            # Auto-detect from handler signature
            sig = inspect.signature(self.handler)
            self.required_params = [
                p for p, v in sig.parameters.items()
                if v.default == inspect.Parameter.empty and p != 'self'
            ]

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate parameters"""
        for required in self.required_params:
            if required not in params:
                return False, f"Missing required parameter: {required}"
        return True, ""

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool"""
        # Validate
        valid, error = self.validate_params(params)
        if not valid:
            return {
                "status": ToolResultStatus.ERROR.value,
                "error": error
            }

        try:
            result = await self._async_execute(params)
            return {
                "status": ToolResultStatus.SUCCESS.value,
                "result": result,
                "tool": self.name
            }
        except Exception as e:
            return {
                "status": ToolResultStatus.ERROR.value,
                "error": str(e),
                "tool": self.name
            }

    async def _async_execute(self, params: Dict[str, Any]) -> Any:
        """Execute handler (handle sync/async)"""
        import asyncio
        if asyncio.iscoroutinefunction(self.handler):
            return await self.handler(**params)
        return self.handler(**params)


class ToolRegistry:
    """
    Tool Registry - Manage available tools
    ========================================
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool

    def unregister(self, name: str):
        """Unregister a tool"""
        self.tools.pop(name, None)

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters
            }
            for t in self.tools.values()
        ]

    def search(self, query: str) -> List[Tool]:
        """Search tools by name or description"""
        query_lower = query.lower()
        return [
            t for t in self.tools.values()
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]


class ToolExecutor:
    """
    Tool Executor - Execute tools with error handling
    ==================================================
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.execution_log: List[Dict[str, Any]] = []

    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool"""
        tool = self.registry.get(tool_name)

        if not tool:
            return {
                "status": ToolResultStatus.ERROR.value,
                "error": f"Tool not found: {tool_name}"
            }

        start_time = datetime.now()

        try:
            result = await tool.execute(params)

            # Log execution
            self.execution_log.append({
                "tool": tool_name,
                "params": params,
                "result": result,
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "timestamp": start_time.isoformat()
            })

            return result

        except Exception as e:
            error_result = {
                "status": ToolResultStatus.ERROR.value,
                "error": str(e),
                "tool": tool_name
            }

            self.execution_log.append({
                "tool": tool_name,
                "params": params,
                "result": error_result,
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "timestamp": start_time.isoformat()
            })

            return error_result

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_log:
            return {"total": 0}

        return {
            "total": len(self.execution_log),
            "success": len([e for e in self.execution_log if e["result"].get("status") == "success"]),
            "errors": len([e for e in self.execution_log if e["result"].get("status") == "error"]),
            "last_execution": self.execution_log[-1]["timestamp"] if self.execution_log else None
        }


class ToolUsingAgent:
    """
    Tool-Using Agent
    =================

    Agent that can use tools to accomplish tasks
    """

    def __init__(self, name: str, tool_executor: ToolExecutor):
        self.name = name
        self.tool_executor = tool_executor
        self.conversation_history: List[Dict[str, Any]] = []

    async def process(
        self,
        user_input: str,
        tools_to_use: List[str] = None
    ) -> Dict[str, Any]:
        """Process input and use tools if needed"""

        # Determine if tool should be used
        tool_calls = self._detect_tool_needs(user_input, tools_to_use)

        results = []
        for tool_call in tool_calls:
            result = await self.tool_executor.execute(
                tool_call["name"],
                tool_call["params"]
            )
            results.append(result)

        # Generate response
        if results:
            response = self._format_tool_results(results)
        else:
            response = f"[{self.name}] Direct response to: {user_input[:30]}..."

        return {
            "response": response,
            "tool_calls": tool_calls,
            "results": results
        }

    def _detect_tool_needs(
        self,
        user_input: str,
        forced_tools: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Detect which tools to use"""
        tool_calls = []

        # Forced tools
        if forced_tools:
            for tool_name in forced_tools:
                tool_calls.append({
                    "name": tool_name,
                    "params": {}
                })

        # Keyword-based detection
        user_lower = user_input.lower()

        if "search" in user_lower or "find" in user_lower:
            tool_calls.append({
                "name": "search",
                "params": {"query": user_input}
            })

        if "calculate" in user_lower or any(c in user_input for c in "+-*/"):
            tool_calls.append({
                "name": "calculate",
                "params": {"expression": user_input}
            })

        return tool_calls

    def _format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """Format tool results for response"""
        formatted = []

        for result in results:
            if result.get("status") == "success":
                formatted.append(f"✓ {result.get('result')}")
            else:
                formatted.append(f"✗ {result.get('error')}")

        return "\n".join(formatted)


# Example tools
def search_tool(query: str) -> str:
    """Search for information"""
    return f"Search results for: {query}"


def calculate_tool(expression: str) -> str:
    """Calculate expression"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def get_weather_tool(location: str) -> str:
    """Get weather for location"""
    return f"Weather in {location}: 72°F, Sunny"


# Demo
def run_demo():
    print("=" * 70)
    print("Tool Use Patterns Demo")
    print("=" * 70)

    import asyncio

    # Create registry
    registry = ToolRegistry()

    # Register tools
    registry.register(Tool(
        name="search",
        description="Search for information",
        parameters={"query": {"type": "string"}},
        handler=search_tool,
        required_params=["query"]
    ))

    registry.register(Tool(
        name="calculate",
        description="Calculate math expression",
        parameters={"expression": {"type": "string"}},
        handler=calculate_tool,
        required_params=["expression"]
    ))

    registry.register(Tool(
        name="weather",
        description="Get weather for location",
        parameters={"location": {"type": "string"}},
        handler=get_weather_tool,
        required_params=["location"]
    ))

    print(f"\nRegistered tools: {list(registry.tools.keys())}")

    # Create executor
    executor = ToolRegistry()
    tool_executor = ToolExecutor(registry)

    # Create agent
    agent = ToolUsingAgent("Assistant", tool_executor)

    # Process requests
    print("\n[1] Tool: Search")
    result = asyncio.run(agent.process("Search for Python tutorials"))
    print(f"  Response: {result['response']}")

    print("\n[2] Tool: Calculate")
    result = asyncio.run(agent.process("Calculate 2 + 2 * 3"))
    print(f"  Response: {result['response']}")

    print("\n[3] Direct Response")
    result = asyncio.run(agent.process("Hello there!"))
    print(f"  Response: {result['response']}")

    # Execution stats
    print("\n[4] Execution Stats")
    stats = tool_executor.get_stats()
    print(f"  {stats}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()