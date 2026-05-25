"""
Day 21: LangChain Basics - The Agent Framework
=================================================
Skill: LangChain Framework
Mini Project: Basic LangChain Agent

LangChain is the most popular framework for building AI agents.
This introduces its core concepts.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Note: This is a simulation of LangChain concepts
# In production: pip install langchain langchain-openai


class PromptTemplate:
    """
    Prompt Template System
    =======================

    LangChain's core component for prompt management
    """

    def __init__(self, template: str, input_variables: List[str]):
        self.template = template
        self.input_variables = input_variables

    def format(self, **kwargs) -> str:
        """Format prompt with variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable: {e}")

    @staticmethod
    def from_template(template: str) -> 'PromptTemplate':
        """Create template from string"""
        import re
        # Find all {variable} patterns
        variables = re.findall(r'\{(\w+)\}', template)
        return PromptTemplate(template, variables)


class LLMChain:
    """
    LLM Chain - Combine prompts with LLMs
    =======================================
    """

    def __init__(self, llm, prompt: PromptTemplate):
        self.llm = llm
        self.prompt = prompt

    async def run(self, **kwargs) -> str:
        """Execute the chain"""
        formatted_prompt = self.prompt.format(**kwargs)
        return await self.llm.generate(formatted_prompt)

    def __call__(self, **kwargs):
        """Sync execution"""
        return self.run(**kwargs)


class MockLLM:
    """Mock LLM for demonstration"""

    def __init__(self, model: str = "gpt-4", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.calls = []

    async def generate(self, prompt: str) -> str:
        """Generate response"""
        self.calls.append({
            "prompt": prompt,
            "model": self.model,
            "timestamp": datetime.now().isoformat()
        })

        # Simple mock response
        return f"[{self.model}] Response to: {prompt[:50]}..."

    def __call__(self, prompt: str):
        """Sync interface"""
        return self.generate(prompt)


class AgentChain(LLMChain):
    """
    Agent Chain - Chain with agent behavior
    =======================================
    """

    def __init__(self, llm, prompt: PromptTemplate, tools: List[Dict] = None):
        super().__init__(llm, prompt)
        self.tools = tools or []
        self.agent_scratchpad = ""

    def add_tool(self, tool: Dict):
        """Add a tool to the agent"""
        self.tools.append(tool)

    async def run_with_tools(self, input_text: str) -> Dict[str, Any]:
        """Run agent with tool consideration"""

        # First, generate with tools in context
        tool_descriptions = self._format_tools()

        prompt_with_tools = self.prompt.format(
            input=input_text,
            tools=tool_descriptions,
            scratchpad=self.agent_scratchpad
        )

        response = await self.llm.generate(prompt_with_tools)

        # Check if tool should be called
        if self._should_use_tool(response):
            tool_result = self._execute_tool(response)
            self.agent_scratchpad += f"\nTool: {response}\nResult: {tool_result}"

            # Generate final response
            final_prompt = self.prompt.format(
                input=input_text,
                tools=tool_descriptions,
                scratchpad=self.agent_scratchpad
            )
            final_response = await self.llm.generate(final_prompt)

            return {
                "response": final_response,
                "tool_used": True,
                "tool_result": tool_result
            }

        return {
            "response": response,
            "tool_used": False
        }

    def _format_tools(self) -> str:
        """Format tools for prompt"""
        if not self.tools:
            return "No tools available."

        return "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in self.tools
        ])

    def _should_use_tool(self, text: str) -> bool:
        """Determine if tool should be used"""
        tool_keywords = ["use", "call", "execute", "search", "calculate"]
        return any(kw in text.lower() for kw in tool_keywords)

    def _execute_tool(self, tool_call: str) -> str:
        """Execute the tool (simplified)"""
        return "Tool executed successfully"


class RunnableSequence:
    """
    Runnable Sequence - Composable chains
    ======================================
    """

    def __init__(self, *steps):
        self.steps = steps

    async def invoke(self, input_data: Any) -> Any:
        """Execute sequence"""
        current = input_data

        for step in self.steps:
            if hasattr(step, 'run'):
                current = await step.run(**current) if isinstance(current, dict) else await step.run(current)
            else:
                current = step(current)

        return current


class ChatPromptTemplate:
    """
    Chat Prompt Template - For chat models
    =======================================
    """

    def __init__(self):
        self.messages = []

    def from_messages(self, messages: List[Dict[str, str]]) -> 'ChatPromptTemplate':
        """Create from message list"""
        for msg in messages:
            self.messages.append(msg)
        return self

    def add_system_message(self, content: str) -> 'ChatPromptTemplate':
        """Add system message"""
        self.messages.append({"type": "system", "content": content})
        return self

    def add_user_message(self, content: str) -> 'ChatPromptTemplate':
        """Add user message"""
        self.messages.append({"type": "user", "content": content})
        return self

    def add_ai_message(self, content: str) -> 'ChatPromptTemplate':
        """Add AI message"""
        self.messages.append({"type": "assistant", "content": content})
        return self

    def format(self) -> str:
        """Format as single prompt"""
        return "\n".join([
            f"{msg['type'].upper()}: {msg['content']}"
            for msg in self.messages
        ])


# Demo
def run_demo():
    print("=" * 70)
    print("LangChain Basics Demo")
    print("=" * 70)

    # Create prompt template
    template = PromptTemplate.from_template(
        "You are {name}, a {role}. Help with: {task}"
    )

    print(f"\nTemplate: {template.template}")
    print(f"Variables: {template.input_variables}")

    formatted = template.format(name="Assistant", role="helper", task="questions")
    print(f"\nFormatted: {formatted}")

    # Create LLM
    llm = MockLLM(model="gpt-4")

    # Create chain
    prompt = PromptTemplate.from_template("Tell me about {topic}")
    chain = LLMChain(llm, prompt)

    # Run
    result = chain.run(topic="Python")
    print(f"\nChain result: {result}")

    # Agent with tools
    print("\n" + "-" * 40)
    print("Agent with Tools")
    print("-" * 40)

    agent_prompt = PromptTemplate.from_template(
        "You are a helpful agent. Input: {input}. Available tools: {tools}"
    )

    agent = AgentChain(llm, agent_prompt)
    agent.add_tool({
        "name": "search",
        "description": "Search for information"
    })

    result = agent.run_with_tools("Find information about AI")
    print(f"\nAgent result: {result['response']}")
    print(f"Tool used: {result.get('tool_used', False)}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()