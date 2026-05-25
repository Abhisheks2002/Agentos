"""
Day 20: Phase 1 Review - Mini-AgentOS CLI
==========================================
Mini Project: Build a complete CLI Agent

This combines all skills from Days 1-19:
- Python async basics
- OpenAI API integration
- Vector database for memory
- Function calling
- FastAPI gateway
- WebSocket communication
- Evaluation & Testing
- Multi-modal support
- State management
- Security

A complete agent you can interact with via CLI!
"""

import asyncio
import sys
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os

# Import our previous implementations
from day14_fastapi_gateway import app as fastapi_app
from day15_websockets import manager as ws_manager
from day18_state_management import AgentStateMachine, AgentState, Event
from day19_security_basics import SecureConfig, AgentAuth

# Note: Run with: python day20_mini_agentos.py


@dataclass
class Agent:
    """Mini AgentOS Agent"""
    id: str
    name: str
    personality: str
    system_prompt: str
    created_at: str
    memory: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Message:
    """Chat message"""
    role: str  # user, assistant, system
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MiniAgentOS:
    """
    Mini-AgentOS CLI
    =================

    A complete AI agent with:
    - Personality configuration
    - Memory (vector store simulation)
    - Tool calling
    - Logging (decorators)
    - State management
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.config = SecureConfig()
        self.auth = AgentAuth()
        self._setup_tools()

    def _setup_tools(self):
        """Define available tools for agents"""
        self.tools = [
            {
                "name": "search_memory",
                "description": "Search the agent's memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "remember",
                "description": "Store a memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "What to remember"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "calculate",
                "description": "Perform a calculation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression"}
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "get_time",
                "description": "Get current time",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_tools",
                "description": "List available tools",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def create_agent(
        self,
        name: str,
        personality: str,
        system_prompt: str = None
    ) -> Agent:
        """Create a new agent"""
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        if not system_prompt:
            system_prompt = f"""You are {name}, {personality}.
You are a helpful AI assistant with memory capabilities.
You can use tools to search your memory, calculate, and get the time.
Always be helpful and concise."""

        agent = Agent(
            id=agent_id,
            name=name,
            personality=personality,
            system_prompt=system_prompt,
            created_at=datetime.now().isoformat(),
            tools=self.tools
        )

        self.agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """List all agents"""
        return list(self.agents.values())

    def remember(self, agent_id: str, content: str) -> bool:
        """Store a memory for the agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        memory_item = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": "memory"
        }
        agent.memory.append(memory_item)
        return True

    def search_memory(self, agent_id: str, query: str) -> List[str]:
        """Search agent's memory (simple keyword match)"""
        agent = self.get_agent(agent_id)
        if not agent:
            return []

        # Simple search - in production use vector similarity
        query_lower = query.lower()
        results = []

        for item in agent.memory:
            if query_lower in item["content"].lower():
                results.append(item["content"])

        return results

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Execute a tool"""
        if tool_name == "search_memory":
            # Handled differently in context
            return "Use agent.search_memory() instead"

        elif tool_name == "remember":
            return "Use agent.remember() instead"

        elif tool_name == "calculate":
            try:
                result = eval(parameters["expression"])
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        elif tool_name == "get_time":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        elif tool_name == "list_tools":
            return json.dumps(self.tools, indent=2)

        return f"Unknown tool: {tool_name}"

    def process_message(
        self,
        agent_id: str,
        user_message: str
    ) -> str:
        """
        Process user message and generate response
        =============================================

        In production, this would call OpenAI API with:
        - System prompt
        - Conversation history
        - Tool definitions
        """

        agent = self.get_agent(agent_id)
        if not agent:
            return "Agent not found"

        # Simple response generation
        # In production: call OpenAI API with tools

        response = self._generate_response(agent, user_message)
        return response

    def _generate_response(self, agent: Agent, message: str) -> str:
        """Generate response (simplified - production would use LLM)"""

        message_lower = message.lower()

        # Check for tool usage
        if "calculate" in message_lower or "what is" in message_lower and any(c in message for c in "+-*/"):
            # Extract expression
            import re
            expr = re.search(r'[\d+\-*/().]+', message)
            if expr:
                result = self.execute_tool("calculate", {"expression": expr.group()})
                return f"Calculation result: {result}"

        # Check for time
        if "time" in message_lower:
            return f"Current time: {self.execute_tool('get_time', {})}"

        # Check for memory search
        if "remember" in message_lower:
            # Extract content
            content = message.replace("remember", "").strip()
            if content:
                agent.memory.append({
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "type": "memory"
                })
                return f"I'll remember: {content}"

        # Check for memory recall
        if "recall" in message_lower or "remember" in message_lower:
            query = message_lower.replace("recall", "").replace("remember", "").strip()
            if query:
                results = self.search_memory(agent.id, query)
                if results:
                    return "I recall: " + "; ".join(results)
                return "I don't recall anything about that"

        # Check for tools list
        if "tools" in message_lower or "what can you do" in message_lower:
            return f"I can:\n" + "\n".join(
                f"- {t['name']}: {t['description']}" for t in self.tools[:3]
            )

        # Default response
        return f"[{agent.name}] {self._get_default_response(message)}"

    def _get_default_response(self, message: str) -> str:
        """Default responses based on message"""
        responses = [
            f"I understand: {message[:30]}... Tell me more!",
            "That's interesting! What would you like to explore?",
            "I'm here to help. What do you need?",
            "Could you elaborate on that?",
        ]
        import random
        return random.choice(responses)


class AgentCLI:
    """
    Command Line Interface for AgentOS
    ====================================

    Interactive CLI to manage and chat with agents
    """

    def __init__(self):
        self.agentos = MiniAgentOS()
        self.current_agent: Optional[Agent] = None

    def run(self):
        """Run the CLI"""
        print("=" * 60)
        print("  Mini-AgentOS CLI v1.0")
        print("  Your Personal AI Agent Platform")
        print("=" * 60)
        print("\nType 'help' for commands\n")

        while True:
            try:
                if self.current_agent:
                    prompt = f"[{self.current_agent.name}]> "
                else:
                    prompt = "agentos> "

                user_input = input(prompt).strip()

                if not user_input:
                    continue

                self.handle_command(user_input)

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def handle_command(self, user_input: str):
        """Handle CLI commands"""

        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "help":
            self.show_help()

        elif command == "create":
            self.cmd_create(args)

        elif command == "list":
            self.cmd_list()

        elif command == "use":
            self.cmd_use(args)

        elif command == "chat":
            self.cmd_chat(args)

        elif command == "remember":
            self.cmd_remember(args)

        elif command == "recall":
            self.cmd_recall(args)

        elif command == "tools":
            self.cmd_tools()

        elif command == "state":
            self.cmd_state()

        elif command == "exit":
            sys.exit(0)

        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")

    def show_help(self):
        """Show help message"""
        print("""
