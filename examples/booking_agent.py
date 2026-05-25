"""Booking Agent - Example from Day 8 PDF

This agent demonstrates:
- Tool definitions (get_available_slots, book_slot, cancel_booking, get_booking_status)
- System prompt defining agent behavior
- User interaction loop
- Tool execution with parameters

Run with: python -m examples.booking_agent
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.agent import Agent, AgentResponse
from core.agent_builder import AgentBuilder
from core.models.models import AgentType
from core.reasoning.chain_of_thought import ReasoningType


# In-memory booking storage (simulates a database)
class BookingStore:
    """Simulated booking database."""
    _slots = {}
    _bookings = {}
    _booking_counter = 1000

    @classmethod
    def get_available_slots(cls, date: str, service: str = None) -> List[Dict]:
        """Get available appointment slots."""
        # Generate time slots for the date
        slots = []
        base_date = datetime.strptime(date, "%Y-%m-%d")

        time_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]

        for time in time_slots:
            slot_id = f"{date}_{time}"
            if slot_id not in cls._slots:
                slots.append({
                    "date": date,
                    "time": time,
                    "available": True
                })

        return slots

    @classmethod
    def book_slot(
        cls,
        date: str,
        time: str,
        service: str,
        customer_name: str,
        customer_email: str
    ) -> Dict:
        """Book an appointment slot."""
        slot_id = f"{date}_{time}"

        if slot_id in cls._slots:
            return {
                "success": False,
                "error": "Slot already booked"
            }

        cls._booking_counter += 1
        booking_id = f"BK{cls._booking_counter}"

        cls._slots[slot_id] = {
            "booking_id": booking_id,
            "date": date,
            "time": time,
            "service": service,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "status": "confirmed"
        }

        cls._bookings[booking_id] = cls._slots[slot_id]

        return {
            "success": True,
            "booking_id": booking_id,
            "date": date,
            "time": time,
            "service": service,
            "customer_name": customer_name,
            "message": f"Booking confirmed! Your appointment is set for {date} at {time}"
        }

    @classmethod
    def cancel_booking(cls, booking_id: str) -> Dict:
        """Cancel a booking."""
        if booking_id not in cls._bookings:
            return {
                "success": False,
                "error": "Booking not found"
            }

        booking = cls._bookings[booking_id]
        slot_id = f"{booking['date']}_{booking['time']}"

        if slot_id in cls._slots:
            del cls._slots[slot_id]

        del cls._bookings[booking_id]

        return {
            "success": True,
            "message": f"Booking {booking_id} has been cancelled"
        }

    @classmethod
    def get_booking_status(cls, booking_id: str) -> Dict:
        """Get booking status."""
        if booking_id not in cls._bookings:
            return {
                "success": False,
                "error": "Booking not found"
            }

        booking = cls._bookings[booking_id]
        return {
            "success": True,
            "booking": booking
        }


def create_booking_agent() -> Agent:
    """Create a fully configured booking agent."""

    # Define the booking tools
    booking_tools = [
        {
            "name": "get_available_slots",
            "description": "Get available appointment slots for a specific date",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    },
                    "service": {
                        "type": "string",
                        "description": "Service type (optional)"
                    }
                },
                "required": ["date"]
            }
        },
        {
            "name": "book_slot",
            "description": "Book an appointment slot",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    },
                    "time": {
                        "type": "string",
                        "description": "Time slot (e.g., 10:00)"
                    },
                    "service": {
                        "type": "string",
                        "description": "Service type"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's full name"
                    },
                    "customer_email": {
                        "type": "string",
                        "description": "Customer's email address"
                    }
                },
                "required": ["date", "time", "service", "customer_name", "customer_email"]
            }
        },
        {
            "name": "cancel_booking",
            "description": "Cancel an existing booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "Booking ID to cancel"
                    }
                },
                "required": ["booking_id"]
            }
        },
        {
            "name": "get_booking_status",
            "description": "Check the status of a booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "Booking ID to check"
                    }
                },
                "required": ["booking_id"]
            }
        }
    ]

    # Create the agent using AgentBuilder
    agent = (
        AgentBuilder("Booking Assistant")
        .with_type(AgentType.CHAT)
        .with_tools(booking_tools)
        .with_reasoning(ReasoningType.REACT)
        .with_system_prompt("""You are a friendly booking assistant for a service business.

