"""Example Agents for AgentOS (Day 8)

These examples demonstrate the practical implementation of AI agents:
1. Booking Agent - Appointment scheduling (from PDF)
2. Research Agent - Web research and summarization
3. Code Assistant Agent - Code generation and review
"""

from .booking_agent import BookingAgent, run_booking_demo
from .research_agent import ResearchAgent, run_research_demo
from .code_assistant import CodeAssistantAgent, run_code_assistant_demo

__all__ = [
    "BookingAgent",
    "run_booking_demo",
    "ResearchAgent",
    "run_research_demo",
    "CodeAssistantAgent",
    "run_code_assistant_demo"
]