"""
Day 73: API Rate Limiting
==========================
Implementing rate limiting for API and agent requests.

Key Concepts:
- Token bucket algorithm
- Leaky bucket algorithm
- Per-user limits
- Global limits
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import time
import uuid


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    burst_limit: int = None


@dataclass
class RateLimitEntry:
    """Rate limit tracking entry"""
    user_id: str
    request_count: int = 0
    window_start: datetime = field(default_factory=datetime.now)
    tokens: float = 0
    last_request: datetime = field(default_factory=datetime.now)


class TokenBucketLimiter:
    """Token bucket rate limiter"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets: Dict[str, RateLimitEntry] = {}
        self._lock = asyncio.Lock()

    def _refill(self, entry: RateLimitEntry):
        """Refill tokens based on time elapsed"""
        now = datetime.now()
        elapsed = (now - entry.last_request).total_seconds()
        new_tokens = elapsed * self.refill_rate
        entry.tokens = min(self.capacity, entry.tokens + new_tokens)
        entry.last_request = now

    async def check_limit(self, user_id: str, cost: int = 1) -> bool:
        """Check if request is allowed"""
        async with self._lock:
            if user_id not in self.buckets:
                self.buckets[user_id] = RateLimitEntry(
                    user_id=user_id,
                    tokens=self.capacity
                )

            entry = self.buckets[user_id]
            self._refill(entry)

            if entry.tokens >= cost:
                entry.tokens -= cost
                return True

            return False

    async def get_remaining(self, user_id: str) -> int:
        """Get remaining requests"""
        if user_id not in self.buckets:
            return self.capacity

        entry = self.buckets[user_id]
        self._refill(entry)
        return int(entry.tokens)


class LeakyBucketLimiter:
    """Leaky bucket rate limiter"""

    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def check_limit(self, user_id: str) -> bool:
        """Check if request is allowed"""
        async with self._lock:
            now = time.time()

            if user_id not in self.buckets:
                self.buckets[user_id] = {
                    "level": 0,
                    "last_leak": now
                }

            bucket = self.buckets[user_id]

            # Leak tokens
            elapsed = now - bucket["last_leak"]
            leak_amount = elapsed * self.leak_rate
            bucket["level"] = max(0, bucket["level"] - leak_amount)
            bucket["last_leak"] = now

            # Check if we can add request
            if bucket["level"] < self.capacity:
                bucket["level"] += 1
                return True

            return False


