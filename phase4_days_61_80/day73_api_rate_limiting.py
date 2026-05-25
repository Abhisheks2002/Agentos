"""
Day 73: API Rate Limiting
==========================
Implementing rate limiting for agent API endpoints.

Key Concepts:
- Token bucket algorithm
- Sliding window
- Rate limit headers
- Quota management
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    burst_allowance: int = 0


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None


class TokenBucket:
    """Token bucket rate limiter"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = datetime.now()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        async with self._lock:
            await self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def _refill(self):
        """Refill tokens based on elapsed time"""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        new_tokens = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    async def get_available(self) -> float:
        """Get available tokens"""
        async with self._lock:
            await self._refill()
            return self.tokens


class SlidingWindow:
    """Sliding window rate limiter"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: list = []
        self._lock = asyncio.Lock()

    async def check(self) -> bool:
        """Check if request is allowed"""
        async with self._lock:
            await self._cleanup()

            if len(self.requests) < self.max_requests:
                self.requests.append(datetime.now())
                return True

            return False

    async def _cleanup(self):
        """Remove old requests outside window"""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        self.requests = [r for r in self.requests if r > cutoff]

    async def get_remaining(self) -> int:
        """Get remaining requests"""
        async with self._lock:
            await self._cleanup()
            return max(0, self.max_requests - len(self.requests))


class RateLimiter:
    """
    API Rate Limiter
    =================

    Provides rate limiting for API endpoints.
    """

    def __init__(self):
        self.limiters: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindow] = {}
        self.configs: Dict[str, RateLimitConfig] = {}
        self.usage_history: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    def configure(
        self,
        endpoint: str,
        config: RateLimitConfig
    ):
        """Configure rate limit for endpoint"""
        self.configs[endpoint] = config

        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            rate = config.max_requests / config.window_seconds
            self.limiters[endpoint] = TokenBucket(
                capacity=config.max_requests + config.burst_allowance,
                refill_rate=rate
            )
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            self.sliding_windows[endpoint] = SlidingWindow(
                max_requests=config.max_requests,
                window_seconds=config.window_seconds
            )

    async def check_rate_limit(
        self,
        client_id: str,
        endpoint: str
    ) -> RateLimitResult:
        """Check if request is within rate limits"""
        key = f"{client_id}:{endpoint}"
        config = self.configs.get(endpoint)

        if not config:
            # No rate limit configured
            return RateLimitResult(
                allowed=True,
                remaining=9999,
                reset_at=datetime.now() + timedelta(hours=1)
            )

        allowed = False
        remaining = 0
        reset_at = datetime.now() + timedelta(seconds=config.window_seconds)

        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            limiter = self.limiters.get(key)
            if not limiter:
                rate = config.max_requests / config.window_seconds
                limiter = TokenBucket(
                    capacity=config.max_requests + config.burst_allowance,
                    refill_rate=rate
                )
                self.limiters[key] = limiter

            allowed = await limiter.consume()
            remaining = int(await limiter.get_available())

        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            window = self.sliding_windows.get(key)
            if not window:
                window = SlidingWindow(
                    max_requests=config.max_requests,
                    window_seconds=config.window_seconds
                )
                self.sliding_windows[key] = window

            allowed = await window.check()
            remaining = await window.get_remaining()

        # Record usage
        if allowed:
            self.usage_history[key].append(datetime.now())

        retry_after = None if allowed else config.window_seconds

        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after
        )

    def get_usage_stats(
        self,
        client_id: str = None,
        endpoint: str = None
    ) -> Dict[str, Any]:
        """Get usage statistics"""
        if client_id and endpoint:
            key = f"{client_id}:{endpoint}"
            history = self.usage_history.get(key, [])
            return {
                "total_requests": len(history),
                "recent_requests": len([
                    r for r in history
                    if r > datetime.now() - timedelta(hours=1)
                ])
            }

        # Overall stats
        total_requests = sum(len(h) for h in self.usage_history.values())
        return {
            "total_requests": total_requests,
            "unique_keys": len(self.usage_history)
        }

    def reset_limit(self, client_id: str, endpoint: str):
        """Reset rate limit for client/endpoint"""
        key = f"{client_id}:{endpoint}"
        if key in self.limiters:
            del self.limiters[key]
        if key in self.sliding_windows:
            del self.sliding_windows[key]


class RateLimitMiddleware:
    """
    Rate Limit Middleware
    =====================

    Middleware for applying rate limits to API requests.
    """

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.default_config = RateLimitConfig(
            max_requests=60,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )

    async def handle(
        self,
        client_id: str,
        endpoint: str,
        handler: Callable
    ) -> Dict[str, Any]:
        """Handle request with rate limiting"""
        # Check rate limit
        result = await self.rate_limiter.check_rate_limit(client_id, endpoint)

        if not result.allowed:
            return {
                "error": "Rate limit exceeded",
                "retry_after": result.retry_after,
                "remaining": 0
            }

        # Execute handler
        response = await handler() if asyncio.iscoroutinefunction(handler) else handler()

        # Add rate limit headers
        response["rate_limit"] = {
            "remaining": result.remaining,
            "reset_at": result.reset_at.isoformat()
        }

        return response


# Demo
async def main():
    print("=" * 60)
    print("Day 73: API Rate Limiting")
    print("=" * 60)

    # Create rate limiter
    limiter = RateLimiter()

    # Configure endpoints
    limiter.configure(
        "/api/agents",
        RateLimitConfig(
            max_requests=10,
            window_seconds=10,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
    )

    limiter.configure(
        "/api/tasks",
        RateLimitConfig(
            max_requests=5,
            window_seconds=10,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            burst_allowance=2
        )
    )

    print("\nTesting rate limiting...")

    # Test /api/agents endpoint
    client_id = "user_123"

    print(f"\nTesting /api/agents (max 10 req/10s):")
    for i in range(12):
        result = await limiter.check_rate_limit(client_id, "/api/agents")
        status = "✓" if result.allowed else "X"
        print(f"  Request {i+1}: {status} (remaining: {result.remaining})")
        await asyncio.sleep(0.2)

    # Test /api/tasks endpoint
    print(f"\nTesting /api/tasks (token bucket, burst 2):")
    for i in range(8):
        result = await limiter.check_rate_limit(client_id, "/api/tasks")
        status = "✓" if result.allowed else "X"
        print(f"  Request {i+1}: {status} (remaining: {result.remaining})")
        await asyncio.sleep(0.1)

    # Usage stats
    stats = limiter.get_usage_stats()
    print(f"\nUsage statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Unique keys: {stats['unique_keys']}")


if __name__ == "__main__":
    asyncio.run(main())