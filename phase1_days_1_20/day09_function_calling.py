"""
Day 9: JSON Mode & Function Calling
====================================
Skill: Tool definition schemas
Mini Project: Swiss Army Agent

This is how AgentOS lets agents "click buttons" or "read files."
Define tools in JSON schema format.
"""

from typing import Dict, List, Any, Callable, Optional
from pydantic import BaseModel, Field
import json
import math

# Tool definitions following OpenAI's function calling schema
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a file from the local filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a message to a user or another agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "The recipient of the message"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message content"
                    }
                },
                "required": ["recipient", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide", "sqrt", "power"],
                        "description": "The mathematical operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number (not needed for sqrt)"
                    }
                },
                "required": ["operation", "a"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location (simulated)",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

class ToolRegistry:
    """Registry of available tools for agents"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.definitions = []

    def register(self, name: str, func: Callable, description: str, parameters: Dict):
        """Register a tool"""
        self.tools[name] = func
        self.definitions.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        })

    def execute(self, tool_name: str, arguments: Dict) -> Any:
        """Execute a tool by name"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            return self.tools[tool_name](**arguments)
        except Exception as e:
            return {"error": str(e)}

# Implement the tool functions
def read_file_impl(filepath: str) -> Dict:
    """Simulated file reading"""
    # In production, actually read the file
    return {
        "success": True,
        "content": f"[Simulated] Contents of {filepath}",
        "lines": 10
    }

def send_message_impl(recipient: str, message: str) -> Dict:
    """Simulated message sending"""
    return {
        "success": True,
        "recipient": recipient,
        "message": message,
        "status": "sent"
    }

def calculate_impl(operation: str, a: float, b: Optional[float] = None) -> Dict:
    """Mathematical calculations"""
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero",
        "sqrt": lambda x, _: math.sqrt(x),
        "power": lambda x, y: x ** y
    }

    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}

    try:
        if operation == "sqrt":
            result = operations[operation](a, 0)
        else:
            result = operations[operation](a, b or 0)

        return {"operation": operation, "result": result, "input": {"a": a, "b": b}}
    except Exception as e:
        return {"error": str(e)}

def get_weather_impl(location: str) -> Dict:
    """Simulated weather (always returns nice weather!)"""
    return {
        "location": location,
        "temperature": 72,
        "condition": "partly cloudy",
        "humidity": 45
    }

# Create the Swiss Army Agent
def create_swiss_army_agent() -> ToolRegistry:
    """Create an agent with multiple tools"""
    registry = ToolRegistry()

    # Register all tools
    registry.register(
        "read_file",
        read_file_impl,
        "Read contents of a file",
        {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}
    )

    registry.register(
        "send_message",
        send_message_impl,
        "Send a message to a user",
        {"type": "object", "properties": {"recipient": {"type": "string"}, "message": {"type": "string"}}, "required": ["recipient", "message"]}
    )

    registry.register(
        "calculate",
        calculate_impl,
        "Perform mathematical calculations",
        {"type": "object", "properties": {"operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide", "sqrt", "power"]}, "a": {"type": "number"}, "b": {"type": "number"}}, "required": ["operation", "a"]}
    )

    registry.register(
        "get_weather",
        get_weather_impl,
        "Get weather for a location",
        {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}
    )

    return registry

def demo():
    """Demo the Swiss Army Agent"""
    print("=" * 70)
    print("Swiss Army Agent - Function Calling Demo")
    print("=" * 70)

    agent = create_swiss_army_agent()

    # Show available tools
    print("\nAvailable Tools:")
    for tool in agent.definitions:
        func = tool["function"]
        print(f"  - {func['name']}: {func['description']}")

    # Simulate tool calls (as if from LLM)
    print("\n" + "-" * 70)
    print("Tool Execution:")
    print("-" * 70)

    tool_calls = [
        ("calculate", {"operation": "add", "a": 10, "b": 5}),
        ("calculate", {"operation": "sqrt", "a": 16}),
        ("get_weather", {"location": "San Francisco"}),
        ("send_message", {"recipient": "admin@example.com", "message": "Task complete!"}),
        ("read_file", {"filepath": "/home/user/data.txt"}),
    ]

    for tool_name, args in tool_calls:
        print(f"\n>>> Calling {tool_name}({args})")
        result = agent.execute(tool_name, args)
        print(f"    Result: {result}")

if __name__ == "__main__":
    demo()