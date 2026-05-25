"""
Day 31: Agent Consensus Mechanisms
==================================
Skill: Consensus Algorithms
Mini Project: Voting System

Reaching agreements among multiple agents.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from collections import Counter


class ConsensusAlgorithm(str, Enum):
    """Consensus algorithms"""
    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    WEIGHTED = "weighted"
    VOTING = "voting"
    AUCTION = "auction"
    ROUND_ROBIN = "round_robin"


@dataclass
class Vote:
    """A vote from an agent"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    voter: str = ""
    candidate: str = ""
    weight: float = 1.0
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Proposal:
    """A proposal for consensus"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    proposer: str = ""
    options: List[str] = field(default_factory=list)
    votes: List[Vote] = field(default_factory=list)
    status: str = "pending"
    result: Optional[str] = None


class ConsensusManager:
    """Manages consensus among agents"""

    def __init__(self, algorithm: ConsensusAlgorithm = ConsensusAlgorithm.MAJORITY):
        self.algorithm = algorithm
        self.proposals: Dict[str, Proposal] = {}
        self.agents: Dict[str, float] = {}  # agent_id -> weight

    def register_agent(self, agent_id: str, weight: float = 1.0):
        """Register an agent with voting weight"""
        self.agents[agent_id] = weight

    def create_proposal(self, title: str, options: List[str], proposer: str) -> Proposal:
        """Create a new proposal"""
        proposal = Proposal(
            title=title,
            proposer=proposer,
            options=options
        )
        self.proposals[proposal.id] = proposal
        return proposal

    async def vote(
        self,
        proposal_id: str,
        voter: str,
        candidate: str,
        weight: float = None
    ) -> bool:
        """Cast a vote"""
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != "pending":
            return False

        if voter not in self.agents:
            return False

        vote = Vote(
            voter=voter,
            candidate=candidate,
            weight=weight or self.agents[voter]
        )
        proposal.votes.append(vote)
        return True

    async def reach_consensus(self, proposal_id: str) -> Dict[str, Any]:
        """Reach consensus on a proposal"""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"success": False, "error": "Proposal not found"}

        if self.algorithm == ConsensusAlgorithm.MAJORITY:
            return await self._majority_consensus(proposal)
        elif self.algorithm == ConsensusAlgorithm.UNANIMOUS:
            return await self._unanimous_consensus(proposal)
        elif self.algorithm == ConsensusAlgorithm.WEIGHTED:
            return await self._weighted_consensus(proposal)
        else:
            return {"success": False, "error": "Unknown algorithm"}

    async def _majority_consensus(self, proposal: Proposal) -> Dict[str, Any]:
        """Majority voting"""
        if not proposal.votes:
            return {"success": False, "error": "No votes"}

        # Count votes
        candidates = [v.candidate for v in proposal.votes]
        counts = Counter(candidates)
        winner = counts.most_common(1)[0]

        # Check if majority
        majority = len(proposal.votes) / 2
        success = winner[1] > majority

        proposal.status = "completed" if success else "failed"
        proposal.result = winner[0] if success else None

        return {
            "success": success,
            "winner": winner[0] if success else None,
            "votes": winner[1],
            "total": len(proposal.votes)
        }

    async def _unanimous_consensus(self, proposal: Proposal) -> Dict[str, Any]:
        """Unanimous agreement"""
        if not proposal.votes:
            return {"success": False, "error": "No votes"}

        candidates = [v.candidate for v in proposal.votes]
        unique_candidates = set(candidates)

        if len(unique_candidates) == 1:
            proposal.status = "completed"
            proposal.result = unique_candidates.pop()
            return {"success": True, "winner": proposal.result}

        return {"success": False, "error": "Not unanimous"}

    async def _weighted_consensus(self, proposal: Proposal) -> Dict[str, Any]:
        """Weighted voting"""
        if not proposal.votes:
            return {"success": False, "error": "No votes"}

        # Sum weights per candidate
        weights: Dict[str, float] = {}
        for vote in proposal.votes:
            if vote.candidate not in weights:
                weights[vote.candidate] = 0
            weights[vote.candidate] += vote.weight

        # Find winner
        winner = max(weights.items(), key=lambda x: x[1])
        total_weight = sum(weights.values())

        # Check if majority
        success = winner[1] > total_weight / 2

        proposal.status = "completed" if success else "failed"
        proposal.result = winner[0] if success else None

        return {
            "success": success,
            "winner": winner[0] if success else None,
            "weight": winner[1],
            "total_weight": total_weight
        }


class AuctionConsensus:
    """Auction-based consensus"""

    def __init__(self):
        self.auctions: Dict[str, Dict] = {}

    def create_auction(self, item: str, sellers: List[str]) -> str:
        """Create an auction"""
        auction_id = str(uuid.uuid4())
        self.auctions[auction_id] = {
            "item": item,
            "sellers": sellers,
            "bids": {},
            "status": "open"
        }
        return auction_id

    async def submit_bid(self, auction_id: str, bidder: str, amount: float) -> bool:
        """Submit a bid"""
        if auction_id not in self.auctions:
            return False

        auction = self.auctions[auction_id]
        if auction["status"] != "open":
            return False

        auction["bids"][bidder] = amount
        return True

    async def close_auction(self, auction_id: str) -> Dict[str, Any]:
        """Close auction and determine winner"""
        if auction_id not in self.auctions:
            return {"success": False}

        auction = self.auctions[auction_id]
        auction["status"] = "closed"

        if not auction["bids"]:
            return {"success": False, "error": "No bids"}

        # Highest bid wins
        winner = max(auction["bids"].items(), key=lambda x: x[1])

        return {
            "success": True,
            "item": auction["item"],
            "winner": winner[0],
            "amount": winner[1]
        }


class DelegatedConsensus(ConsensusManager):
    """Liquid democracy - delegate votes"""

    def __init__(self):
        super().__init__(ConsensusAlgorithm.WEIGHTED)
        self.delegations: Dict[str, str] = {}  # voter -> delegate

    def delegate_vote(self, voter: str, delegate: str):
        """Delegate voting power"""
        if delegate in self.agents:
            self.delegations[voter] = delegate

    async def vote_with_delegation(
        self,
        proposal_id: str,
        voter: str,
        candidate: str
    ) -> bool:
        """Vote with delegation"""
        actual_voter = self.delegations.get(voter, voter)
        return await self.vote(proposal_id, actual_voter, candidate)


# Demo
def run_demo():
    print("=" * 70)
    print("Agent Consensus Mechanisms Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create consensus manager
        manager = ConsensusManager(ConsensusAlgorithm.MAJORITY)

        # Register agents
        print("\n[1] Register Agents")
        print("-" * 40)

        manager.register_agent("Alice", 1.0)
        manager.register_agent("Bob", 1.0)
        manager.register_agent("Carol", 1.0)
        manager.register_agent("Dave", 2.0)  # Weighted more

        print(f"  Registered {len(manager.agents)} agents")

        # Create proposal
        print("\n[2] Create Proposal")
        print("-" * 40)

        proposal = manager.create_proposal(
            "Choose framework",
            ["React", "Vue", "Angular"],
            "Alice"
        )
        print(f"  Proposal: {proposal.title}")
        print(f"  Options: {proposal.options}")

        # Cast votes
        print("\n[3] Cast Votes")
        print("-" * 40)

        await manager.vote(proposal.id, "Alice", "React")
        await manager.vote(proposal.id, "Bob", "React")
        await manager.vote(proposal.id, "Carol", "Vue")
        await manager.vote(proposal.id, "Dave", "Vue")  # Weighted

        print(f"  Alice -> React")
        print(f"  Bob -> React")
        print(f"  Carol -> Vue")
        print(f"  Dave -> Vue (weight: 2.0)")

        # Reach consensus
        print("\n[4] Majority Consensus")
        print("-" * 40)

        result = await manager.reach_consensus(proposal.id)
        print(f"  Success: {result['success']}")
        print(f"  Winner: {result.get('winner')}")
        print(f"  Votes: {result.get('votes')}/{result.get('total')}")

        # Unanimous consensus
        print("\n[5] Unanimous Consensus")
        print("-" * 40)

        manager2 = ConsensusManager(ConsensusAlgorithm.UNANIMOUS)
        for agent in ["Alice", "Bob", "Carol"]:
            manager2.register_agent(agent)

        prop2 = manager2.create_proposal("All agree?", ["Yes", "No"], "Alice")
        await manager2.vote(prop2.id, "Alice", "Yes")
        await manager2.vote(prop2.id, "Bob", "Yes")
        await manager2.vote(prop2.id, "Carol", "Yes")

        result2 = await manager2.reach_consensus(prop2.id)
        print(f"  Unanimous: {result2['success']}")
        print(f"  Winner: {result2.get('winner')}")

        # Auction
        print("\n[6] Auction Consensus")
        print("-" * 40)

        auction = AuctionConsensus()
        auction_id = auction.create_auction("API License", ["Seller1", "Seller2"])

        await auction.submit_bid(auction_id, "Buyer1", 100)
        await auction.submit_bid(auction_id, "Buyer2", 150)
        await auction.submit_bid(auction_id, "Buyer3", 120)

        result3 = await auction.close_auction(auction_id)
        print(f"  Winner: {result3.get('winner')}")
        print(f"  Amount: ${result3.get('amount')}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()