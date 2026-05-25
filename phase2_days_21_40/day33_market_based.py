"""
Day 33: Market-Based Multi-Agent Systems
=========================================
Skill: Market Mechanisms
Mini Project: Agent Marketplace

Economic mechanisms for agent coordination.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class ResourceType(str, Enum):
    """Types of resources"""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATA = "data"
    SKILL = "skill"
    TIME = "time"


@dataclass
class Resource:
    """A tradable resource"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resource_type: ResourceType = ResourceType.COMPUTE
    owner: str = ""
    quantity: float = 1.0
    price: float = 0.0
    unit: str = "unit"


@dataclass
class Bid:
    """A bid in the market"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bidder: str = ""
    resource_type: ResourceType = ResourceType.COMPUTE
    quantity: float = 1.0
    max_price: float = 100.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Ask:
    """An ask in the market"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    seller: str = ""
    resource_type: ResourceType = ResourceType.COMPUTE
    quantity: float = 1.0
    min_price: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class OrderBook:
    """Order book for a resource"""

    def __init__(self, resource_type: ResourceType):
        self.resource_type = resource_type
        self.bids: List[Bid] = []
        self.asks: List[Ask] = []

    def add_bid(self, bid: Bid):
        """Add a bid"""
        self.bids.append(bid)
        self.bids.sort(key=lambda x: x.max_price, reverse=True)

    def add_ask(self, ask: Ask):
        """Add an ask"""
        self.asks.append(ask)
        self.asks.sort(key=lambda x: x.min_price)

    def match(self) -> List[Dict[str, Any]]:
        """Match bids and asks"""
        matches = []

        while self.bids and self.asks:
            best_bid = self.bids[0]
            best_ask = self.asks[0]

            if best_bid.max_price >= best_ask.min_price:
                # Match!
                quantity = min(best_bid.quantity, best_ask.quantity)
                price = (best_bid.max_price + best_ask.min_price) / 2

                matches.append({
                    "bid_id": best_bid.id,
                    "ask_id": best_ask.id,
                    "bidder": best_bid.bidder,
                    "seller": best_ask.seller,
                    "quantity": quantity,
                    "price": price
                })

                # Update quantities
                best_bid.quantity -= quantity
                best_ask.quantity -= quantity

                # Remove if fully matched
                if best_bid.quantity <= 0:
                    self.bids.pop(0)
                if best_ask.quantity <= 0:
                    self.asks.pop(0)
            else:
                break

        return matches

    def get_spread(self) -> Optional[Dict[str, float]]:
        """Get bid-ask spread"""
        if not self.bids or not self.asks:
            return None

        return {
            "bid": self.bids[0].max_price,
            "ask": self.asks[0].min_price,
            "spread": self.asks[0].min_price - self.bids[0].max_price
        }


class AgentMarketplace:
    """Marketplace for agent resources"""

    def __init__(self):
        self.order_books: Dict[ResourceType, OrderBook] = {}
        self.transactions: List[Dict] = []
        self.agents: Dict[str, Dict] = {}

    def create_order_book(self, resource_type: ResourceType):
        """Create order book for resource"""
        self.order_books[resource_type] = OrderBook(resource_type)

    def register_agent(self, agent_id: str, balance: float = 1000.0):
        """Register an agent"""
        self.agents[agent_id] = {
            "balance": balance,
            "holdings": defaultdict(float)
        }

    def place_bid(
        self,
        agent_id: str,
        resource_type: ResourceType,
        quantity: float,
        max_price: float
    ) -> bool:
        """Place a bid"""
        if agent_id not in self.agents:
            return False

        if resource_type not in self.order_books:
            self.create_order_book(resource_type)

        bid = Bid(
            bidder=agent_id,
            resource_type=resource_type,
            quantity=quantity,
            max_price=max_price
        )

        self.order_books[resource_type].add_bid(bid)
        return True

    def place_ask(
        self,
        agent_id: str,
        resource_type: ResourceType,
        quantity: float,
        min_price: float
    ) -> bool:
        """Place an ask"""
        if agent_id not in self.agents:
            return False

        if resource_type not in self.order_books:
            self.create_order_book(resource_type)

        ask = Ask(
            seller=agent_id,
            resource_type=resource_type,
            quantity=quantity,
            min_price=min_price
        )

        self.order_books[resource_type].add_ask(ask)
        return True

    async def clear_market(self, resource_type: ResourceType) -> List[Dict]:
        """Clear the market"""
        if resource_type not in self.order_books:
            return []

        order_book = self.order_books[resource_type]
        matches = order_book.match()

        # Execute transactions
        for match in matches:
            buyer = match["bidder"]
            seller = match["seller"]
            quantity = match["quantity"]
            price = match["price"]

            # Update balances
            self.agents[buyer]["balance"] -= price * quantity
            self.agents[seller]["balance"] += price * quantity

            # Update holdings
            self.agents[buyer]["holdings"][resource_type.value] += quantity
            self.agents[seller]["holdings"][resource_type.value] -= quantity

            # Record transaction
            self.transactions.append({
                **match,
                "timestamp": datetime.now().isoformat()
            })

        return matches

    def get_price(self, resource_type: ResourceType) -> Optional[float]:
        """Get current market price"""
        if resource_type not in self.order_books:
            return None

        spread = self.order_books[resource_type].get_spread()
        if spread:
            return (spread["bid"] + spread["ask"]) / 2
        return None

    def get_agent_balance(self, agent_id: str) -> float:
        """Get agent balance"""
        return self.agents.get(agent_id, {}).get("balance", 0.0)


