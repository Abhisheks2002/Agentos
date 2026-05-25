"""
Day 24: AutoGen - Advanced Multi-Agent Framework
=================================================
Skill: AutoGen Framework
Mini Project: Conversation Flow Designer

AutoGen enables sophisticated multi-agent conversations with
customizable agents and automated conversation flow.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class AutoGenAgentType(str, Enum):
    """AutoGen agent types"""
    ASSISTANT = "assistant"
    USER_PROXY = "user_proxy"
    CODE_EXECUTOR = "code_executor"
    GROUP_CHAT = "group_chat"


@dataclass
class AgentConfig:
    """AutoGen agent configuration"""
    name: str
    agent_type: AutoGenAgentType
    system_message: str
    llm_config: Dict[str, Any] = field(default_factory=dict)
    code_execution_config: Optional[Dict] = None


@dataclass
class Message:
    """Conversation message"""
    sender: str
    recipient: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AutoGenAgent:
    """
    AutoGen Agent
    =============

    Agents that can:
    - Receive and send messages
    - Generate responses using LLMs
    - Execute code
    - Participate in group chats
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.agent_type = config.agent_type
        self.system_message = config.system_message
        self.llm_config = config.llm_config
        self.conversation_history: List[Message] = []

    async def generate_reply(self, messages: List[Dict[str, str]]) -> str:
        """Generate reply based on messages"""
        # In production: call LLM with messages
        last_message = messages[-1]["content"] if messages else ""

        response = f"[{self.name}] Response to: {last_message[:30]}..."

        # Simulate tool use if needed
        if "code" in last_message.lower() and self.config.code_execution_config:
            response = await self._execute_code(last_message)

        return response

    async def _execute_code(self, code: str) -> str:
        """Execute code (simplified)"""
        # In production: use actual code execution
        return f"Executed: {code[:50]}...\nResult: Success"

    def add_message(self, message: Message):
        """Add message to history"""
        self.conversation_history.append(message)

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


class UserProxyAgent(AutoGenAgent):
    """User proxy agent - represents user in conversation"""

    def __init__(self, name: str, human_input_mode: str = "ALWAYS"):
        config = AgentConfig(
            name=name,
            agent_type=AutoGenAgentType.USER_PROXY,
            system_message="You are a user proxy. Collect input and forward to agents."
        )
        super().__init__(config)
        self.human_input_mode = human_input_mode

    async def generate_reply(self, messages: List[Dict[str, str]]) -> str:
        """Get user input or auto-reply"""
        if self.human_input_mode == "NEVER":
            return "Continuing with automated response..."
        return "User input required"


class CodeExecutorAgent(AutoGenAgent):
    """Code execution agent"""

    def __init__(self, name: str):
        config = AgentConfig(
            name=name,
            agent_type=AutoGenAgentType.CODE_EXECUTOR,
            system_message="You execute Python code and return results.",
            code_execution_config={
                "work_dir": ".",
                "use_docker": False
            }
        )
        super().__init__(config)

    async def generate_reply(self, messages: List[Dict[str, str]]) -> str:
        """Execute code in messages"""
        last_msg = messages[-1]["content"] if messages else ""

        # Extract code
        if "```python" in last_msg:
            code = last_msg.split("```python")[1].split("```")[0]
            return await self._execute_code(code)
        elif "```" in last_msg:
            code = last_msg.split("```")[1].split("```")[0]
            return await self._execute_code(code)

        return "No code found to execute"


