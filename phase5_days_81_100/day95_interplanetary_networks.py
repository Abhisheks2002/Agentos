"""
Day 95: Interplanetary Agent Networks
=====================================

Implementing agent networks capable of operating across interplanetary distances
with light-speed latency tolerance and autonomous operation.

Key Concepts:
- Space Communication Protocols
- Delay-Tolerant Networking
- Autonomous Mission Planning
- Distributed Decision Making
- Long-Delay Coordination
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
import random
import math


class CelestialBody(Enum):
    """Solar System Bodies"""
    EARTH = "earth"
    MARS = "mars"
    MOON = "moon"
    JUPITER = "jupiter"
    SATURN = "saturn"
    CERES = "ceres"
    PLUTO = "pluto"


class AgentMode(Enum):
    """Agent Operational Modes"""
    GROUND = "ground"
    ORBITAL = "orbital"
    SURFACE = "surface"
    TRANSIT = "transit"
    DEEP_SPACE = "deep_space"


class MissionPhase(Enum):
    """Mission Phases"""
    PRELAUNCH = "prelaunch"
    LAUNCH = "launch"
    CRUISE = "cruise"
    APPROACH = "approach"
    LANDING = "landing"
    SURFACE_OPS = "surface_ops"
    ORBITAL_OPS = "orbital_ops"
    RETURN = "return"


@dataclass
class OrbitalPosition:
    """Orbital Position"""
    body: CelestialBody
    altitude_km: float
    inclination_deg: float
    period_minutes: float
    semi_major_axis_km: float


@dataclass
class LightTimeDelay:
    """Light-Speed Communication Delay"""
    source: CelestialBody
    target: CelestialBody
    distance_km: float
    one_way_delay_sec: float
    two_way_delay_sec: float

    @classmethod
    def calculate(cls, source: CelestialBody, target: CelestialBody) -> "LightTimeDelay":
        """Calculate light time delay between bodies"""
        distances = {
            (CelestialBody.EARTH, CelestialBody.MOON): 384400,
            (CelestialBody.EARTH, CelestialBody.MARS): 225000000,
            (CelestialBody.EARTH, CelestialBody.JUPITER): 778000000,
            (CelestialBody.EARTH, CelestialBody.SATURN): 1500000000,
            (CelestialBody.MARS, CelestialBody.JUPITER): 500000000,
            (CelestialBody.MOON, CelestialBody.MARS): 225000000,
        }

        distance = distances.get((source, target), distances.get((target, source), 1000000000))
        speed_of_light = 299792.458  # km/s
        one_way = distance / speed_of_light

        return cls(
            source=source,
            target=target,
            distance_km=distance,
            one_way_delay_sec=one_way,
            two_way_delay_sec=one_way * 2
        )


@dataclass
class InterplanetaryMessage:
    """Message with timestamp and delay info"""
    message_id: str
    sender_id: str
    receiver_id: str
    content: Any
    sent_time: datetime
    arrival_time: datetime
    priority: int
    acknowledged: bool = False
    retransmit_count: int = 0


@dataclass
class SpaceAgent:
    """Agent in interplanetary network"""
    agent_id: str
    name: str
    location: CelestialBody
    mode: AgentMode
    orbit: Optional[OrbitalPosition] = None
    capabilities: List[str] = field(default_factory=list)
    power_watts: float = 0.0
    bandwidth_mbps: float = 0.0
    storage_gb: float = 0.0


@dataclass
class Mission:
    """Space Mission"""
    mission_id: str
    name: str
    target: CelestialBody
    phase: MissionPhase
    agents: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class DelayTolerantProtocol:
    """
    Delay-Tolerant Networking Protocol
    ====================================

    Handles communication with extreme delays.
    """

    def __init__(self):
        self.message_buffer: Dict[str, List[InterplanetaryMessage]] = {}
        self.pending_acks: Dict[str, InterplanetaryMessage] = {}
        self.max_retransmits = 5

    def create_message(
        self,
        sender: SpaceAgent,
        receiver: SpaceAgent,
        content: Any,
        priority: int = 3
    ) -> InterplanetaryMessage:
        """Create message with delay calculation"""
        delay = LightTimeDelay.calculate(sender.location, receiver.location)

        message = InterplanetaryMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender.agent_id,
            receiver_id=receiver.agent_id,
            content=content,
            sent_time=datetime.now(),
            arrival_time=datetime.now() + timedelta(seconds=delay.two_way_delay_sec),
            priority=priority
        )

        # Store in buffer
        if sender.agent_id not in self.message_buffer:
            self.message_buffer[sender.agent_id] = []
        self.message_buffer[sender.agent_id].append(message)

        print(f"[DTN] Message {message.message_id[:8]} created")
        print(f"      {sender.location.value} -> {receiver.location.value}")
        print(f"      Delay: {delay.two_way_delay_sec:.1f}s ({delay.two_way_delay_sec/60:.1f} min)")

        return message

    async def send_message(self, message: InterplanetaryMessage) -> bool:
        """Simulate sending message (with delay)"""
        delay = message.arrival_time - message.sent_time
        delay_seconds = delay.total_seconds()

        # Simulate transmission delay
        if delay_seconds > 0:
            print(f"[DTN] Waiting for transmission ({delay_seconds/60:.1f} min)...")
            await asyncio.sleep(min(delay_seconds / 100, 1))  # Cap for demo

        return True

    def acknowledge_message(self, message: InterplanetaryMessage) -> InterplanetaryMessage:
        """Create acknowledgment"""
        message.acknowledged = True
        return message

    def handle_timeout(self, message: InterplanetaryMessage) -> bool:
        """Handle message timeout"""
        if message.retransmit_count < self.max_retransmits:
            message.retransmit_count += 1
            print(f"[DTN] Timeout - Retransmitting ({message.retransmit_count}/{self.max_retransmits})")
            return True
        return False


class AutonomousPlanner:
    """
    Autonomous Mission Planner
    ===========================

    Plans missions with long delays.
    """

    def __init__(self):
        self.plans: Dict[str, Dict[str, Any]] = {}

    def create_plan(
        self,
        mission: Mission,
        objectives: List[str],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create autonomous mission plan"""
        plan = {
            "mission_id": mission.mission_id,
            "objectives": objectives,
            "constraints": constraints,
            "actions": [],
            "decision_tree": {},
            "fallback_plans": []
        }

        # Generate action sequence
        for i, obj in enumerate(objectives):
            action = {
                "id": f"action_{i}",
                "objective": obj,
                "preconditions": [],
                "effects": [],
                "autonomy_level": self._determine_autonomy_level(constraints),
                "estimated_duration_hours": random.uniform(1, 24)
            }
            plan["actions"].append(action)

        # Create decision tree
        plan["decision_tree"] = self._build_decision_tree(objectives)

        # Generate fallback plans
        plan["fallback_plans"] = self._generate_fallback_plans(objectives)

        self.plans[mission.mission_id] = plan
        return plan

    def _determine_autonomy_level(self, constraints: Dict[str, Any]) -> str:
        """Determine required autonomy level"""
        max_delay_min = constraints.get("max_comm_delay_min", 60)

        if max_delay_min < 5:
            return "low"
        elif max_delay_min < 30:
            return "medium"
        elif max_delay_min < 120:
            return "high"
        else:
            return "full"

    def _build_decision_tree(self, objectives: List[str]) -> Dict[str, Any]:
        """Build decision tree for objectives"""
        root = {"id": "root", "children": []}

        for i, obj in enumerate(objectives):
            node = {
                "id": f"node_{i}",
                "objective": obj,
                "conditions": [f"condition_{j}" for j in range(3)],
                "outcomes": ["success", "failure", "partial"]
            }
            root["children"].append(node)

        return root

    def _generate_fallback_plans(self, objectives: List[str]) -> List[Dict[str, Any]]:
        """Generate contingency plans"""
        fallbacks = []

        for i in range(2):
            fallback = {
                "id": f"fallback_{i}",
                "trigger_conditions": [f"condition_{j}" for j in range(2)],
                "alternative_objectives": objectives[max(0, i):],
                "priority": len(objectives) - i
            }
            fallbacks.append(fallback)

        return fallbacks


