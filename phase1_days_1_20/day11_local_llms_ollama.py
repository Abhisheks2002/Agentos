"""
Day 11: Introduction to Local LLMs (Ollama)
============================================
Skill: Running models locally
Mini Project: The Private Agent

Run Llama 3 locally for privacy-focused agents.
Completely offline agent that summarizes local text files.
"""

import os
import subprocess
from typing import Optional, Dict

# Note: Requires Ollama to be installed
# Download from: https://ollama.ai

class OllamaClient:
    """Simple client for Ollama local LLM"""

    def __init__(self, model: str = "llama3"):
        self.model = model

    def generate(self, prompt: str, system: str = None, **kwargs) -> str:
        """Generate text using local Ollama model"""
        cmd = ["ollama", "run", self.model]

        # Build the prompt
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\n{prompt}"

        try:
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 120)
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr}"

        except FileNotFoundError:
            return "Error: Ollama not found. Install from https://ollama.ai"
        except subprocess.TimeoutExpired:
            return "Error: Generation timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    def list_models(self) -> list:
        """List available Ollama models"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                return [line.split()[0] for line in lines if line]
            return []

        except FileNotFoundError:
            return []
        except Exception:
            return []

class PrivateAgent:
    """A completely offline agent for privacy-sensitive tasks"""

    def __init__(self, name: str = "PrivateAgent"):
        self.name = name
        self.ollama = OllamaClient()

    def summarize_file(self, filepath: str) -> str:
        """Summarize a local text file (completely offline)"""
        if not os.path.exists(filepath):
            return f"Error: File not found: {filepath}"

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Truncate if too long (Ollama has context limits)
            max_chars = 8000
            if len(content) > max_chars:
                content = content[:max_chars] + "..."

            prompt = f"""Please summarize the following text concisely:

{content}

Summary:"""

            system = f"You are {self.name}, a privacy-focused assistant that summarizes documents locally."

            return self.ollama.generate(prompt, system=system)

        except Exception as e:
            return f"Error: {str(e)}"

    def answer_question(self, question: str, context: str = "") -> str:
        """Answer a question, optionally with context"""
        prompt = question
        if context:
            prompt = f"""Based on the following context, answer the question.

Context: {context}

Question: {question}

Answer:"""

        return self.ollama.generate(prompt)

def demo_ollama_available():
    """Check if Ollama is available"""
    client = OllamaClient()
    models = client.list_models()

    if models:
        print(f"Available Ollama models: {', '.join(models)}")
        return True
    else:
        print("Ollama not available. Install from https://ollama.ai")
        return False

def demo():
    """Demo The Private Agent"""
    print("=" * 70)
    print("The Private Agent - Local LLM Demo")
    print("=" * 70)

    if not demo_ollama_available():
        print("\nTo use this demo:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Run: ollama pull llama3")
        print("3. Run this script again")
        return

    agent = PrivateAgent("PrivacyBot")

    # Create a sample file
    sample_file = "sample_document.txt"
    sample_content = """
    AgentOS Architecture Overview

    AgentOS is designed as a multi-layered operating system for AI agents.
    The architecture consists of the following components:

    1. Kernel Layer: Manages agent lifecycles, scheduling, and resource allocation.
    2. Memory Layer: Provides persistent and ephemeral memory storage using vector databases.
    3. Communication Layer: Handles inter-agent messaging via Redis pub/sub.
    4. Governance Layer: Implements RBAC, audit logging, and security policies.
    5. Tool Layer: Manages tool registration and execution.

    The system is built for scalability, supporting thousands of concurrent agents.
    """

    with open(sample_file, 'w') as f:
        f.write(sample_content)

    print(f"\nCreated sample file: {sample_file}")
    print("-" * 50)

    print("\nSummarizing file with local LLM...")
    summary = agent.summarize_file(sample_file)
    print(f"\nSummary:\n{summary}")

    # Clean up
    os.remove(sample_file)

    print("\n" + "-" * 50)
    print("\nAsking a general question to local LLM...")
    answer = agent.answer_question("What is the capital of France?")
    print(f"\nAnswer: {answer}")

if __name__ == "__main__":
    demo()