class DutchAuction:
    """Dutch auction (descending price)"""

    def __init__(self, item: str, starting_price: float, min_price: float):
        self.item = item
        self.starting_price = starting_price
        self.min_price = min_price
        self.current_price = starting_price
        self.bids: List[Dict] = []
        self.closed = False

    def place_bid(self, agent_id: str) -> Dict:
        """Place bid at current price"""
        if self.closed:
            return {"success": False, "error": "Auction closed"}

        bid = {
            "agent": agent_id,
            "price": self.current_price,
            "timestamp": datetime.now().isoformat()
        }
        self.bids.append(bid)
        self.closed = True

        return {
            "success": True,
            "price": self.current_price,
            "item": self.item
        }

    def lower_price(self, decrement: float = 1.0):
        """Lower the price"""
        if self.current_price - decrement >= self.min_price:
            self.current_price -= decrement

    def get_status(self) -> Dict:
        """Get auction status"""
        return {
            "item": self.item,
            "price": self.current_price,
            "bids": len(self.bids),
            "closed": self.closed
        }


# Demo
def run_demo():
    print("=" * 70)
    print("Market-Based Multi-Agent Systems Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create marketplace
        marketplace = AgentMarketplace()

        # Register agents
        print("\n[1] Register Agents")
        print("-" * 40)

        marketplace.register_agent("Buyer1", 1000.0)
        marketplace.register_agent("Buyer2", 800.0)
        marketplace.register_agent("Seller1", 500.0)
        marketplace.register_agent("Seller2", 500.0)

        for agent_id, agent in marketplace.agents.items():
            print(f"  {agent_id}: ${agent['balance']:.2f}")

        # Place orders
        print("\n[2] Place Orders")
        print("-" * 40)

        marketplace.place_bid("Buyer1", ResourceType.COMPUTE, 10, 50.0)
        marketplace.place_bid("Buyer2", ResourceType.COMPUTE, 5, 40.0)
        marketplace.place_ask("Seller1", ResourceType.COMPUTE, 8, 35.0)
        marketplace.place_ask("Seller2", ResourceType.COMPUTE, 5, 45.0)

        print("  Buyer1 bids: 10 units @ $50")
        print("  Buyer2 bids: 5 units @ $40")
        print("  Seller1 asks: 8 units @ $35")
        print("  Seller2 asks: 5 units @ $45")

        # Clear market
        print("\n[3] Clear Market")
        print("-" * 40)

        matches = await marketplace.clear_market(ResourceType.COMPUTE)
        print(f"  Matches: {len(matches)}")

        for match in matches:
            print(f"    {match['bidder']} buys {match['quantity']} @ ${match['price']:.2f}")

        # Check balances after
        print("\n[4] Balances After")
        print("-" * 40)

        for agent_id, agent in marketplace.agents.items():
            print(f"  {agent_id}: ${agent['balance']:.2f}")

        # Price
        print("\n[5] Market Price")
        print("-" * 40)

        price = marketplace.get_price(ResourceType.COMPUTE)
        print(f"  Current price: ${price:.2f}" if price else "  No price")

        # Dutch auction
        print("\n[6] Dutch Auction")
        print("-" * 40)

        auction = DutchAuction("GPU Compute", 100.0, 50.0)

        for i in range(6):
            status = auction.get_status()
            print(f"  Round {i+1}: ${status['price']:.2f}")

            if status['price'] <= 70:
                result = auction.place_bid(f"Buyer{i+1}")
                if result['success']:
                    print(f"    Sold to {result.get('bid', {}).get('agent', 'Buyer')} @ ${result['price']:.2f}")
                break

            auction.lower_price(10.0)

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()