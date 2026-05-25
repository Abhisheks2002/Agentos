"""
Day 42: Function Tools - Building Agent Capabilities
======================================================
Skill: Tool Development
Mini Project: Custom Tool Library

Build custom tools that agents can use to extend their capabilities.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import inspect


class ToolCategory(str, Enum):
    """Tool categories"""
    DATA = "data"
    COMPUTATION = "computation"
    EXTERNAL = "external"
    UTILITY = "utility"


@dataclass
class ToolSpec:
    """Tool specification"""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    examples: List[Dict[str, str]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class BaseTool:
    """Base class for tools"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def execute(self, **kwargs) -> Any:
        """Execute the tool"""
        raise NotImplementedError

    def get_spec(self) -> ToolSpec:
        """Get tool specification"""
        return ToolSpec(
            name=self.name,
            description=self.description,
            category=ToolCategory.UTILITY,
            parameters={},
            returns={}
        )


class DataTool(BaseTool):
    """Tool for data operations"""

    async def execute(self, **kwargs) -> Any:
        data = kwargs.get("data", [])
        operation = kwargs.get("operation", "count")

        if operation == "count":
            return len(data)
        elif operation == "sum":
            return sum(data)
        elif operation == "avg":
            return sum(data) / len(data) if data else 0
        elif operation == "unique":
            return list(set(data))
        elif operation == "sort":
            return sorted(data, reverse=kwargs.get("reverse", False))

        return data


class WebTool(BaseTool):
    """Tool for web operations"""

    async def execute(self, **kwargs) -> Any:
        url = kwargs.get("url", "")
        method = kwargs.get("method", "GET")

        # Simulate web request
        return {
            "url": url,
            "method": method,
            "status": 200,
            "data": f"Response from {url}"
        }


class SearchTool(BaseTool):
    """Tool for searching"""

    async def execute(self, **kwargs) -> Any:
        query = kwargs.get("query", "")
        engine = kwargs.get("engine", "web")

        # Simulate search
        results = [
            {"title": f"Result 1 for {query}", "url": "http://example.com/1"},
            {"title": f"Result 2 for {query}", "url": "http://example.com/2"},
            {"title": f"Result 3 for {query}", "url": "http://example.com/3"},
        ]

        return {
            "query": query,
            "engine": engine,
            "results": results,
            "count": len(results)
        }


class CalculatorTool(BaseTool):
    """Tool for calculations"""

    async def execute(self, **kwargs) -> Any:
        expression = kwargs.get("expression", "")

        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return {"result": result, "valid": True}
        except Exception as e:
            return {"error": str(e), "valid": False}


class FileTool(BaseTool):
    """Tool for file operations"""

    async def execute(self, **kwargs) -> Any:
        operation = kwargs.get("operation", "read")
        path = kwargs.get("path", "")

        if operation == "read":
            return {"content": f"Content of {path}", "exists": True}
        elif operation == "write":
            content = kwargs.get("content", "")
            return {"success": True, "written": len(content)}
        elif operation == "exists":
            return {"exists": True}
        elif operation == "list":
            return {"files": ["file1.txt", "file2.py", "data.json"]}

        return {}


class ToolBuilder:
    """
    Tool Builder - Create tools from functions
    ===========================================
    """

    @staticmethod
    def from_function(func: Callable) -> BaseTool:
        """Create tool from function"""

        name = func.__name__
        description = func.__doc__ or "No description"

        class FunctionTool(BaseTool):
            async def execute(self, **kwargs):
                return func(**kwargs)

        return FunctionTool(name, description)


class ToolManager:
    """
    Tool Manager - Manage tool collection
    ======================================
    """

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.usage_stats: Dict[str, int] = {}

    def register(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.name] = tool
        self.usage_stats[tool.name] = 0

    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(name)

    async def execute(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool"""
        tool = self.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        result = await tool.execute(**kwargs)

        # Track usage
        self.usage_stats[tool_name] += 1

        return result

    def list_tools(self) -> List[ToolSpec]:
        """List all tool specifications"""
        return [tool.get_spec() for tool in self.tools.values()]

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_tools": len(self.tools),
            "total_uses": sum(self.usage_stats.values()),
            "by_tool": self.usage_stats.copy()
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Function Tools Demo")
    print("=" * 70)

    import asyncio

    # Create tool manager
    manager = ToolManager()

    # Register tools
    manager.register(DataTool("data", "Process data operations"))
    manager.register(WebTool("web", "Make web requests"))
    manager.register(SearchTool("search", "Search the web"))
    manager.register(CalculatorTool("calc", "Perform calculations"))
    manager.register(FileTool("file", "File operations"))

    print(f"\nRegistered tools: {list(manager.tools.keys())}")

    # Execute tools
    print("\n[1] Data Tool")
    result = asyncio.run(manager.execute("data", data=[1, 2, 3, 4, 5], operation="avg"))
    print(f"  Average: {result}")

    print("\n[2] Calculator Tool")
    result = asyncio.run(manager.execute("calc", expression="2 + 2 * 3"))
    print(f"  Result: {result}")

    print("\n[3] Search Tool")
    result = asyncio.run(manager.execute("search", query="Python"))
    print(f"  Found: {result['count']} results")

    print("\n[4] Usage Stats")
    stats = manager.get_stats()
    print(f"  {stats}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()