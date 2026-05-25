"""
Day 8: Token Management & Cost Optimization
============================================
Skill: Tiktoken & Token Windowing
Mini Project: Cost Dashboard

Memory is expensive. We need to "evict" old memories when an agent's
"context window" is full.
"""

from typing import List, Dict
import tiktoken

# Encoding for token counting (using cl100k_base for GPT-4)
try:
    enc = tiktoken.get_encoding("cl100k_base")
except:
    enc = None

DEFAULT_MAX_TOKENS = 4096

def count_tokens(text: str) -> int:
    """Count tokens in text"""
    if enc:
        return len(enc.encode(text))
    # Fallback: rough estimate
    return len(text.split()) * 1.3

def truncate_to_token_limit(messages: List[Dict], max_tokens: int = DEFAULT_MAX_TOKENS) -> List[Dict]:
    """
    Truncate conversation history to stay under token limit.
    Keeps system prompt and most recent messages.
    """
    truncated = []
    total_tokens = 0

    # Iterate backwards (most recent first)
    for msg in reversed(messages):
        msg_tokens = count_tokens(msg.get("content", ""))

        if total_tokens + msg_tokens <= max_tokens:
            truncated.insert(0, msg)
            total_tokens += msg_tokens
        else:
            break

    return truncated

class CostTracker:
    """Track and estimate costs for AgentOS sessions"""

    PRICING = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},  # per 1K tokens
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.pricing = self.PRICING.get(model, self.PRICING["gpt-4o-mini"])
        self.session_tokens = {"input": 0, "output": 0}

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage"""
        self.session_tokens["input"] += input_tokens
        self.session_tokens["output"] += output_tokens

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD"""
        input_cost = (input_tokens / 1000) * self.pricing["input"]
        output_cost = (output_tokens / 1000) * self.pricing["output"]
        return input_cost + output_cost

    def get_session_cost(self) -> float:
        """Get total session cost"""
        return self.estimate_cost(
            self.session_tokens["input"],
            self.session_tokens["output"]
        )

    def get_cost_report(self) -> Dict:
        """Get detailed cost report"""
        total_tokens = self.session_tokens["input"] + self.session_tokens["output"]
        cost = self.get_session_cost()

        return {
            "model": self.model,
            "input_tokens": self.session_tokens["input"],
            "output_tokens": self.session_tokens["output"],
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(cost, 4),
            "pricing": self.pricing
        }

def demo_token_counting():
    """Demo token counting"""
    print("=" * 70)
    print("Token Management & Cost Optimization Demo")
    print("=" * 70)

    sample_text = "This is a sample text for token counting. AgentOS needs to manage tokens efficiently to control costs."

    token_count = count_tokens(sample_text)
    print(f"\nSample text: {sample_text}")
    print(f"Character count: {len(sample_text)}")
    print(f"Estimated tokens: {token_count}")

def demo_conversation_truncation():
    """Demo conversation truncation"""
    print("\n" + "-" * 70)
    print("Conversation Truncation Demo")
    print("-" * 70)

    # Simulated conversation
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, my name is John."},
        {"role": "assistant", "content": "Hello John! Nice to meet you. How can I help you today?"},
        {"role": "user", "content": "I want to build an AI agent."},
        {"role": "assistant", "content": "That's great! I can help you build an AI agent. What kind of agent would you like to create?"},
        {"role": "user", "content": "I want an agent that can read files and search the web."},
        {"role": "assistant", "content": "I can help you build that! We'll need to create tools for file reading and web search."},
        {"role": "user", "content": "Perfect. Let me tell you about my project. It's called AgentOS and it's a platform for managing AI agents."},
    ]

    print(f"Original messages: {len(messages)}")
    print(f"Original tokens: {sum(count_tokens(m['content']) for m in messages)}")

    truncated = truncate_to_token_limit(messages, max_tokens=50)

    print(f"\nTruncated to {len(truncated)} messages")
    print(f"Truncated tokens: {sum(count_tokens(m['content']) for m in truncated)}")

def demo_cost_tracking():
    """Demo cost tracking"""
    print("\n" + "-" * 70)
    print("Cost Dashboard Demo")
    print("-" * 70)

    tracker = CostTracker("gpt-4o-mini")

    # Simulate some API calls
    tracker.add_usage(150, 50)   # First call
    tracker.add_usage(200, 80)   # Second call
    tracker.add_usage(100, 40)   # Third call

    report = tracker.get_cost_report()
    print(f"\nCost Report:")
    print(f"  Model: {report['model']}")
    print(f"  Input tokens: {report['input_tokens']}")
    print(f"  Output tokens: {report['output_tokens']}")
    print(f"  Total tokens: {report['total_tokens']}")
    print(f"  Estimated cost: ${report['estimated_cost_usd']:.4f}")

if __name__ == "__main__":
    demo_token_counting()
    demo_conversation_truncation()
    demo_cost_tracking()