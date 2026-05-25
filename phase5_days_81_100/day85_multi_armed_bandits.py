"""
Day 85: Multi-Armed Bandits for Agents
======================================

Implementing Multi-Armed Bandit algorithms for agent decision-making,
providing smarter exploration-exploitation strategies compared to A/B testing.

Key Concepts:
- Exploration vs Exploitation
- Epsilon-greedy strategy
- UCB (Upper Confidence Bound)
- Thompson Sampling
- Contextual Bandits
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import random
import math
from collections import defaultdict
import json


class BanditAlgorithm(Enum):
    """Multi-armed bandit algorithms"""
    EPSILON_GREEDY = "epsilon_greedy"
    UCB1 = "ucb1"
    UCB2 = "ucb2"
    THOMPSON_SAMPLING = "thompson_sampling"
    EPSILON_DECAYING = "epsilon_decaying"
    SOFTMAX = "softmax"


class ArmType(Enum):
    """Type of bandit arm"""
    AGENT_CONFIG = "agent_config"
    PROMPT_STRATEGY = "prompt_strategy"
    TOOL_SELECTION = "tool_selection"
    ROUTING = "routing"


@dataclass
class Arm:
    """Represents a bandit arm (option/choice)"""
    arm_id: str
    name: str
    description: str
    config: Dict[str, Any]
    arm_type: ArmType = ArmType.AGENT_CONFIG


@dataclass
class ArmReward:
    """Tracks reward for an arm"""
    arm_id: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArmStatistics:
    """Statistics for a bandit arm"""
    arm_id: str
    pull_count: int = 0
    total_reward: float = 0.0
    rewards: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def mean_reward(self) -> float:
        """Calculate mean reward"""
        if self.pull_count == 0:
            return 0.0
        return self.total_reward / self.pull_count

    @property
    def variance(self) -> float:
        """Calculate reward variance"""
        if self.pull_count < 2:
            return 0.0
        mean = self.mean_reward
        return sum((r - mean) ** 2 for r in self.rewards) / (self.pull_count - 1)


class EpsilonGreedy:
    """
    Epsilon-Greedy Algorithm
    ========================

    With probability epsilon, explore (choose random arm).
    With probability 1-epsilon, exploit (choose best known arm).
    """

    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon

    def select_arm(self, arms: Dict[str, ArmStatistics]) -> Optional[str]:
        """Select an arm using epsilon-greedy strategy"""
        if not arms:
            return None

        # Explore: random arm
        if random.random() < self.epsilon:
            return random.choice(list(arms.keys()))

        # Exploit: best arm
        best_arm = max(arms.keys(), key=lambda a: arms[a].mean_reward)
        return best_arm

    def update(self, arms: Dict[str, ArmStatistics], arm_id: str, reward: float):
        """Update arm statistics"""
        if arm_id not in arms:
            arms[arm_id] = ArmStatistics(arm_id=arm_id)

        arms[arm_id].pull_count += 1
        arms[arm_id].total_reward += reward
        arms[arm_id].rewards.append(reward)
        arms[arm_id].last_updated = datetime.now()


class EpsilonDecaying:
    """
    Epsilon-Decaying Algorithm
    ==========================

    Epsilon starts high and decays over time, transitioning from
    exploration to exploitation.
    """

    def __init__(self, initial_epsilon: float = 1.0, decay_rate: float = 0.995, min_epsilon: float = 0.01):
        self.initial_epsilon = initial_epsilon
        self.decay_rate = decay_rate
        self.min_epsilon = min_epsilon
        self.current_epsilon = initial_epsilon
        self.total_pulls = 0

    def select_arm(self, arms: Dict[str, ArmStatistics]) -> Optional[str]:
        """Select an arm using epsilon-decaying strategy"""
        if not arms:
            return None

        # Explore: random arm
        if random.random() < self.current_epsilon:
            return random.choice(list(arms.keys()))

        # Exploit: best arm
        best_arm = max(arms.keys(), key=lambda a: arms[a].mean_reward)
        return best_arm

    def update(self, arms: Dict[str, ArmStatistics], arm_id: str, reward: float):
        """Update arm statistics and decay epsilon"""
        if arm_id not in arms:
            arms[arm_id] = ArmStatistics(arm_id=arm_id)

        arms[arm_id].pull_count += 1
        arms[arm_id].total_reward += reward
        arms[arm_id].rewards.append(reward)
        arms[arm_id].last_updated = datetime.now()

        # Decay epsilon
        self.total_pulls += 1
        self.current_epsilon = max(
            self.min_epsilon,
            self.initial_epsilon * (self.decay_rate ** self.total_pulls)
        )


class UCB1:
    """
    UCB1 (Upper Confidence Bound 1)
    ===============================

    Balances exploration-exploitation using confidence bounds.
    """

    def __init__(self, exploration_param: float = 2.0):
        self.exploration_param = exploration_param

    def select_arm(self, arms: Dict[str, ArmStatistics]) -> Optional[str]:
        """Select an arm using UCB1"""
        if not arms:
            return None

        total_pulls = sum(a.pull_count for a in arms.values())

        # If any arm hasn't been pulled, pull it first
        for arm_id, stats in arms.items():
            if stats.pull_count == 0:
                return arm_id

        # Calculate UCB score for each arm
        def ucb_score(arm_id: str) -> float:
            stats = arms[arm_id]
            exploitation = stats.mean_reward
            exploration = self.exploration_param * math.sqrt(
                math.log(total_pulls) / stats.pull_count
            )
            return exploitation + exploration

        return max(arms.keys(), key=ucb_score)

    def update(self, arms: Dict[str, ArmStatistics], arm_id: str, reward: float):
        """Update arm statistics"""
        if arm_id not in arms:
            arms[arm_id] = ArmStatistics(arm_id=arm_id)

        arms[arm_id].pull_count += 1
        arms[arm_id].total_reward += reward
        arms[arm_id].rewards.append(reward)
        arms[arm_id].last_updated = datetime.now()


class UCB2:
    """
    UCB2 (Improved Upper Confidence Bound)
    =======================================

    More sophisticated UCB with logarithmic exploration bonus.
    """

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.r = 1  # Current round

    def select_arm(self, arms: Dict[str, ArmStatistics]) -> Optional[str]:
        """Select an arm using UCB2"""
        if not arms:
            return None

        # Check if we should explore new arms
        for arm_id, stats in arms.items():
            if stats.pull_count == 0:
                return arm_id

        total_pulls = sum(a.pull_count for a in arms.values())

        # Calculate r (exploration rounds)
        self.r = int(math.log(total_pulls) + 1) + 1

        def ucb2_score(arm_id: str) -> float:
            stats = arms[arm_id]
            exploitation = stats.mean_reward

            # Exploration term
            delta = self.exploration_param(stats.pull_count)
            exploration = math.sqrt(
                (1 + delta) * math.log(math.e * total_pulls / stats.pull_count) / stats.pull_count
            )

            return exploitation + exploration

        return max(arms.keys(), key=ucb2_score)

    def exploration_param(self, n: int) -> float:
        """Calculate exploration parameter"""
        return self.alpha * math.log(self.r) / n

    def update(self, arms: Dict[str, ArmStatistics], arm_id: str, reward: float):
        """Update arm statistics"""
        if arm_id not in arms:
            arms[arm_id] = ArmStatistics(arm_id=arm_id)

        arms[arm_id].pull_count += 1
        arms[arm_id].total_reward += reward
        arms[arm_id].rewards.append(reward)
        arms[arm_id].last_updated = datetime.now()


class ThompsonSampling:
    """
    Thompson Sampling
    =================

    Bayesian approach that maintains a probability distribution
    over arm reward rates and samples from posterior.
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        """
        Initialize with Beta prior for Bernoulli rewards
        """
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.alpha = defaultdict(lambda: prior_alpha)
        self.beta = defaultdict(lambda: prior_beta)

    def select_arm(self, arms: Dict[str, ArmStatistics]) -> Optional[str]:
        """Select an arm using Thompson Sampling"""
        if not arms:
            return None

        # Sample from posterior for each arm
        samples = {}
        for arm_id in arms.keys():
            samples[arm_id] = random.beta(self.alpha[arm_id], self.beta[arm_id])

        # Choose arm with highest sample
        return max(samples.keys(), key=lambda a: samples[a])

    def update(self, arms: Dict[str, ArmStatistics], arm_id: str, reward: float):
        """Update posterior parameters"""
        # Convert reward to binary (for Bernoulli)
        binary_reward = 1.0 if reward > 0 else 0.0

        self.alpha[arm_id] += binary_reward
        self.beta[arm_id] += (1 - binary_reward)

        # Also update ArmStatistics
        if arm_id not in arms:
            arms[arm_id] = ArmStatistics(arm_id=arm_id)

        arms[arm_id].pull_count += 1
        arms[arm_id].total_reward += reward
        arms[arm_id].rewards.append(reward)
        arms[arm_id].last_updated = datetime.now()


