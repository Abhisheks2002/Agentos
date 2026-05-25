"""
Day 9: JSON Mode & Function Calling
====================================
Skill: Tool definition schemas
Mini Project: Swiss Army Agent

This is how AgentOS lets agents "click buttons" or "read files."
Define read_file and send_message tool in JSON schema.
"""

import json
from typing import Dict, List, Callable, Any, Optional
from pydantic import BaseModel, Field

# Tool schema definitions (OpenAI function calling format)
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the local filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The path to the file to read"
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to read",
                        "default": 100
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
                        "description": "The recipient of the message (username or agent ID)"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message content"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "default": "normal"
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
            "description": "Perform a mathematical calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_weather",
            "description": "Check the weather for a location (simulated)",
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
    """Registry for AgentOS tools"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """Register a tool"""
        self.tools[name] = func

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a tool by name"""
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}
        return self.tools[name](**kwargs)

    def get_schemas(self) -> List[Dict]:
        """Get tool schemas for LLM function calling"""
        return [s for s in TOOL_SCHEMAS if s["function"]["name"] in self.tools]

# Define tool implementations
def read_file(filepath: str, max_lines: int = 100) -> Dict:
    """Tool: Read a file"""
    try:
        with open(filepath, 'r') as f:
            lines = [f.readline() for _ in range(max_lines)]
        return {
            "success": True,
            "filepath": filepath,
            "lines_read": len(lines),
            "content": "".join(lines)
        }
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {filepath}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_message(recipient: str, message: str, priority: str = "normal") -> Dict:
    """Tool: Send a message"""
    return {
        "success": True,
        "recipient": recipient,
        "message": message,
        "priority": priority,
        "sent_at": "2024-01-01T12:00:00Z"  # In production, use actual timestamp
    }

def calculate(expression: str) -> Dict:
    """Tool: Calculate math expression"""
    try:
        # WARNING: eval is dangerous in production! Use a safe parser
        # For demo only
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "success": True,
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_weather(location: str) -> Dict:
    """Tool: Check weather (simulated)"""
    import random
    conditions = ["sunny", "cloudy", "rainy", "partly cloudy"]
    temps = range(15, 30)
    return {
        "success": True,
        "location": location,
        "condition": random.choice(conditions),
        "temperature": random.choice(temps),
        "unit": "celsius"
    }

# Create and populate the registry
def create_tool_registry() -> ToolRegistry:
    """Create the AgentOS tool registry"""
    registry = ToolRegistry()
    registry.register("read_file", read_file)
    registry.register("send_message", send_message)
    registry.register("calculate", calculate)
    registry.register("check_weather", check_weather)
    return registry

def demo():
    """Demo the Swiss Army Agent"""
    print("=" * 70)
    print("Swiss Army Agent - Function Calling Demo")
    print("=" * 70)

    registry = create_tool_registry()

    # Show available tools
    print("\nAvailable Tools:")
    for schema in registry.get_schemas():
        func = schema["function"]
        print(f"  - {func['name']}: {func['description']}")

    # Demo tool execution
    print("\n" + "-" * 70)
    print("Tool Execution Demo")
    print("-" * 70)

    # Test calculate
    result = registry.execute("calculate", expression="2 + 2")
    print(f"\ncalculate(2 + 2): {result}")

    # Test weather
    result = registry.execute("check_weather", location="San Francisco")
    print(f"\ncheck_weather('San Francisco'): {result}")

    # Test send_message
    result = registry.execute("send_message", recipient="user@example.com", message="Hello!", priority="high")
    print(f"\nsend_message: {result}")

    # Simulate LLM calling a tool
    print("\n" + "-" * 70)
    print("Simulated LLM Function Call")
    print("-" * 70)

    # This is what the LLM would generate
    llm_response = {
        "tool_calls": [
            {
                "id": "call_abc123",
                "function": {
                    "name": "calculate",
                    "arguments": '{"expression": "(10 + 5) * 2"}'
                }
            }
        ]
    }

    for call in llm_response.get("tool_calls", []):
        args = json.loads(call["function"]["arguments"])
        result = registry.execute(call["function"]["name"], **args)
        print(f"\nLLM called: {call['function']['name']}({args})")
        print(f"Result: {result}")

if __name__ == "__main__":
    demo()