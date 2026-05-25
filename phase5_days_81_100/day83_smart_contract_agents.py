"""
Day 83: Smart Contract Agents
==============================

Autonomous agents that interact with blockchain smart contracts
for secure, trustless operations.

Key Concepts:
- Smart contract interaction
- Blockchain transactions
- Token operations
- Decentralized governance
- Atomic swaps
- Contract verification
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json


class ContractType(Enum):
    """Types of smart contracts"""
    TOKEN = "token"
    STORAGE = "storage"
    GOVERNANCE = "governance"
    ORACLE = "oracle"
    DAO = "dao"


class TransactionStatus(Enum):
    """Transaction status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class SmartContract:
    """Represents a smart contract"""
    address: str
    name: str
    contract_type: ContractType
    abi: List[Dict]
    bytecode: str
    deployed_at: datetime = field(default_factory=datetime.now)


@dataclass
class Transaction:
    """Blockchain transaction"""
    tx_hash: str
    from_address: str
    to_address: str
    value: float
    gas_used: int
    status: TransactionStatus
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentWallet:
    """Agent wallet for blockchain operations"""
    address: str
    balance: float
    tokens: Dict[str, float] = field(default_factory=dict)
    nonce: int = 0


class ContractExecutor:
    """
    Contract Executor
    =================

    Executes smart contract functions.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.deployed_contracts: Dict[str, SmartContract] = {}

    def deploy_contract(
        self,
        name: str,
        contract_type: ContractType,
        bytecode: str,
        abi: List[Dict]
    ) -> SmartContract:
        """Deploy a new smart contract"""
        # Simulate contract deployment
        address = f"0x{hashlib.sha256(name.encode()).hexdigest()[:40]}"

        contract = SmartContract(
            address=address,
            name=name,
            contract_type=contract_type,
            bytecode=bytecode,
            abi=abi,
            deployed_at=datetime.now()
        )

        self.deployed_contracts[address] = contract
        return contract

    def call_function(
        self,
        contract_address: str,
        function_name: str,
        params: Dict[str, Any],
        wallet: AgentWallet
    ) -> Transaction:
        """Call a contract function"""
        contract = self.deployed_contracts.get(contract_address)
        if not contract:
            raise ValueError(f"Contract not found: {contract_address}")

        # Simulate transaction
        tx_hash = hashlib.sha256(
            f"{wallet.address}{contract_address}{function_name}".encode()
        ).hexdigest()

        tx = Transaction(
            tx_hash=tx_hash,
            from_address=wallet.address,
            to_address=contract_address,
            value=0,
            gas_used=21000,
            status=TransactionStatus.CONFIRMED,
            data={
                "function": function_name,
                "params": params
            }
        )

        wallet.nonce += 1
        return tx


class TokenManager:
    """
    Token Manager
    =============

    Manages token operations for agents.
    """

    def __init__(self):
        self.token_balances: Dict[str, Dict[str, float]] = {}

    def create_token(
        self,
        name: str,
        symbol: str,
        total_supply: float,
        decimals: int = 18
    ) -> Dict[str, Any]:
        """Create a new token"""
        token_id = hashlib.md5(name.encode()).hexdigest()[:8]

        token_info = {
            "token_id": token_id,
            "name": name,
            "symbol": symbol,
            "total_supply": total_supply,
            "decimals": decimals,
            "circulating": 0
        }

        self.token_balances[token_id] = {}
        return token_info

    def mint(
        self,
        token_id: str,
        to_address: str,
        amount: float
    ):
        """Mint tokens to an address"""
        if token_id not in self.token_balances:
            self.token_balances[token_id] = {}

        if to_address not in self.token_balances[token_id]:
            self.token_balances[token_id][to_address] = 0

        self.token_balances[token_id][to_address] += amount

    def transfer(
        self,
        token_id: str,
        from_address: str,
        to_address: str,
        amount: float
    ) -> bool:
        """Transfer tokens between addresses"""
        if token_id not in self.token_balances:
            return False

        balances = self.token_balances[token_id]
        from_balance = balances.get(from_address, 0)

        if from_balance < amount:
            return False

        # Execute transfer
        balances[from_address] -= amount
        if to_address not in balances:
            balances[to_address] = 0
        balances[to_address] += amount

        return True

    def get_balance(self, token_id: str, address: str) -> float:
        """Get token balance for an address"""
        if token_id not in self.token_balances:
            return 0
        return self.token_balances[token_id].get(address, 0)


class GovernanceController:
    """
    Governance Controller
    ======================

    Manages DAO-style governance for agent systems.
    """

    def __init__(self):
        self.proposals: Dict[str, Dict] = {}
        self.votes: Dict[str, List[Dict]] = {}

    def create_proposal(
        self,
        title: str,
        description: str,
        proposer: str,
        voting_period: int = 7
    ) -> str:
        """Create a governance proposal"""
        proposal_id = hashlib.sha256(title.encode()).hexdigest()[:8]

        proposal = {
            "id": proposal_id,
            "title": title,
            "description": description,
            "proposer": proposer,
            "status": "active",
            "votes_for": 0,
            "votes_against": 0,
            "voting_ends": datetime.now(),
            "voting_period": voting_period
        }

        self.proposals[proposal_id] = proposal
        self.votes[proposal_id] = []

        return proposal_id

    def vote(
        self,
        proposal_id: str,
        voter: str,
        support: bool,
        weight: float = 1.0
    ):
        """Cast a vote on a proposal"""
        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal not found: {proposal_id}")

        proposal = self.proposals[proposal_id]

        # Record vote
        vote = {
            "voter": voter,
            "support": support,
            "weight": weight,
            "timestamp": datetime.now()
        }
        self.votes[proposal_id].append(vote)

        # Update proposal counts
        if support:
            proposal["votes_for"] += weight
        else:
            proposal["votes_against"] += weight

    def execute_proposal(self, proposal_id: str) -> bool:
        """Execute a passed proposal"""
        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]

        # Check if proposal passed
        total_votes = proposal["votes_for"] + proposal["votes_against"]
        if total_votes == 0:
            return False

        passed = proposal["votes_for"] > proposal["votes_against"]

        if passed:
            proposal["status"] = "executed"
            return True
        else:
            proposal["status"] = "rejected"
            return False


class SmartContractAgent:
    """
    Smart Contract Agent
    ====================

    Autonomous agent for blockchain operations.
    """

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.wallet = AgentWallet(
            address=f"0x{hashlib.sha256(agent_id.encode()).hexdigest()[:40]}",
            balance=100.0
        )
        self.contract_executor = ContractExecutor(agent_id)
        self.token_manager = TokenManager()
        self.governance = GovernanceController()

    def deploy_token(
        self,
        name: str,
        symbol: str,
        supply: float
    ) -> Dict[str, Any]:
        """Deploy a new token"""
        token_info = self.token_manager.create_token(name, symbol, supply)

        # Mint initial supply to agent wallet
        self.token_manager.mint(
            token_info["token_id"],
            self.wallet.address,
            supply
        )

        print(f"[{self.name}] Deployed token {symbol} at {self.wallet.address}")
        return token_info

    def submit_proposal(
        self,
        title: str,
        description: str
    ) -> str:
        """Submit a governance proposal"""
        proposal_id = self.governance.create_proposal(
            title, description, self.wallet.address
        )
        print(f"[{self.name}] Submitted proposal: {title}")
        return proposal_id


def main():
    """Demonstrate Smart Contract Agents"""
    print("=" * 60)
    print("Smart Contract Agents - Day 83")
    print("=" * 60)

    # Create agent
    agent = SmartContractAgent("agent_001", "BlockchainAgent")

    # Deploy token
    print("\n[Deploying Token]")
    token = agent.deploy_token("AgentOS Token", "AOS", 1000000)
    print(f"  Token: {token['name']} ({token['symbol']})")
    print(f"  Supply: {token['total_supply']}")

    # Check balance
    balance = agent.token_manager.get_balance(
        token["token_id"],
        agent.wallet.address
    )
    print(f"  Agent Balance: {balance}")

    # Create governance proposal
    print("\n[Governance Proposal]")
    proposal_id = agent.submit_proposal(
        "Increase Agent Rewards",
        "Proposal to increase rewards for high-performing agents"
    )

    # Simulate voting
    agent.governance.vote(proposal_id, "voter_1", True, 10.0)
    agent.governance.vote(proposal_id, "voter_2", True, 15.0)
    agent.governance.vote(proposal_id, "voter_3", False, 8.0)

    proposal = agent.governance.proposals[proposal_id]
    print(f"  Votes For: {proposal['votes_for']}")
    print(f"  Votes Against: {proposal['votes_against']}")

    # Execute proposal
    passed = agent.governance.execute_proposal(proposal_id)
    print(f"  Proposal Passed: {passed}")

    print("\n" + "=" * 60)
    print("Smart Contract demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()