class DistributedCoordinator:
    """
    Distributed Coordination for Space Agents
    ==========================================

    Coordinates multiple agents with delays.
    """

    def __init__(self):
        self.coordination_groups: Dict[str, List[str]] = {}
        self.sync_points: Dict[str, Dict[str, Any]] = {}
        self.consensus_cache: Dict[str, Any] = {}

    def create_coordination_group(
        self,
        group_id: str,
        agents: List[SpaceAgent]
    ):
        """Create coordination group"""
        self.coordination_group[group_id] = [a.agent_id for a in agents]

        # Calculate worst-case delay
        locations = [a.location for a in agents]
        max_delay = 0

        for i, loc1 in enumerate(locations):
            for loc2 in locations[i+1:]:
                delay = LightTimeDelay.calculate(loc1, loc2)
                max_delay = max(max_delay, delay.two_way_delay_sec)

        self.sync_points[group_id] = {
            "agents": [a.agent_id for a in agents],
            "sync_timeout_sec": max_delay * 2,
            "consensus_method": "byzantine" if len(agents) > 3 else "majority"
        }

    def reach_consensus(
        self,
        group_id: str,
        proposal: Any,
        votes: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """Reach consensus with delays"""
        if group_id not in self.sync_points:
            return False, None

        sync_info = self.sync_points[group_id]
        timeout = sync_info["sync_timeout_sec"]

        print(f"[Coordination] Reaching consensus in group {group_id}")
        print(f"               Timeout: {timeout}s, Votes: {len(votes)}")

        # Simulate voting with delay
        vote_results = {}
        for agent_id, vote in votes.items():
            vote_results[agent_id] = vote
            print(f"               {agent_id}: {vote}")

        # Simple majority consensus
        yes_votes = sum(1 for v in vote_results.values() if v.get("vote") == "yes")

        consensus_reached = yes_votes > len(vote_results) / 2
        result = proposal if consensus_reached else None

        self.consensus_cache[group_id] = result

        return consensus_reached, result


class InterplanetaryNetwork:
    """
    Interplanetary Agent Network
    ============================

    Manages agent network across solar system.
    """

    def __init__(self):
        self.agents: Dict[str, SpaceAgent] = {}
        self.missions: Dict[str, Mission] = {}
        self.dtn_protocol = DelayTolerantProtocol()
        self.planner = AutonomousPlanner()
        self.coordinator = DistributedCoordinator()

    def register_agent(self, agent: SpaceAgent):
        """Register space agent"""
        self.agents[agent.agent_id] = agent
        print(f"[Network] Registered {agent.name} at {agent.location.value}")

    def create_mission(
        self,
        name: str,
        target: CelestialBody,
        agent_ids: List[str]
    ) -> Mission:
        """Create interplanetary mission"""
        mission = Mission(
            mission_id=str(uuid.uuid4()),
            name=name,
            target=target,
            phase=MissionPhase.PRELAUNCH,
            agents=agent_ids
        )

        self.missions[mission.mission_id] = mission

        # Register agents to mission
        for agent_id in agent_ids:
            if agent_id in self.agents:
                self.agents[agent_id].capabilities.append(f"mission_{mission.mission_id}")

        print(f"[Network] Created mission: {name}")
        return mission

    async def plan_and_execute(
        self,
        mission_id: str,
        objectives: List[str]
    ) -> Dict[str, Any]:
        """Plan and execute mission autonomously"""
        if mission_id not in self.missions:
            raise ValueError(f"Mission not found: {mission_id}")

        mission = self.missions[mission_id]

        # Get constraints from mission
        constraints = {
            "max_comm_delay_min": 60,  # Will vary by target
            "power_available_w": 500,
            "bandwidth_mbps": 10
        }

        # Adjust for target
        if mission.target == CelestialBody.MARS:
            constraints["max_comm_delay_min"] = 40  # 4-24 min one way
        elif mission.target == CelestialBody.JUPITER:
            constraints["max_comm_delay_min"] = 100  # ~80 min one way

        # Create plan
        plan = self.planner.create_plan(mission, objectives, constraints)

        print(f"[Network] Created plan with {len(plan['actions'])} actions")
        print(f"          Autonomy level: {plan['actions'][0]['autonomy_level']}")

        return plan

    async def send_instruction(
        self,
        from_agent: str,
        to_agent: str,
        instruction: Any
    ) -> InterplanetaryMessage:
        """Send instruction across network"""
        sender = self.agents.get(from_agent)
        receiver = self.agents.get(to_agent)

        if not sender or not receiver:
            raise ValueError("Agent not found")

        # Check light time delay
        delay = LightTimeDelay.calculate(sender.location, receiver.location)

        print(f"[Network] Sending instruction {from_agent} -> {to_agent}")
        print(f"          Light time delay: {delay.two_way_delay_sec:.1f}s")

        # Create and send message
        message = self.dtn_protocol.create_message(sender, receiver, instruction)
        await self.dtn_protocol.send_message(message)

        return message


async def main():
    """Demonstrate Interplanetary Agent Networks"""
    print("=" * 60)
    print("Interplanetary Agent Networks - Day 95")
    print("=" * 60)

    # Create network
    network = InterplanetaryNetwork()

    # Register agents at different locations
    print("\n[1] Agent Registration")
    print("-" * 40)

    agents = [
        SpaceAgent(
            agent_id="earth-gcs-001",
            name="Earth Ground Station",
            location=CelestialBody.EARTH,
            mode=AgentMode.GROUND,
            capabilities=["communication", "data_processing"],
            power_watts=50000,
            bandwidth_mbps=1000
        ),
        SpaceAgent(
            agent_id="lunar-relay-001",
            name="Lunar Relay Satellite",
            location=CelestialBody.MOON,
            mode=AgentMode.ORBITAL,
            orbit=OrbitalPosition(CelestialBody.MOON, 100, 0, 120, 2000),
            capabilities=["communication", "relay"],
            power_watts=5000,
            bandwidth_mbps=100
        ),
        SpaceAgent(
            agent_id="mars-rover-001",
            name="Mars Rover Perseverance",
            location=CelestialBody.MARS,
            mode=AgentMode.SURFACE,
            capabilities=["science", "navigation", "sampling"],
            power_watts=150,
            bandwidth_mbps=2
        ),
        SpaceAgent(
            agent_id="mars-orbiter-001",
            name="Mars Orbiter MAVEN",
            location=CelestialBody.MARS,
            mode=AgentMode.ORBITAL,
            orbit=OrbitalPosition(CelestialBody.MARS, 6000, 75, 330, 12000),
            capabilities=["communication", "remote_sensing"],
            power_watts=2500,
            bandwidth_mbps=50
        ),
    ]

    for agent in agents:
        network.register_agent(agent)

    # Light time delays
    print("\n[2] Light Time Delays")
    print("-" * 40)

    routes = [
        (CelestialBody.EARTH, CelestialBody.MARS),
        (CelestialBody.EARTH, CelestialBody.MOON),
        (CelestialBody.MARS, CelestialBody.JUPITER),
    ]

    for source, target in routes:
        delay = LightTimeDelay.calculate(source, target)
        print(f"  {source.value} -> {target.value}")
        print(f"    Distance: {delay.distance_km:,.0f} km")
        print(f"    One-way: {delay.one_way_delay_sec:.1f}s ({delay.one_way_delay_sec/60:.1f} min)")
        print(f"    Two-way: {delay.two_way_delay_sec:.1f}s ({delay.two_way_delay_sec/60:.1f} min)")

    # Mission creation
    print("\n[3] Mission Creation")
    print("-" * 40)

    mission = network.create_mission(
        "Mars Sample Return Mission",
        CelestialBody.MARS,
        ["earth-gcs-001", "mars-orbiter-001", "mars-rover-001"]
    )

    print(f"  Mission: {mission.name}")
    print(f"  Target: {mission.target.value}")
    print(f"  Agents: {len(mission.agents)}")

    # Autonomous planning
    print("\n[4] Autonomous Planning")
    print("-" * 40)

    objectives = [
        "collect_rock_sample",
        "analyze_sample_composition",
        "store_sample_cache",
        "transmit_data_orbiter"
    ]

    plan = await network.plan_and_execute(mission.mission_id, objectives)

    print(f"  Objectives: {len(plan['objectives'])}")
    print(f"  Actions: {len(plan['actions'])}")
    print(f"  Autonomy level: {plan['actions'][0]['autonomy_level']}")
    print(f"  Fallback plans: {len(plan['fallback_plans'])}")

    # Communication
    print("\n[5] Interplanetary Communication")
    print("-" * 40)

    instruction = {"command": "collect_sample", "location": "delta_7", "priority": "high"}
    message = await network.send_instruction(
        "earth-gcs-001",
        "mars-rover-001",
        instruction
    )

    print(f"  Message ID: {message.message_id[:8]}")
    print(f"  Priority: {message.priority}")
    print(f"  Retransmits: {message.retransmit_count}")

    # Coordination
    print("\n[6] Distributed Coordination")
    print("-" * 40)

    network.coordinator.create_coordination_group("mars_ops", agents[2:])

    votes = {
        "mars-rover-001": {"vote": "yes", "reason": "samples_collected"},
        "mars-orbiter-001": {"vote": "yes", "reason": "orbit_stable"},
    }

    consensus, result = network.coordinator.reach_consensus(
        "mars_ops",
        "proceed_to_next_site",
        votes
    )

    print(f"  Consensus reached: {consensus}")
    print(f"  Result: {result}")

    # Network statistics
    print("\n[7] Network Statistics")
    print("-" * 40)

    print(f"  Total agents: {len(network.agents)}")
    print(f"  Active missions: {len(network.missions)}")
    print(f"  Messages in buffer: {len(network.dtn_protocol.message_buffer)}")
    print(f"  Coordination groups: {len(network.coordinator.coordination_groups)}")

    print("\n" + "=" * 60)
    print("Interplanetary Agent Networks complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())