Your capabilities:
- Check available appointment slots using get_available_slots
- Book appointments using book_slot
- Cancel bookings using cancel_booking
- Check booking status using get_booking_status

When helping customers:
1. Ask for the required information
2. Use tools to check availability before booking
3. Confirm booking details before finalizing
4. Provide clear confirmation with booking ID

Always be polite and helpful!""")
        .build()
    )

    return agent


def get_tool_handlers():
    """Get tool handlers that connect tools to BookingStore."""
    return {
        "get_available_slots": lambda params: BookingStore.get_available_slots(
            params.get("date"),
            params.get("service")
        ),
        "book_slot": lambda params: BookingStore.book_slot(
            params.get("date"),
            params.get("time"),
            params.get("service"),
            params.get("customer_name"),
            params.get("customer_email")
        ),
        "cancel_booking": lambda params: BookingStore.cancel_booking(
            params.get("booking_id")
        ),
        "get_booking_status": lambda params: BookingStore.get_booking_status(
            params.get("booking_id")
        )
    }


class BookingAgent:
    """Booking Agent with integrated tool handlers."""

    def __init__(self):
        self.agent = create_booking_agent()
        self.tool_handlers = get_tool_handlers()

        # Override tool execution to use our handlers
        original_execute = self.agent._execute_tool

        async def execute_with_handler(tool_name: str, params: Dict):
            handler = self.tool_handlers.get(tool_name)
            if handler:
                try:
                    return handler(params)
                except Exception as e:
                    return {"error": str(e)}
            return await original_execute(tool_name, params)

        self.agent._execute_tool = execute_with_handler

    async def start(self):
        """Start the agent."""
        await self.agent.start()

    async def stop(self):
        """Stop the agent."""
        await self.agent.stop()

    async def handle_message(self, message: str) -> str:
        """Handle a user message."""
        response = await self.agent.run(message)
        return response.output

    async def run_interactive(self):
        """Run an interactive booking session."""
        print("=" * 50)
        print("Booking Agent - Interactive Mode")
        print("=" * 50)
        print("\nWelcome! I can help you:")
        print("- Check available slots")
        print("- Book an appointment")
        print("- Cancel a booking")
        print("- Check booking status")
        print("\nType 'quit' to exit\n")

        await self.start()

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nThank you for using Booking Agent. Goodbye!")
                break

            if not user_input:
                continue

            response = await self.handle_message(user_input)
            print(f"\nAgent: {response}\n")

        await self.stop()


async def run_booking_demo():
    """Run a demonstration of the booking agent."""
    print("=" * 50)
    print("Booking Agent Demo")
    print("=" * 50)

    # Create agent
    agent_wrapper = BookingAgent()
    await agent_wrapper.start()

    # Demo interactions
    test_scenarios = [
        "I want to book an appointment",
        "What slots are available on 2026-03-20?",
        "Book a slot at 10:00 on 2026-03-20 for hair cut",
        "What's my booking status?"
    ]

    for scenario in test_scenarios:
        print(f"\n--- User: {scenario} ---")
        response = await agent_wrapper.handle_message(scenario)
        print(f"Agent: {response}")

    await agent_wrapper.stop()

    print("\n" + "=" * 50)
    print("Demo complete!")
    print("=" * 50)


if __name__ == "__main__":
    # Option 1: Run demo
    asyncio.run(run_booking_demo())

    # Option 2: Run interactive mode (uncomment below)
    # agent = BookingAgent()
    # asyncio.run(agent.run_interactive())