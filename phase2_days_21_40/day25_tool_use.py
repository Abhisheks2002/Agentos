"""
Day 25: Tool Use Patterns - Function Calling
=============================================
Skill: Tool Integration
Mini Project: Tool-Compatible Agent

Learn to give agents capabilities through function calling
and tool integration.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json


class ToolCallStatus(str, Enum):
    """Status of tool call"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class Tool:
    """Tool definition for agents"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable] = None

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class ToolCall:
    """A tool call request"""
    id: str
    name: str
    arguments: Dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: Any = None
    error: Optional[str] = None


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
        if name in self.tools:
            del self.tools[name]

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        """List all tools"""
        return list(self.tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for LLM"""
        return [tool.to_openai_schema() for tool in self.tools.values()]

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        if tool.handler:
            return tool.handler(**arguments)

        return f"Tool {tool_name} executed"


class ToolUseAgent:
    """
    Tool-Using Agent
    ================

    An agent that can use tools via function calling
    """

    def __init__(self, name: str, tools: ToolRegistry):
        self.name = name
        self.tools = tools
        self.conversation = []

    def prepare_messages(self, user_message: str) -> List[Dict[str, Any]]:
        """Prepare messages including tool schemas"""
        messages = [
            {"role": "system", "content": f"You are {self.name}. You have access to tools."},
        ]

        # Add tool schemas as part of system message
        tool_schemas = self.tools.get_schemas()
        if tool_schemas:
            tools_text = "\n".join([
                f"- {s['function']['name']}: {s['function']['description']}"
                for s in tool_schemas
            ])
            messages.append({
                "role": "system",
                "content": f"Available tools:\n{tools_text}"
            })

        # Add conversation history
        messages.extend(self.conversation)

        # Add current message
        messages.append({"role": "user", "content": user_message})

        return messages

    def parse_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse tool calls from LLM response"""
        tool_calls = []

        # Simple parsing - in production use proper JSON parsing
        if "TOOL_CALL:" in response:
            try:
                # Extract tool call
                call_str = response.split("TOOL_CALL:")[1].strip()
                call_data = json.loads(call_str)

                tool_calls.append(ToolCall(
                    id=f"call_{len(tool_calls)}",
                    name=call_data["name"],
                    arguments=call_data.get("arguments", {})
                ))
            except:
                pass

        return tool_calls

    async def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results"""
        results = []

        for call in tool_calls:
            call.status = ToolCallStatus.EXECUTING

            try:
                result = self.tools.execute(call.name, call.arguments)
                call.status = ToolCallStatus.SUCCESS
                call.result = result
                results.append({
                    "call_id": call.id,
                    "tool": call.name,
                    "result": result,
                    "status": "success"
                })
            except Exception as e:
                call.status = ToolCallStatus.ERROR
                call.error = str(e)
                results.append({
                    "call_id": call.id,
                    "tool": call.name,
                    "error": str(e),
                    "status": "error"
                })

        return results

    async def chat(self, user_message: str) -> str:
        """Chat with tool capabilities"""

        # Prepare messages
        messages = self.prepare_messages(user_message)

        # In production: call LLM with messages
        # response = await llm.chat(messages)

        # Simulated response
        response = f"[{self.name}] I'll help with that. Let me use a tool."

        # Check for tool usage
        tool_calls = self.parse_tool_calls(response)

        if tool_calls:
            # Execute tools
            tool_results = await self.execute_tool_calls(tool_calls)

            # Generate final response with tool results
            response += "\n\nResults:\n"
            for result in tool_results:
                response += f"- {result['tool']}: {result.get('result', result.get('error'))}\n"

        # Save to conversation
        self.conversation.append({"role": "user", "content": user_message})
        self.conversation.append({"role": "assistant", "content": response})

        return response


# Prebuilt Tools
class StandardTools:
    """Standard tools for agents"""

    @staticmethod
    def create_search_tool() -> Tool:
        def search(query: str) -> str:
            return f"Search results for: {query}"

        return Tool(
            name="search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            },
            handler=search
        )

    @staticmethod
    def create_calculator_tool() -> Tool:
        def calculate(expression: str) -> str:
            try:
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"Error: {e}"

        return Tool(
            name="calculate",
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"]
            },
            handler=calculate
        )

    @staticmethod
    def create_weather_tool() -> Tool:
        def get_weather(location: str) -> str:
            return f"Weather in {location}: 72°F, Partly Cloudy"

        return Tool(
            name="get_weather",
            description="Get current weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            },
            handler=get_weather
        )

    @staticmethod
    def create_memory_tools() -> Tuple[Tool, Tool]:
        memory_store = {}

        def remember(key: str, value: str) -> str:
            memory_store[key] = value
            return f"Remembered: {key}"

        def recall(key: str) -> str:
            return memory_store.get(key, "Not found")

        remember_tool = Tool(
            name="remember",
            description="Store information in memory",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key"},
                    "value": {"type": "string", "description": "Value to remember"}
                },
                "required": ["key", "value"]
            },
            handler=remember
        )

        recall_tool = Tool(
            name="recall",
            description="Retrieve information from memory",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key"}
                },
                "required": ["key"]
            },
            handler=recall
        )

        return remember_tool, recall_tool


from typing import Tuple


# Demo
def run_demo():
    print("=" * 70)
    print("Tool Use Patterns Demo")
    print("=" * 70)

    # Create registry
    print("\n[1] Creating Tool Registry")
    print("-" * 40)

    registry = ToolRegistry()

    # Add standard tools
    registry.register(StandardTools.create_search_tool())
    registry.register(StandardTools.create_calculator_tool())
    registry.register(StandardTools.create_weather_tool())

    remember, recall = StandardTools.create_memory_tools()
    registry.register(remember)
    registry.register(recall)

    print(f"  Registered {len(registry.list_tools())} tools:")
    for tool in registry.list_tools():
        print(f"    - {tool.name}")

    # Test execution
    print("\n[2] Executing Tools Directly")
    print("-" * 40)

    result = registry.execute("calculate", {"expression": "2 + 2 * 3"})
    print(f"  calculate(2 + 2 * 3) = {result}")

    result = registry.execute("get_weather", {"location": "San Francisco"})
    print(f"  get_weather('San Francisco') = {result}")

    # Test agent
    print("\n[3] Tool-Using Agent")
    print("-" * 40)

    agent = ToolUseAgent("Assistant", registry)

    response = "What's 15 * 15?"
    print(f"  User: {response}")

    import asyncio
    result = asyncio.run(agent.chat(response))
    print(f"  Agent: {result}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()