class Softmax:
    """
    Softmax (Boltzmann) Exploration
    ===============================

    Chooses arms based on exponential weighting of their mean rewards.
    """

    def __init__(self, temperature: float = 1.0):
        self.temperature = temperature

    def select_arm(self, arms: Dict[str, ArmStatistics]) -> Optional[str]:
        """Select an arm using Softmax"""
        if not arms:
            return None

        # Calculate exp-weighted probabilities
        exp_weights = {}
        for arm_id, stats in arms.items():
            exp_weights[arm_id] = math.exp(stats.mean_reward / self.temperature)

        total = sum(exp_weights.values())
        if total == 0:
            return random.choice(list(arms.keys()))

        # Normalize and sample
        probs = [exp_weights[a] / total for a in arms.keys()]
        arm_ids = list(arms.keys())

        return random.choices(arm_ids, weights=probs, k=1)[0]

    def update(self, arms: Dict[str, ArmStatistics], arm_id: str, reward: float):
        """Update arm statistics"""
        if arm_id not in arms:
            arms[arm_id] = ArmStatistics(arm_id=arm_id)

        arms[arm_id].pull_count += 1
        arms[arm_id].total_reward += reward
        arms[arm_id].rewards.append(reward)
        arms[arm_id].last_updated = datetime.now()