Available Commands:
  create <name> <personality>  - Create a new agent
  list                         - List all agents
  use <agent_id>              - Switch to an agent
  chat <message>              - Chat with current agent
  remember <content>          - Store a memory
  recall <query>              - Search memories
  tools                       - List available tools
  state                       - Show agent state
  exit                        - Exit CLI
        """)

    def cmd_create(self, args: str):
        """Create an agent"""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            print("Usage: create <name> <personality>")
            return

        name, personality = parts
        agent = self.agentos.create_agent(name, personality)
        print(f"✓ Created agent: {agent.name} ({agent.id})")

    def cmd_list(self):
        """List agents"""
        agents = self.agentos.list_agents()
        if not agents:
            print("No agents yet. Create one with 'create' command.")
            return

        print(f"\nAgents ({len(agents)}):")
        for agent in agents:
            print(f"  {agent.id} - {agent.name} ({agent.personality})")

    def cmd_use(self, args: str):
        """Switch to agent"""
        agent_id = args.strip()
        agent = self.agentos.get_agent(agent_id)

        if not agent:
            print(f"Agent not found: {agent_id}")
            return

        self.current_agent = agent
        print(f"Switched to: {agent.name}")

    def cmd_chat(self, args: str):
        """Chat with agent"""
        if not self.current_agent:
            print("No active agent. Use 'create' or 'use' first.")
            return

        if not args.strip():
            print("What do you want to say?")
            return

        response = self.agentos.process_message(
            self.current_agent.id,
            args
        )
        print(f"\n{response}\n")

    def cmd_remember(self, args: str):
        """Store memory"""
        if not self.current_agent:
            print("No active agent.")
            return

        if self.agentos.remember(self.current_agent.id, args):
            print("✓ Memory stored!")
        else:
            print("Failed to store memory")

    def cmd_recall(self, args: str):
        """Search memory"""
        if not self.current_agent:
            print("No active agent.")
            return

        results = self.agentos.search_memory(self.current_agent.id, args)
        if results:
            print("Found memories:")
            for r in results:
                print(f"  - {r}")
        else:
            print("No memories found.")

    def cmd_tools(self):
        """List tools"""
        print("Available Tools:")
        for tool in self.agentos.tools:
            print(f"\n{tool['name']}:")
            print(f"  {tool['description']}")

    def cmd_state(self):
        """Show agent state"""
        if not self.current_agent:
            print("No active agent.")
            return

        agent = self.current_agent
        print(f"""
Agent State:
  ID: {agent.id}
  Name: {agent.name}
  Personality: {agent.personality}
  Created: {agent.created_at}
  Memories: {len(agent.memory)}
        """)


# Demo function
def demo():
    """Demonstrate Mini-AgentOS"""
    print("=" * 60)
    print("  Mini-AgentOS Demo")
    print("=" * 60)

    agentos = MiniAgentOS()

    # Create agent
    agent = agentos.create_agent("Assistant", "helpful and concise")
    print(f"\nCreated: {agent.name} ({agent.id})")

    # Chat
    response = agentos.process_message(agent.id, "Hello!")
    print(f"\nUser: Hello!")
    print(f"Agent: {response}")

    # Remember something
    agentos.remember(agent.id, "User likes Python programming")
    print("\nStored: User likes Python programming")

    # Recall
    results = agentos.search_memory(agent.id, "Python")
    print(f"\nRecall 'Python': {results}")

    # Use tool
    time_result = agentos.execute_tool("get_time", {})
    print(f"\nTool 'get_time': {time_result}")

    # More chat
    response = agentos.process_message(agent.id, "What do you remember about me?")
    print(f"\nUser: What do you remember about me?")
    print(f"Agent: {response}")

    print("\n" + "=" * 60)
    print("Demo complete! Run: python day20_mini_agentos.py")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        cli = AgentCLI()
        cli.run()