class FixedWindowLimiter:
    """Fixed window rate limiter"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.windows: Dict[str, RateLimitEntry] = {}
        self._lock = asyncio.Lock()

    async def check_limit(self, user_id: str) -> bool:
        """Check if request is allowed"""
        async with self._lock:
            now = datetime.now()

            if user_id not in self.windows:
                self.windows[user_id] = RateLimitEntry(
                    user_id=user_id,
                    window_start=now
                )

            entry = self.windows[user_id]

            # Check if window has expired
            if (now - entry.window_start).total_seconds() >= self.window_seconds:
                entry.request_count = 0
                entry.window_start = now

            # Check limit
            if entry.request_count < self.max_requests:
                entry.request_count += 1
                return True

            return False

    async def get_remaining(self, user_id: str) -> int:
        """Get remaining requests"""
        if user_id not in self.windows:
            return self.max_requests

        entry = self.windows[user_id]
        return max(0, self.max_requests - entry.request_count)


class RateLimitManager:
    """
    Rate Limit Manager
    ==================

    Manages rate limiting across different strategies and scopes.
    """

    def __init__(self):
        self.limiters: Dict[str, Any] = {}
        self.default_config = RateLimitConfig(
            max_requests=60,
            window_seconds=60,
            strategy=RateLimitStrategy.TOKEN_BUCKET
        )
        self._lock = asyncio.Lock()

    def create_limiter(
        self,
        name: str,
        config: RateLimitConfig
    ) -> str:
        """Create a rate limiter"""
        limiter_id = str(uuid.uuid4())

        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            refill_rate = config.max_requests / config.window_seconds
            limiter = TokenBucketLimiter(
                config.burst_limit or config.max_requests,
                refill_rate
            )
        elif config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            limiter = LeakyBucketLimiter(
                config.max_requests,
                config.max_requests / config.window_seconds
            )
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            limiter = FixedWindowLimiter(
                config.max_requests,
                config.window_seconds
            )
        else:
            limiter = FixedWindowLimiter(
                config.max_requests,
                config.window_seconds
            )

        self.limiters[name] = limiter
        return limiter_id

    async def check_limit(
        self,
        limiter_name: str,
        user_id: str,
        cost: int = 1
    ) -> Dict[str, Any]:
        """Check rate limit for a request"""
        limiter = self.limiters.get(limiter_name)
        if not limiter:
            return {"allowed": True, "reason": "No limiter configured"}

        # Use appropriate check method
        if hasattr(limiter, 'check_limit'):
            try:
                allowed = await limiter.check_limit(user_id, cost)
            except TypeError:
                allowed = await limiter.check_limit(user_id)

            return {
                "allowed": allowed,
                "limiter": limiter_name,
                "retry_after": self.default_config.window_seconds if not allowed else None
            }

        return {"allowed": False, "reason": "Invalid limiter"}

    async def get_remaining(
        self,
        limiter_name: str,
        user_id: str
    ) -> int:
        """Get remaining requests"""
        limiter = self.limiters.get(limiter_name)
        if not limiter or not hasattr(limiter, 'get_remaining'):
            return -1

        return await limiter.get_remaining(user_id)

    def get_limiter_info(self) -> Dict[str, Any]:
        """Get limiter information"""
        info = {}
        for name, limiter in self.limiters.items():
            limiter_type = type(limiter).__name__
            info[name] = {"type": limiter_type}
        return info


class APIGateway:
    """
    API Gateway with Rate Limiting
    ===============================

    Demo API gateway demonstrating rate limiting.
    """

    def __init__(self, rate_limit_manager: RateLimitManager):
        self.rate_limit_manager = rate_limit_manager
        self.requests: Dict[str, List[datetime]] = {}

        # Create default limiter
        self.rate_limit_manager.create_limiter(
            "default",
            RateLimitConfig(
                max_requests=10,
                window_seconds=60,
                strategy=RateLimitStrategy.FIXED_WINDOW
            )
        )

    async def handle_request(
        self,
        user_id: str,
        endpoint: str,
        handler
    ) -> Dict[str, Any]:
        """Handle API request with rate limiting"""

        # Check rate limit
        result = await self.rate_limit_manager.check_limit("default", user_id)

        if not result["allowed"]:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": result.get("retry_after")
            }

        # Execute request
        try:
            result = await handler()
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Demo
async def main():
    print("=" * 60)
    print("Day 73: API Rate Limiting")
    print("=" * 60)

    # Create rate limit manager
    manager = RateLimitManager()

    # Create limiters
    print("\nCreating rate limiters...")

    # Standard API limit
    manager.create_limiter(
        "api_standard",
        RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            burst_limit=120
        )
    )

    # Strict limit for expensive operations
    manager.create_limiter(
        "api_strict",
        RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW
        )
    )

    print(f"Limiters: {list(manager.get_limiter_info().keys())}")

    # Test rate limiting
    print("\nTesting rate limit (10 requests allowed)...")

    for i in range(15):
        result = await manager.check_limit("api_strict", "user_1")
        status = "✓" if result["allowed"] else "✗"
        print(f"  Request {i+1}: {status} (allowed={result['allowed']})")

    remaining = await manager.get_remaining("api_strict", "user_1")
    print(f"\nRemaining requests: {remaining}")

    # Test API Gateway
    print("\nTesting API Gateway...")

    gateway = APIGateway(manager)

    async def some_handler():
        return {"message": "Success!"}

    for i in range(12):
        result = await gateway.handle_request("user_1", "/api/data", some_handler)
        status = "✓" if result["success"] else "✗"
        if not result["success"]:
            print(f"  Request {i+1}: {status} - {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())