class GroupChat:
    """
    Group Chat - Multiple agents in conversation
    ============================================
    """

    def __init__(
        self,
        agents: List[AutoGenAgent],
        speaker_selection_method: str = "round_robin",
        max_round: int = 10
    ):
        self.agents = agents
        self.speaker_selection = speaker_selection_method
        self.max_round = max_round
        self.messages: List[Message] = []
        self.current_speaker_index = 0

    async def add(self, agent: AutoGenAgent):
        """Add agent to group"""
        if agent not in self.agents:
            self.agents.append(agent)

    async def remove(self, agent_name: str):
        """Remove agent from group"""
        self.agents = [a for a in self.agents if a.name != agent_name]

    async def select_speaker(self) -> AutoGenAgent:
        """Select next speaker"""
        if self.speaker_selection == "round_robin":
            speaker = self.agents[self.current_speaker_index]
            self.current_speaker_index = (self.current_speaker_index + 1) % len(self.agents)
            return speaker
        elif self.speaker_selection == "random":
            import random
            return random.choice(self.agents)
        return self.agents[0]

    async def execute(self, initial_message: str = None) -> Dict[str, Any]:
        """Execute group chat"""
        results = []

        # Initial message
        if initial_message:
            msg = Message(
                sender="system",
                recipient="all",
                content=initial_message
            )
            self.messages.append(msg)

        # Round-robin execution
        for round_num in range(self.max_round):
            speaker = await self.select_speaker()

            # Convert history to dict format
            history = [
                {"content": m.content, "role": "user" if m.sender != speaker.name else "assistant"}
                for m in self.messages[-10:]  # Last 10 messages
            ]

            # Generate response
            response = await speaker.generate_reply(history)

            # Add to messages
            msg = Message(
                sender=speaker.name,
                recipient="group",
                content=response
            )
            self.messages.append(msg)
            results.append({
                "round": round_num + 1,
                "speaker": speaker.name,
                "response": response
            })

        return {
            "rounds": len(results),
            "messages": [
                {"sender": m.sender, "content": m.content[:50]}
                for m in self.messages
            ]
        }


class ConversableAgent(AutoGenAgent):
    """
    Conversable Agent - Can be extended
    ====================================
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.register_reply()

    def register_reply(self):
        """Register reply functions"""
        self.reply_funcs = []

    def register_function(self, func: Callable):
        """Register a function for the agent"""
        self.reply_funcs.append(func)


# Demo
def run_demo():
    print("=" * 70)
    print("AutoGen Framework Demo")
    print("=" * 70)

    import asyncio

    # Create agents
    print("\n[1] Creating Agents")
    print("-" * 40)

    assistant = AutoGenAgent(AgentConfig(
        name="Assistant",
        agent_type=AutoGenAgentType.ASSISTANT,
        system_message="You are a helpful assistant."
    ))

    executor = CodeExecutorAgent("CodeExecutor")

    print(f"  ✓ {assistant.name} ({assistant.agent_type.value})")
    print(f"  ✓ {executor.name} ({executor.agent_type.value})")

    # Test conversation
    print("\n[2] Single Agent Conversation")
    print("-" * 40)

    messages = [
        {"content": "Hello, how can you help?", "role": "user"}
    ]

    response = asyncio.run(assistant.generate_reply(messages))
    print(f"  User: Hello, how can you help?")
    print(f"  {assistant.name}: {response}")

    # Test code execution
    print("\n[3] Code Execution")
    print("-" * 40)

    code_msg = [{"content": "```python\nprint('Hello from AutoGen!')\n```", "role": "user"}]
    response = asyncio.run(executor.generate_reply(code_msg))
    print(f"  Result: {response[:80]}...")

    # Test group chat
    print("\n[4] Group Chat")
    print("-" * 40)

    writer = AutoGenAgent(AgentConfig(
        name="Writer",
        agent_type=AutoGenAgentType.ASSISTANT,
        system_message="You are a creative writer."
    ))

    critic = AutoGenAgent(AgentConfig(
        name="Critic",
        agent_type=AutoGenAgentType.ASSISTANT,
        system_message="You critique written content."
    ))

    group = GroupChat(
        agents=[assistant, writer, critic],
        speaker_selection_method="round_robin",
        max_round=3
    )

    result = asyncio.run(group.execute("Write about AI"))

    print(f"  Completed {result['rounds']} rounds")
    for msg in result["messages"][:3]:
        print(f"    {msg['sender']}: {msg['content']}...")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()