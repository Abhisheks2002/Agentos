"""
Day 30: Agent Collaboration Patterns
=====================================
Skill: Team Collaboration
Mini Project: Team Manager

Patterns for agents working together on shared goals.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid


class CollaborationMode(str, Enum):
    """How agents collaborate"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ROUND_ROBIN = "round_robin"
    DEMOCRATIC = "democratic"


@dataclass
class SharedArtifact:
    """Something agents are collaborating on"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: Any = None
    contributors: List[str] = field(default_factory=list)
    version: int = 1
    history: List[Dict] = field(default_factory=list)

    def contribute(self, agent_id: str, content: Any):
        """Add contribution"""
        self.content = content
        if agent_id not in self.contributors:
            self.contributors.append(agent_id)
        self.version += 1
        self.history.append({
            "agent": agent_id,
            "version": self.version,
            "timestamp": datetime.now().isoformat()
        })


@dataclass
class TeamRole:
    """Role in a team"""
    name: str = ""
    description: str = ""
    responsibilities: List[str] = field(default_factory=list)
    authority_level: int = 0


class CollaborationTeam:
    """A team of collaborating agents"""

    def __init__(self, team_id: str, name: str):
        self.team_id = team_id
        self.name = name
        self.members: Dict[str, Dict[str, Any]] = {}
        self.artifacts: Dict[str, SharedArtifact] = {}
        self.mode = CollaborationMode.PARALLEL
        self.leader: Optional[str] = None

    def add_member(self, agent_id: str, role: str = "member", skills: List[str] = None):
        """Add a team member"""
        self.members[agent_id] = {
            "role": role,
            "skills": skills or [],
            "joined": datetime.now().isoformat()
        }

        if role == "leader":
            self.leader = agent_id

    def remove_member(self, agent_id: str):
        """Remove a team member"""
        self.members.pop(agent_id, None)

    def create_artifact(self, title: str) -> SharedArtifact:
        """Create a shared artifact"""
        artifact = SharedArtifact(title=title)
        self.artifacts[artifact.id] = artifact
        return artifact

    async def collaborate(
        self,
        artifact_id: str,
        agent_contributions: Dict[str, Any]
    ) -> SharedArtifact:
        """Collaborate on an artifact"""
        artifact = self.artifacts.get(artifact_id)
        if not artifact:
            raise ValueError("Artifact not found")

        if self.mode == CollaborationMode.PARALLEL:
            # All contribute at once
            for agent_id, content in agent_contributions.items():
                artifact.contribute(agent_id, content)

        elif self.mode == CollaborationMode.SEQUENTIAL:
            # One after another
            for agent_id, content in agent_contributions.items():
                artifact.contribute(agent_id, content)
                await asyncio.sleep(0.01)

        elif self.mode == CollaborationMode.HIERARCHICAL:
            # Leader approves contributions
            for agent_id, content in agent_contributions.items():
                if agent_id == self.leader:
                    artifact.contribute(agent_id, content)
                else:
                    # Simulate approval
                    approved = True
                    if approved:
                        artifact.contribute(agent_id, content)

        return artifact

    def get_team_stats(self) -> Dict[str, Any]:
        """Get team statistics"""
        return {
            "team_id": self.team_id,
            "name": self.name,
            "members": len(self.members),
            "artifacts": len(self.artifacts),
            "mode": self.mode.value,
            "leader": self.leader
        }


class PeerReviewTeam(CollaborationTeam):
    """Team with peer review"""

    def __init__(self, team_id: str, name: str):
        super().__init__(team_id, name)
        self.reviews: Dict[str, List[Dict]] = {}

    async def submit_for_review(self, artifact_id: str, submitter: str) -> List[str]:
        """Submit artifact for peer review"""
        artifact = self.artifacts.get(artifact_id)
        if not artifact:
            return []

        # Request reviews from other members
        reviewers = [
            m for m in self.members.keys()
            if m != submitter
        ]

        self.reviews[artifact_id] = [
            {"reviewer": r, "status": "pending"}
            for r in reviewers
        ]

        return reviewers

    async def submit_review(
        self,
        artifact_id: str,
        reviewer: str,
        feedback: Dict[str, Any]
    ):
        """Submit a review"""
        if artifact_id not in self.reviews:
            return

        for review in self.reviews[artifact_id]:
            if review["reviewer"] == reviewer:
                review["status"] = "completed"
                review["feedback"] = feedback


class EnsembleTeam(CollaborationTeam):
    """Ensemble pattern - multiple agents solve, best selected"""

    def __init__(self, team_id: str, name: str):
        super().__init__(team_id, name)
        self.solutions: Dict[str, List[Dict]] = {}

    async def solve_parallel(self, task: str) -> Dict[str, Any]:
        """Solve task in parallel and select best"""
        solutions = []

        for agent_id in self.members.keys():
            # Each agent solves independently
            solution = {
                "agent": agent_id,
                "result": f"Solution by {agent_id} for {task}",
                "confidence": 0.8
            }
            solutions.append(solution)

        self.solutions[task] = solutions

        # Select best
        best = max(solutions, key=lambda x: x["confidence"])

        return {
            "task": task,
            "all_solutions": len(solutions),
            "best_solution": best
        }


class PairProgrammingTeam(CollaborationTeam):
    """Pair programming pattern"""

    def __init__(self, team_id: str, name: str):
        super().__init__(team_id, name)
        self.pairs: Dict[str, str] = {}

    def form_pairs(self, agent_ids: List[str]):
        """Form pairs of agents"""
        self.pairs = {}
        for i in range(0, len(agent_ids) - 1, 2):
            self.pairs[agent_ids[i]] = agent_ids[i + 1]

    async def pair_program(self, task: str, driver: str, navigator: str) -> Dict[str, Any]:
        """Run pair programming session"""
        # Driver writes, Navigator reviews
        result = {
            "task": task,
            "driver": driver,
            "navigator": navigator,
            "code": f"Code written by {driver}, reviewed by {navigator}",
            "iterations": 3
        }

        return result


# Demo
def run_demo():
    print("=" * 70)
    print("Agent Collaboration Patterns Demo")
    print("=" * 70)

    import asyncio

    async def demo():
        # Create team
        team = CollaborationTeam("team1", "Project Alpha")

        # Add members
        print("\n[1] Team Setup")
        print("-" * 40)

        team.add_member("Alice", "leader", ["design", "code"])
        team.add_member("Bob", "developer", ["code", "test"])
        team.add_member("Carol", "developer", ["code", "review"])

        stats = team.get_team_stats()
        print(f"  Team: {stats['name']}")
        print(f"  Members: {stats['members']}")
        print(f"  Leader: {stats['leader']}")

        # Create and collaborate on artifact
        print("\n[2] Collaboration")
        print("-" * 40)

        artifact = team.create_artifact("Project Spec")
        print(f"  Created: {artifact.title}")

        contributions = {
            "Alice": "Initial design...",
            "Bob": "Added implementation details...",
            "Carol": "Added testing considerations..."
        }

        result = await team.collaborate(artifact.id, contributions)
        print(f"  Contributors: {len(result.contributors)}")
        print(f"  Version: {result.version}")

        # Peer review team
        print("\n[3] Peer Review")
        print("-" * 40)

        review_team = PeerReviewTeam("team2", "Review Team")
        review_team.add_member("Dave", "reviewer")
        review_team.add_member("Eve", "reviewer")
        review_team.add_member("Frank", "author")

        artifact2 = review_team.create_artifact("Code Review")
        reviewers = await review_team.submit_for_review(artifact2.id, "Frank")
        print(f"  Review requested from: {reviewers}")

        # Ensemble team
        print("\n[4] Ensemble Pattern")
        print("-" * 40)

        ensemble = EnsembleTeam("team3", "Ensemble")
        ensemble.add_member("Agent1", "solver")
        ensemble.add_member("Agent2", "solver")
        ensemble.add_member("Agent3", "solver")

        result = await ensemble.solve_parallel("Fix bug #123")
        print(f"  Solutions: {result['all_solutions']}")
        print(f"  Best: {result['best_solution']['agent']}")

        # Pair programming
        print("\n[5] Pair Programming")
        print("-" * 40)

        pair_team = PairProgrammingTeam("team4", "Pair Team")
        pair_team.add_member("Programmer1", "driver")
        pair_team.add_member("Programmer2", "navigator")

        result = await pair_team.pair_program(
            "Implement feature",
            "Programmer1",
            "Programmer2"
        )
        print(f"  Driver: {result['driver']}")
        print(f"  Navigator: {result['navigator']}")

    asyncio.run(demo())
    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()