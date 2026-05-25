"""
Day 37: Context Management
=========================
Skill: Context Engineering
Mini Project: Context Window Manager

Managing context windows and optimizing token usage.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import tiktoken
from collections import deque


class ContextStrategy(str, Enum):
    """Context management strategies"""
    FULL = "full"                    # Keep all context
    SLIDING = "sliding"              # Sliding window
    SUMMARIZE = "summarize"          # Summarize old content
    LANDMARK = "landmark"            # Keep important landmarks
    SEMANTIC = "semantic"            # Semantic chunking


@dataclass
class Message:
    """A message in the conversation"""
    role: str
    content: str
    token_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """Manages a context window"""
    max_tokens: int
    strategy: ContextStrategy = ContextStrategy.SLIDING
    messages: List[Message] = field(default_factory=list)
    system_prompt: str = ""

    def __post_init__(self):
        self._tokenizer = self._get_tokenizer()

    def _get_tokenizer(self):
        """Get tokenizer for token counting"""
        try:
            return tiktoken.get_encoding("cl100k_base")
        except:
            return None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        return len(text) // 4  # Approximate

    def get_total_tokens(self) -> int:
        """Get total tokens in context"""
        total = self.count_tokens(self.system_prompt)
        for msg in self.messages:
            total += msg.token_count
        return total

    def is_full(self) -> bool:
        """Check if context is full"""
        return self.get_total_tokens() >= self.max_tokens

    def add_message(self, role: str, content: str, metadata: Dict = None) -> int:
        """Add a message to context"""
        token_count = self.count_tokens(content)
        message = Message(
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {}
        )

        # Apply strategy
        self._apply_strategy(message)
        return token_count

    def _apply_strategy(self, new_message: Message):
        """Apply context management strategy"""
        if self.strategy == ContextStrategy.FULL:
            self.messages.append(new_message)

        elif self.strategy == ContextStrategy.SLIDING:
            self.messages.append(new_message)
            while self.is_full() and len(self.messages) > 1:
                self.messages.pop(0)

        elif self.strategy == ContextStrategy.SUMMARIZE:
            self.messages.append(new_message)
            while self.is_full() and len(self.messages) > 1:
                # Summarize oldest message
                old = self.messages.pop(0)
                summarized = f"[Summary of previous {old.role} message]: {old.content[:100]}..."
                self.messages.insert(0, Message(old.role, summarized, self.count_tokens(summarized)))

        elif self.strategy == ContextStrategy.LANDMARK:
            self.messages.append(new_message)
            # Keep first message as landmark
            landmarks = [self.messages[0]] if self.messages else []
            regular = [m for m in self.messages[1:] if m.metadata.get("is_landmark", False)]

            # Rebuild from landmarks + regular
            self.messages = landmarks + regular
            while self.is_full() and len(self.messages) > 1:
                self.messages.pop(1)

        elif self.strategy == ContextStrategy.SEMANTIC:
            # Keep most semantically relevant
            self.messages.append(new_message)
            # For now, fall back to sliding
            while self.is_full() and len(self.messages) > 1:
                self.messages.pop(0)

    def get_context(self) -> List[Dict[str, str]]:
        """Get formatted context for LLM"""
        context = []
        if self.system_prompt:
            context.append({"role": "system", "content": self.system_prompt})

        for msg in self.messages:
            context.append({"role": msg.role, "content": msg.content})

        return context

    def get_context_text(self) -> str:
        """Get context as text"""
        parts = []
        if self.system_prompt:
            parts.append(f"System: {self.system_prompt}")

        for msg in self.messages:
            parts.append(f"{msg.role.capitalize()}: {msg.content}")

        return "\n\n".join(parts)


class ContextManager:
    """Manages multiple context windows"""

    def __init__(self, max_tokens: int = 8000, strategy: ContextStrategy = ContextStrategy.SLIDING):
        self.max_tokens = max_tokens
        self.strategy = strategy
        self.windows: Dict[str, ContextWindow] = {}
        self.default_window = ContextWindow(max_tokens, strategy)

    def create_context(self, context_id: str, system_prompt: str = "", max_tokens: int = None) -> ContextWindow:
        """Create a new context window"""
        window = ContextWindow(
            max_tokens=max_tokens or self.max_tokens,
            strategy=self.strategy,
            system_prompt=system_prompt
        )
        self.windows[context_id] = window
        return window

    def get_context(self, context_id: str = None) -> ContextWindow:
        """Get a context window"""
        if context_id and context_id in self.windows:
            return self.windows[context_id]
        return self.default_window

    def add_message(
        self,
        role: str,
        content: str,
        context_id: str = None,
        metadata: Dict = None
    ) -> int:
        """Add a message to a context"""
        window = self.get_context(context_id)
        return window.add_message(role, content, metadata)

    def clear_context(self, context_id: str = None):
        """Clear a context"""
        if context_id and context_id in self.windows:
            self.windows[context_id] = ContextWindow(
                self.max_tokens,
                self.strategy,
                self.windows[context_id].system_prompt
            )
        else:
            self.default_window = ContextWindow(self.max_tokens, self.strategy)

    def get_stats(self, context_id: str = None) -> Dict[str, Any]:
        """Get context statistics"""
        window = self.get_context(context_id)
        return {
            "token_count": window.get_total_tokens(),
            "max_tokens": window.max_tokens,
            "message_count": len(window.messages),
            "strategy": window.strategy.value,
            "usage_percent": (window.get_total_tokens() / window.max_tokens) * 100
        }


class TokenOptimizer:
    """Optimizes token usage"""

    def __init__(self):
        self.strategies = {
            "truncate": self._truncate,
            "compress": self._compress,
            "extract": self._extract_key_info
        }

    def optimize(
        self,
        text: str,
        max_tokens: int,
        strategy: str = "truncate"
    ) -> str:
        """Optimize text to fit token limit"""
        if strategy in self.strategies:
            return self.strategies[strategy](text, max_tokens)
        return text

    def _truncate(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit"""
        try:
            tokenizer = tiktoken.get_encoding("cl100k_base")
            tokens = tokenizer.encode(text)
            if len(tokens) <= max_tokens:
                return text
            return tokenizer.decode(tokens[:max_tokens])
        except:
            return text[:max_tokens * 4]

    def _compress(self, text: str, max_tokens: int) -> str:
        """Compress text (simple approach)"""
        # Remove extra whitespace
        compressed = " ".join(text.split())
        return self._truncate(compressed, max_tokens)

    def _extract_key_info(self, text: str, max_tokens: int) -> str:
        """Extract key information"""
        # Simple extraction: keep first and last parts
        lines = text.split("\n")
        if len(lines) <= 2:
            return self._truncate(text, max_tokens)

        # Keep first and last lines
        kept = [lines[0], "..."]
        if len(lines) > 2:
            kept.append(lines[-1])

        result = "\n".join(kept)
        return self._truncate(result, max_tokens)


