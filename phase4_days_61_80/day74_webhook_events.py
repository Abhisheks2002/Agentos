"""
Day 74: Webhook Events
======================
Event system with webhook support for external integrations.

Key Concepts:
- Event publishing
- Webhook delivery
- Retry logic
- Event filtering
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import hashlib
import hmac


class EventType(Enum):
    """Event types"""
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    ERROR_OCCURRED = "error.occurred"


class WebhookStatus(Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Event:
    """An event"""
    event_id: str
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"


@dataclass
class Webhook:
    """Webhook endpoint configuration"""
    webhook_id: str
    url: str
    events: List[EventType]
    secret: str = None
    active: bool = True
    retry_count: int = 3
    timeout: int = 30


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""
    delivery_id: str
    webhook_id: str
    event_id: str
    status: WebhookStatus = WebhookStatus.PENDING
    attempts: int = 0
    response_code: int = None
    response_body: str = None
    error: str = None
    created_at: datetime = field(default_factory=datetime.now)
    delivered_at: datetime = None


class EventBus:
    """
    Event Bus
    =========

    Publish-subscribe event system.
    """

    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = asyncio.Lock()

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable
    ):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable
    ):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(handler)

    async def publish(self, event: Event):
        """Publish an event"""
        async with self._lock:
            handlers = self.subscribers.get(event.event_type, [])

            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"Event handler error: {e}")


class WebhookManager:
    """
    Webhook Manager
    ==============

    Manages webhook endpoints and delivery.
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.webhooks: Dict[str, Webhook] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self._lock = asyncio.Lock()

        # Subscribe to all events by default
        self._setup_event_subscription()

    def _setup_event_subscription(self):
        """Setup event subscriptions"""
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._handle_event)

    async def _handle_event(self, event: Event):
        """Handle incoming events"""
        async with self._lock:
            # Find matching webhooks
            for webhook in self.webhooks.values():
                if not webhook.active:
                    continue

                if event.event_type in webhook.events:
                    await self._queue_delivery(webhook, event)

    async def register_webhook(
        self,
        url: str,
        events: List[EventType],
        secret: str = None
    ) -> Webhook:
        """Register a webhook"""
        webhook = Webhook(
            webhook_id=str(uuid.uuid4()),
            url=url,
            events=events,
            secret=secret
        )

        self.webhooks[webhook.webhook_id] = webhook
        return webhook

    async def _queue_delivery(self, webhook: Webhook, event: Event):
        """Queue webhook delivery"""
        delivery = WebhookDelivery(
            delivery_id=str(uuid.uuid4()),
            webhook_id=webhook.webhook_id,
            event_id=event.event_id
        )

        self.deliveries[delivery.delivery_id] = delivery
        asyncio.create_task(self._deliver_webhook(webhook, delivery, event))

    async def _deliver_webhook(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery,
        event: Event
    ):
        """Deliver webhook (simulated)"""
        delivery.attempts += 1

        try:
            # Simulate HTTP request
            await asyncio.sleep(0.1)  # Simulate network latency

            # Sign payload if secret is set
            payload = str(event.data)
            if webhook.secret:
                signature = hmac.new(
                    webhook.secret.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()

            # Simulate success (in real implementation, actual HTTP call)
            success = delivery.attempts < 3 or True  # Simulate success

            if success:
                delivery.status = WebhookStatus.DELIVERED
                delivery.response_code = 200
                delivery.delivered_at = datetime.now()
            else:
                delivery.status = WebhookStatus.FAILED
                delivery.error = "Simulated failure"

        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error = str(e)

            # Retry logic
            if delivery.attempts < webhook.retry_count:
                delivery.status = WebhookStatus.RETRYING
                await asyncio.sleep(2 ** delivery.attempts)
                asyncio.create_task(
                    self._deliver_webhook(webhook, delivery, event)
                )

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID"""
        return self.webhooks.get(webhook_id)

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all webhooks"""
        return [
            {
                "webhook_id": w.webhook_id,
                "url": w.url,
                "events": [e.value for e in w.events],
                "active": w.active
            }
            for w in self.webhooks.values()
        ]

    def get_delivery_status(
        self,
        webhook_id: str = None
    ) -> Dict[str, Any]:
        """Get delivery status"""
        deliveries = list(self.deliveries.values())

        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]

        return {
            "total": len(deliveries),
            "delivered": sum(1 for d in deliveries if d.status == WebhookStatus.DELIVERED),
            "failed": sum(1 for d in deliveries if d.status == WebhookStatus.FAILED),
            "pending": sum(1 for d in deliveries if d.status == WebhookStatus.PENDING)
        }


# Demo
async def main():
    print("=" * 60)
    print("Day 74: Webhook Events")
    print("=" * 60)

    # Create event bus and webhook manager
    event_bus = EventBus()
    webhook_manager = WebhookManager(event_bus)

    # Register webhooks
    print("\nRegistering webhooks...")

    webhook1 = await webhook_manager.register_webhook(
        url="https://example.com/hooks/taskNotifier",
        events=[
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED
        ],
        secret="my_secret_key"
    )

    webhook2 = await webhook_manager.register_webhook(
        url="https://example.com/hooks/agentMonitor",
        events=[
            EventType.AGENT_CREATED,
            EventType.AGENT_DELETED
        ]
    )

    print(f"  Registered: {webhook1.url}")
    print(f"  Registered: {webhook2.url}")

    # Publish some events
    print("\nPublishing events...")

    await event_bus.publish(Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.TASK_COMPLETED,
        data={"task_id": "task_001", "status": "success"}
    ))

    await event_bus.publish(Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.AGENT_CREATED,
        data={"agent_id": "agent_001", "name": "New Agent"}
    ))

    await event_bus.publish(Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.TASK_FAILED,
        data={"task_id": "task_002", "error": "Timeout"}
    ))

    # Wait for deliveries
    await asyncio.sleep(0.5)

    # Check status
    print("\nWebhook delivery status:")
    status = webhook_manager.get_delivery_status()
    print(f"  Total: {status['total']}")
    print(f"  Delivered: {status['delivered']}")
    print(f"  Failed: {status['failed']}")

    print("\nRegistered webhooks:")
    for wh in webhook_manager.list_webhooks():
        print(f"  - {wh['url']}")
        print(f"    Events: {', '.join(wh['events'])}")


if __name__ == "__main__":
    asyncio.run(main())