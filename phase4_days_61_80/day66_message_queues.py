"""
Day 66: Message Queue Integration
==================================
Integrating agents with message queues for async communication.

Key Concepts:
- Task queues
- Priority handling
- Dead letter queues
- Message acknowledgment
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import heapq


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class QueueMessage:
    """A message in the queue"""
    message_id: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    retry_count: int = 0
    max_retries: int = 3


class PriorityQueue:
    """
    Priority Message Queue
    ======================

    Thread-safe priority queue for messages.
    """

    def __init__(self):
        self._queue: List[tuple] = []
        self._message_map: Dict[str, QueueMessage] = {}
        self._lock = asyncio.Lock()

    async def put(self, message: QueueMessage):
        """Add message to queue"""
        async with self._lock:
            heapq.heappush(
                self._queue,
                (message.priority.value, message.created_at, message.message_id)
            )
            self._message_map[message.message_id] = message

    async def get(self) -> Optional[QueueMessage]:
        """Get highest priority message"""
        async with self._lock:
            if not self._queue:
                return None

            _, _, message_id = heapq.heappop(self._queue)
            return self._message_map.get(message_id)

    async def get_by_id(self, message_id: str) -> Optional[QueueMessage]:
        """Get message by ID"""
        async with self._lock:
            return self._message_map.get(message_id)

    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message processing"""
        async with self._lock:
            if message_id in self._message_map:
                self._message_map[message_id].acknowledged = True
                return True
            return False

    async def size(self) -> int:
        """Get queue size"""
        async with self._lock:
            return len(self._queue)

    async def get_pending(self) -> List[QueueMessage]:
        """Get all pending messages"""
        async with self._lock:
            return [
                msg for msg in self._message_map.values()
                if not msg.acknowledged
            ]


class AgentMessageQueue:
    """
    Agent Message Queue
    ===================

    Message queue system for agent task distribution.
    """

    def __init__(self, max_concurrent: int = 10):
        self.main_queue = PriorityQueue()
        self.dead_letter_queue = PriorityQueue()
        self.max_concurrent = max_concurrent
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, task_type: str, handler: Callable):
        """Register a task handler"""
        self.handlers[task_type] = handler

    async def enqueue(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """Enqueue a task"""
        message = QueueMessage(
            message_id=str(uuid.uuid4()),
            payload={
                "task_type": task_type,
                "data": payload
            },
            priority=priority
        )

        await self.main_queue.put(message)
        return message.message_id

    async def process_queue(self):
        """Process messages from queue"""
        while True:
            # Check concurrency limit
            active_count = sum(
                1 for t in self.active_tasks.values()
                if not t.done()
            )

            if active_count >= self.max_concurrent:
                await asyncio.sleep(0.1)
                continue

            # Get message
            message = await self.main_queue.get()
            if not message:
                await asyncio.sleep(0.1)
                continue

            # Create processing task
            task = asyncio.create_task(self._process_message(message))
            self.active_tasks[message.message_id] = task

            # Cleanup finished tasks
            done = [k for k, v in self.active_tasks.items() if v.done()]
            for k in done:
                del self.active_tasks[k]

    async def _process_message(self, message: QueueMessage):
        """Process a single message"""
        task_type = message.payload.get("task_type")
        handler = self.handlers.get(task_type)

        try:
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message.payload.get("data", {}))
                else:
                    handler(message.payload.get("data", {}))

            # Acknowledge
            await self.main_queue.acknowledge(message.message_id)

        except Exception as e:
            # Handle retry
            message.retry_count += 1

            if message.retry_count < message.max_retries:
                # Requeue with slight delay
                await asyncio.sleep(0.5 * message.retry_count)
                await self.main_queue.put(message)
            else:
                # Move to dead letter queue
                await self.dead_letter_queue.put(message)

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "main_queue_size": len(self.active_tasks),
            "pending_tasks": len(self.active_tasks),
            "registered_handlers": list(self.handlers.keys())
        }


# Demo
async def main():
    print("=" * 60)
    print("Day 66: Message Queue Integration")
    print("=" * 60)

    queue = AgentMessageQueue(max_concurrent=5)

    # Register handlers
    async def handle_analysis(data: Dict):
        print(f"  Processing analysis: {data}")
        await asyncio.sleep(0.2)

    def handle_notification(data: Dict):
        print(f"  Sending notification: {data}")

    queue.register_handler("analysis", handle_analysis)
    queue.register_handler("notification", handle_notification)

    # Start queue processor
    processor = asyncio.create_task(queue.process_queue())

    # Enqueue tasks
    print("\nEnqueuing tasks...")
    for i in range(5):
        await queue.enqueue(
            "analysis",
            {"task_id": f"task_{i}", "data": f"data_{i}"},
            MessagePriority.NORMAL
        )

    await queue.enqueue(
        "notification",
        {"user": "admin", "message": "System alert"},
        MessagePriority.HIGH
    )

    # Wait for processing
    await asyncio.sleep(1)

    # Cancel processor
    processor.cancel()
    try:
        await processor
    except asyncio.CancelledError:
        pass

    # Stats
    print("\n" + "-" * 40)
    stats = queue.get_stats()
    print(f"Queue stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())