class MultiArmedBandit:
    """
    Multi-Armed Bandit Framework
    =============================

    Complete MAB implementation with multiple algorithms.
    """

    def __init__(
        self,
        bandit_id: str,
        name: str,
        algorithm: BanditAlgorithm = BanditAlgorithm.EPSILON_GREEDY,
        arms: Optional[List[Arm]] = None
    ):
        self.bandit_id = bandit_id
        self.name = name
        self.algorithm = algorithm
        self.arms = {arm.arm_id: arm for arm in (arms or [])}
        self.arm_stats: Dict[str, ArmStatistics] = {}
        self.rewards_history: List[ArmReward] = []
        self.total_pulls = 0

        # Initialize algorithm
        self._init_algorithm()

    def _init_algorithm(self):
        """Initialize the bandit algorithm"""
        if self.algorithm == BanditAlgorithm.EPSILON_GREEDY:
            self.selector = EpsilonGreedy(epsilon=0.1)
        elif self.algorithm == BanditAlgorithm.EPSILON_DECAYING:
            self.selector = EpsilonDecaying()
        elif self.algorithm == BanditAlgorithm.UCB1:
            self.selector = UCB1()
        elif self.algorithm == BanditAlgorithm.UCB2:
            self.selector = UCB2()
        elif self.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            self.selector = ThompsonSampling()
        elif self.algorithm == BanditAlgorithm.SOFTMAX:
            self.selector = Softmax(temperature=1.0)
        else:
            self.selector = EpsilonGreedy(epsilon=0.1)

    def add_arm(self, arm: Arm):
        """Add a new arm to the bandit"""
        self.arms[arm.arm_id] = arm
        self.arm_stats[arm.arm_id] = ArmStatistics(arm_id=arm.arm_id)

    def select_arm(self) -> Optional[str]:
        """Select an arm using the configured algorithm"""
        return self.selector.select_arm(self.arm_stats)

    def pull_arm(self, arm_id: str, reward: float, context: Optional[Dict] = None):
        """Pull an arm and receive reward"""
        self.selector.update(self.arm_stats, arm_id, reward)
        self.rewards_history.append(ArmReward(
            arm_id=arm_id,
            value=reward,
            context=context or {}
        ))
        self.total_pulls += 1

    def get_best_arm(self) -> Optional[str]:
        """Get the currently best arm based on observed rewards"""
        if not self.arm_stats:
            return None
        return max(self.arm_stats.keys(), key=lambda a: self.arm_stats[a].mean_reward)

    def get_arm_config(self, arm_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for an arm"""
        arm = self.arms.get(arm_id)
        return arm.config if arm else None

    def get_statistics(self) -> Dict[str, Any]:
        """Get bandit statistics"""
        stats = {
            "bandit_id": self.bandit_id,
            "name": self.name,
            "algorithm": self.algorithm.value,
            "total_pulls": self.total_pulls,
            "best_arm": self.get_best_arm(),
            "arms": {}
        }

        for arm_id, arm_stat in self.arm_stats.items():
            arm_name = self.arms.get(arm_id, Arm(arm_id, "Unknown", "", {}))
            stats["arms"][arm_id] = {
                "name": arm_name.name,
                "pull_count": arm_stat.pull_count,
                "mean_reward": arm_stat.mean_reward,
                "variance": arm_stat.variance,
                "total_reward": arm_stat.total_reward
            }

        return stats

    def get_regret(self) -> float:
        """Calculate cumulative regret (optimal - actual)"""
        if not self.arm_stats:
            return 0.0

        # Find optimal arm
        optimal_arm = self.get_best_arm()
        if not optimal_arm:
            return 0.0

        optimal_mean = self.arm_stats[optimal_arm].mean_reward

        # Calculate regret
        regret = 0.0
        for arm_id, stats in self.arm_stats.items():
            regret += stats.pull_count * (optimal_mean - stats.mean_reward)

        return regret


class AgentBanditRouter:
    """
    Agent Bandit Router
    ====================

    Uses multi-armed bandits to route agent requests to the best
    performing agent configuration.
    """

    def __init__(self):
        self.bandits: Dict[str, MultiArmedBandit] = {}

    def create_bandit(
        self,
        name: str,
        algorithm: BanditAlgorithm,
        arms: List[Arm]
    ) -> str:
        """Create a new bandit"""
        bandit_id = str(uuid.uuid4())[:8]
        bandit = MultiArmedBandit(
            bandit_id=bandit_id,
            name=name,
            algorithm=algorithm,
            arms=arms
        )
        self.bandits[bandit_id] = bandit
        return bandit_id

    def select_arm(self, bandit_id: str) -> Optional[Tuple[str, Dict]]:
        """Select an arm and return its configuration"""
        bandit = self.bandits.get(bandit_id)
        if not bandit:
            return None

        arm_id = bandit.select_arm()
        if not arm_id:
            return None

        config = bandit.get_arm_config(arm_id)
        return arm_id, config

    def report_reward(self, bandit_id: str, arm_id: str, reward: float):
        """Report reward for an arm"""
        bandit = self.bandits.get(bandit_id)
        if bandit:
            bandit.pull_arm(arm_id, reward)

    def get_best_config(self, bandit_id: str) -> Optional[Dict]:
        """Get the best performing configuration"""
        bandit = self.bandits.get(bandit_id)
        if not bandit:
            return None

        best_arm = bandit.get_best_arm()
        if not best_arm:
            return None

        return bandit.get_arm_config(best_arm)

    def get_bandit_status(self, bandit_id: str) -> Dict:
        """Get bandit status"""
        bandit = self.bandits.get(bandit_id)
        return bandit.get_statistics() if bandit else {}


def simulate_agent_task(
    config: Dict[str, Any],
    task_difficulty: float = 1.0
) -> Tuple[Any, float]:
    """
    Simulate an agent task execution and return result and reward.

    Reward is based on:
    - Task success (0-1)
    - Speed (faster is better)
    - Resource efficiency
    """
    # Simulate based on config
    prompt_style = config.get("prompt_style", "detailed")
    examples = config.get("examples", 3)
    temperature = config.get("temperature", 0.7)

    # More examples = better quality but slower
    base_success = 0.7 + (examples * 0.05)
    base_time = 5.0 + (examples * 1.0)

    # Adjust based on prompt style
    if prompt_style == "detailed":
        base_success += 0.1
        base_time += 1.0
    elif prompt_style == "minimal":
        base_success -= 0.05
        base_time -= 1.0

    # Apply difficulty
    success_prob = base_success * (1.0 / task_difficulty)
    time_factor = task_difficulty

    # Simulate execution
    success = random.random() < success_prob
    execution_time = base_time * time_factor * random.uniform(0.8, 1.2)

    # Calculate reward
    if success:
        reward = 1.0 * (10.0 / execution_time)  # Higher reward for faster execution
    else:
        reward = 0.0

    return {"success": success, "time": execution_time}, reward


def main():
    """Demonstrate Multi-Armed Bandits for Agents"""
    print("=" * 60)
    print("Multi-Armed Bandits for Agents - Day 85")
    print("=" * 60)

    # Create agent bandit router
    router = AgentBanditRouter()

    # Define arms (different agent configurations)
    arms = [
        Arm(
            arm_id="detailed_5_examples",
            name="Detailed Prompts (5 examples)",
            description="Detailed prompts with 5 few-shot examples",
            config={"prompt_style": "detailed", "examples": 5, "temperature": 0.7},
            arm_type=ArmType.PROMPT_STRATEGY
        ),
        Arm(
            arm_id="minimal_1_example",
            name="Minimal Prompts (1 example)",
            description="Minimal prompts with 1 few-shot example",
            config={"prompt_style": "minimal", "examples": 1, "temperature": 0.7},
            arm_type=ArmType.PROMPT_STRATEGY
        ),
        Arm(
            arm_id="balanced_3_examples",
            name="Balanced Prompts (3 examples)",
            description="Balanced prompts with 3 few-shot examples",
            config={"prompt_style": "balanced", "examples": 3, "temperature": 0.5},
            arm_type=ArmType.PROMPT_STRATEGY
        ),
        Arm(
            arm_id="creative_0_examples",
            name="Creative (0 examples)",
            description="No few-shot examples, more creative",
            config={"prompt_style": "creative", "examples": 0, "temperature": 1.0},
            arm_type=ArmType.PROMPT_STRATEGY
        )
    ]

    # Test different algorithms
    algorithms_to_test = [
        (BanditAlgorithm.EPSILON_GREEDY, "Epsilon-Greedy (ε=0.1)"),
        (BanditAlgorithm.UCB1, "UCB1"),
        (BanditAlgorithm.THOMPSON_SAMPLING, "Thompson Sampling"),
        (BanditAlgorithm.EPSILON_DECAYING, "Epsilon-Decaying")
    ]

    results = {}

    for algo, algo_name in algorithms_to_test:
        print(f"\n[Testing {algo_name}]")

        # Create bandit
        bandit_id = router.create_bandit(
            name=f"Prompt Strategy - {algo_name}",
            algorithm=algo,
            arms=arms
        )

        # Run simulation
        num_trials = 200

        for trial in range(num_trials):
            # Select arm
            result = router.select_arm(bandit_id)
            if not result:
                continue

            arm_id, config = result

            # Simulate task
            task_result, reward = simulate_agent_task(config, task_difficulty=1.0)

            # Report reward
            router.report_reward(bandit_id, arm_id, reward)

        # Get results
        status = router.get_bandit_status(bandit_id)
        best_arm = status.get("best_arm")
        total_pulls = status.get("total_pulls", 0)

        # Find best arm name
        best_arm_name = "Unknown"
        for arm in arms:
            if arm.arm_id == best_arm:
                best_arm_name = arm.name
                break

        regret = router.bandits[bandit_id].get_regret()

        results[algo_name] = {
            "best_arm": best_arm_name,
            "total_pulls": total_pulls,
            "regret": regret,
            "arm_stats": status.get("arms", {})
        }

        print(f"  Best Arm: {best_arm_name}")
        print(f"  Total Pulls: {total_pulls}")
        print(f"  Cumulative Regret: {regret:.2f}")

    # Summary comparison
    print("\n" + "=" * 60)
    print("Algorithm Comparison")
    print("=" * 60)
    print(f"{'Algorithm':<25} {'Best Arm':<30} {'Regret':<10}")
    print("-" * 60)

    for algo_name, result in results.items():
        print(f"{algo_name:<25} {result['best_arm']:<30} {result['regret']:<10.2f}")

    # Detailed stats for best algorithm
    print("\n[Detailed Statistics - Thompson Sampling]")

    # Find algorithm with lowest regret
    best_algo = min(results.keys(), key=lambda k: results[k]["regret"])
    print(f"Best Algorithm: {best_algo}")

    ts_bandit = None
    for bid, bandit in router.bandits.items():
        if bandit.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            ts_bandit = bandit
            break

    if ts_bandit:
        print("\nArm Performance:")
        for arm_id, stats in ts_bandit.arm_stats.items():
            arm_name = next((a.name for a in arms if a.arm_id == arm_id), arm_id)
            print(f"  {arm_name}:")
            print(f"    Pulls: {stats.pull_count}")
            print(f"    Mean Reward: {stats.mean_reward:.4f}")
            print(f"    Total Reward: {stats.total_reward:.2f}")

    # Demonstrate routing
    print("\n[Live Routing Example]")

    # Create fresh bandit for demonstration
    demo_bandit_id = router.create_bandit(
        name="Live Demo",
        algorithm=BanditAlgorithm.UCB1,
        arms=arms
    )

    print("Making 10 routing decisions...")

    for i in range(10):
        result = router.select_arm(demo_bandit_id)
        if result:
            arm_id, config = result

            # Simulate reward
            _, reward = simulate_agent_task(config)

            # Report reward
            router.report_reward(demo_bandit_id, arm_id, reward)

            arm_name = next((a.name for a in arms if a.arm_id == arm_id), arm_id)
            print(f"  Request {i+1}: {arm_name} (reward: {reward:.2f})")

    print("\n" + "=" * 60)
    print("Multi-Armed Bandits demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()