class ConversationMemory:
    """Long-term conversation memory with retrieval"""

    def __init__(self, max_memory_tokens: int = 50000):
        self.max_memory_tokens = max_memory_tokens
        self.long_term: deque = deque(maxlen=1000)
        self.short_term: List[Message] = []
        self.current_tokens = 0
        self._tokenizer = None

        try:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            pass

    def _count_tokens(self, text: str) -> int:
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        return len(text) // 4

    def add_message(self, role: str, content: str):
        """Add a message to memory"""
        tokens = self._count_tokens(content)
        msg = Message(role, content, tokens)

        self.short_term.append(msg)
        self.current_tokens += tokens

        # Move to long-term if short-term is full
        while self.current_tokens > self.max_memory_tokens and self.short_term:
            old = self.short_term.pop(0)
            self.long_term.append(old)
            self.current_tokens -= old.token_count

    def get_recent(self, max_tokens: int) -> List[Message]:
        """Get recent messages within token limit"""
        result = []
        total = 0

        for msg in reversed(self.short_term):
            if total + msg.token_count <= max_tokens:
                result.insert(0, msg)
                total += msg.token_count
            else:
                break

        return result

    def search(self, query: str, max_results: int = 5) -> List[Message]:
        """Search long-term memory"""
        query_lower = query.lower()
        results = []

        for msg in self.long_term:
            if query_lower in msg.content.lower():
                results.append(msg)
                if len(results) >= max_results:
                    break

        return results


# Demo
def run_demo():
    print("=" * 70)
    print("Context Management Demo")
    print("=" * 70)

    # Test Context Window
    print("\n[1] Context Window")
    print("-" * 40)

    ctx = ContextWindow(max_tokens=500, strategy=ContextStrategy.SLIDING)
    ctx.system_prompt = "You are a helpful assistant."

    ctx.add_message("user", "Hello, how are you?")
    print(f"  After 1 message: {ctx.get_total_tokens()} tokens")

    ctx.add_message("assistant", "I'm doing great, thank you!")
    print(f"  After 2 messages: {ctx.get_total_tokens()} tokens")

    # Add many messages to test sliding
    for i in range(10):
        ctx.add_message("user", f"This is message number {i} with some additional content to test the sliding window.")

    print(f"  After 12 messages: {ctx.get_total_tokens()} tokens, {len(ctx.messages)} messages kept")

    # Test Context Manager
    print("\n[2] Context Manager")
    print("-" * 40)

    manager = ContextManager(max_tokens=1000)

    manager.add_message("user", "First message", "session-1")
    manager.add_message("assistant", "First response", "session-1")
    manager.add_message("user", "Different session", "session-2")

    stats1 = manager.get_stats("session-1")
    stats2 = manager.get_stats("session-2")

    print(f"  Session 1: {stats1['message_count']} messages, {stats1['token_count']} tokens")
    print(f"  Session 2: {stats2['message_count']} messages, {stats2['token_count']} tokens")

    # Test Token Optimizer
    print("\n[3] Token Optimizer")
    print("-" * 40)

    optimizer = TokenOptimizer()

    long_text = "This is a very long piece of text that we need to optimize. " * 20

    truncated = optimizer.optimize(long_text, 50, "truncate")
    compressed = optimizer.optimize(long_text, 50, "compress")
    extracted = optimizer.optimize(long_text, 50, "extract")

    print(f"  Original length: {len(long_text)} chars")
    print(f"  Truncated: {len(truncated)} chars")
    print(f"  Compressed: {len(compressed)} chars")
    print(f"  Extracted: {len(extracted)} chars")

    # Test Conversation Memory
    print("\n[4] Conversation Memory")
    print("-" * 40)

    memory = ConversationMemory(max_memory_tokens=1000)

    for i in range(20):
        memory.add_message("user", f"Message {i}: Some content here")

    print(f"  Short-term messages: {len(memory.short_term)}")
    print(f"  Long-term messages: {len(memory.long_term)}")

    recent = memory.get_recent(200)
    print(f"  Retrieved recent: {len(recent)} messages")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()