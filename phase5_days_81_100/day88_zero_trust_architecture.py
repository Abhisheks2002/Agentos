"""
Day 88: Zero-Trust Architecture
===============================

Implementing Zero-Trust security model for Agent OS including
identity verification, micro-segmentation, continuous validation,
and least-privilege access.

Key Concepts:
- Never Trust, Always Verify
- Micro-segmentation
- Identity-based Access
- Continuous Authentication
- Least Privilege Principle
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib
import asyncio
from collections import defaultdict
import json
import secrets


class TrustLevel(Enum):
    """Trust levels"""
    UNTRUSTED = "untrusted"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL = "full"


class AccessDecision(Enum):
    """Access decision types"""
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"
    MFA_REQUIRED = "mfa_required"


class ResourceType(Enum):
    """Resource types"""
    FILE = "file"
    API = "api"
    PROCESS = "process"
    NETWORK = "network"
    DATA = "data"
    SYSTEM = "system"


@dataclass
class Identity:
    """Identity information"""
    identity_id: str
    identity_type: str  # agent, user, service
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    mfa_enabled: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_authenticated: Optional[datetime] = None


@dataclass
class AccessPolicy:
    """Access policy definition"""
    policy_id: str
    name: str
    resource_type: ResourceType
    resource_pattern: str
    allowed_identities: List[str] = field(default_factory=list)
    denied_identities: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    trust_level_required: TrustLevel = TrustLevel.LOW
    mfa_required: bool = False
    time_restrictions: Optional[Dict] = None
    rate_limit: Optional[int] = None


@dataclass
class AccessRequest:
    """Access request"""
    request_id: str
    identity_id: str
    resource_type: ResourceType
    resource_path: str
    action: str  # read, write, execute, delete
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class AccessDecisionResult:
    """Access decision result"""
    request_id: str
    decision: AccessDecision
    trust_level: TrustLevel
    reason: str
    conditions: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MicroSegment:
    """
    Micro-segment
    =============

    Isolated network segment with specific security controls.
    """

    def __init__(self, segment_id: str, name: str):
        self.segment_id = segment_id
        self.name = name
        self.members: Set[str] = set()
        self.ingress_rules: List[Dict] = []
        self.egress_rules: List[Dict] = []
        self.security_level: TrustLevel = TrustLevel.MEDIUM
        self.isolation_level: str = "strict"

    def add_member(self, identity_id: str):
        """Add member to segment"""
        self.members.add(identity_id)

    def remove_member(self, identity_id: str):
        """Remove member from segment"""
        self.members.discard(identity_id)

    def can_communicate(self, source: str, dest: str) -> bool:
        """Check if communication is allowed between members"""
        if source not in self.members or dest not in self.members:
            return False

        # Check egress rules
        for rule in self.egress_rules:
            if rule.get("destination") == dest or rule.get("destination") == "*":
                return rule.get("action") == "allow"

        return False


class ZeroTrustPolicyEngine:
    """
    Zero-Trust Policy Engine
    ========================

    Evaluates access requests against Zero-Trust policies.
    """

    def __init__(self):
        self.identities: Dict[str, Identity] = {}
        self.policies: Dict[str, AccessPolicy] = {}
        self.segments: Dict[str, MicroSegment] = {}
        self.trust_scores: Dict[str, float] = {}
        self.session_tokens: Dict[str, Dict] = {}
        self._init_default_policies()

    def _init_default_policies(self):
        """Initialize default Zero-Trust policies"""
        self.policies = {
            "default-deny": AccessPolicy(
                policy_id="default-deny",
                name="Default Deny All",
                resource_type=ResourceType.SYSTEM,
                resource_pattern="*",
                trust_level_required=TrustLevel.HIGH,
                denied_identities=["*"]
            ),
            "agent-api-access": AccessPolicy(
                policy_id="agent-api-access",
                name="Agent API Access",
                resource_type=ResourceType.API,
                resource_pattern="/api/agents/*",
                allowed_identities=["agent-*"],
                trust_level_required=TrustLevel.MEDIUM,
                mfa_required=False
            ),
            "data-read-access": AccessPolicy(
                policy_id="data-read-access",
                name="Data Read Access",
                resource_type=ResourceType.DATA,
                resource_pattern="/data/**",
                trust_level_required=TrustLevel.LOW,
                conditions={"max_size_mb": 100}
            ),
            "process-execution": AccessPolicy(
                policy_id="process-execution",
                name="Process Execution",
                resource_type=ResourceType.PROCESS,
                resource_pattern="*",
                trust_level_required=TrustLevel.HIGH,
                mfa_required=True
            )
        }

    def register_identity(self, identity: Identity):
        """Register an identity"""
        self.identities[identity.identity_id] = identity
        self.trust_scores[identity.identity_id] = 50.0  # Start at medium

    def create_segment(self, segment: MicroSegment):
        """Create a micro-segment"""
        self.segments[segment.segment_id] = segment

    def evaluate_access(self, request: AccessRequest) -> AccessDecisionResult:
        """Evaluate access request using Zero-Trust model"""
        # Step 1: Verify identity
        if request.identity_id not in self.identities:
            return AccessDecisionResult(
                request_id=request.request_id,
                decision=AccessDecision.DENY,
                trust_level=TrustLevel.UNTRUSTED,
                reason="Identity not recognized"
            )

        identity = self.identities[request.identity_id]

        # Step 2: Get current trust score
        trust_score = self.trust_scores.get(request.identity_id, 0)
        trust_level = self._score_to_level(trust_score)

        # Step 3: Find matching policies
        matching_policies = self._find_matching_policies(request)

        if not matching_policies:
            return AccessDecisionResult(
                request_id=request.request_id,
                decision=AccessDecision.DENY,
                trust_level=trust_level,
                reason="No matching policy found"
            )

        # Step 4: Evaluate policies
        for policy in matching_policies:
            decision = self._evaluate_policy(policy, request, trust_level, identity)

            if decision.decision != AccessDecision.DENY:
                # Update trust score based on access
                self._update_trust_score(request.identity_id, decision.decision)

                return decision

        return AccessDecisionResult(
            request_id=request.request_id,
            decision=AccessDecision.DENY,
            trust_level=trust_level,
            reason="All policies denied access"
        )

    def _score_to_level(self, score: float) -> TrustLevel:
        """Convert trust score to level"""
        if score >= 80:
            return TrustLevel.FULL
        elif score >= 60:
            return TrustLevel.HIGH
        elif score >= 40:
            return TrustLevel.MEDIUM
        elif score >= 20:
            return TrustLevel.LOW
        return TrustLevel.UNTRUSTED

    def _find_matching_policies(self, request: AccessRequest) -> List[AccessPolicy]:
        """Find policies matching the request"""
        matching = []

        for policy in self.policies.values():
            if policy.resource_type != request.resource_type:
                continue

            # Check resource pattern
            if self._matches_pattern(request.resource_path, policy.resource_pattern):
                matching.append(policy)

        # Sort by specificity (most specific first)
        matching.sort(key=lambda p: len(p.resource_pattern), reverse=True)
        return matching

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern"""
        if pattern == "*":
            return True
        if "**" in pattern:
            base = pattern.replace("**", "")
            return path.startswith(base)
        if "*" in pattern:
            import fnmatch
            return fnmatch.fnmatch(path, pattern)
        return path == pattern

    def _evaluate_policy(self, policy: AccessPolicy, request: AccessRequest,
                        trust_level: TrustLevel, identity: Identity) -> AccessDecisionResult:
        """Evaluate a single policy"""
        # Check explicit deny
        if identity.identity_id in policy.denied_identities or "*" in policy.denied_identities:
            return AccessDecisionResult(
                request_id=request.request_id,
                decision=AccessDecision.DENY,
                trust_level=trust_level,
                reason="Explicitly denied by policy"
            )

        # Check allowed identities
        allowed = False
        for allowed_id in policy.allowed_identities:
            if allowed_id == "*" or allowed_id == identity.identity_id:
                allowed = True
                break

        if not allowed:
            return AccessDecisionResult(
                request_id=request.request_id,
                decision=AccessDecision.DENY,
                trust_level=trust_level,
                reason="Not in allowed identities list"
            )

        # Check trust level requirement
        trust_hierarchy = [
            TrustLevel.UNTRUSTED, TrustLevel.LOW, TrustLevel.MEDIUM,
            TrustLevel.HIGH, TrustLevel.FULL
        ]
        required_idx = trust_hierarchy.index(policy.trust_level_required)
        current_idx = trust_hierarchy.index(trust_level)

        if current_idx < required_idx:
            return AccessDecisionResult(
                request_id=request.request_id,
                decision=AccessDecision.CONDITIONAL,
                trust_level=trust_level,
                reason=f"Insufficient trust level: {trust_level.value} < {policy.trust_level_required.value}",
                conditions=[f"Requires trust level {policy.trust_level_required.value} or higher"]
            )

        # Check MFA requirement
        if policy.mfa_required and not identity.mfa_enabled:
            return AccessDecisionResult(
                request_id=request.request_id,
                decision=AccessDecision.MFA_REQUIRED,
                trust_level=trust_level,
                reason="MFA required but not enabled"
            )

        # Check time restrictions
        if policy.time_restrictions:
            current_hour = datetime.now().hour
            allowed_hours = policy.time_restrictions.get("allowed_hours", [])
            if current_hour not in allowed_hours:
                return AccessDecisionResult(
                    request_id=request.request_id,
                    decision=AccessDecision.DENY,
                    trust_level=trust_level,
                    reason="Outside allowed time window"
                )

        # All checks passed
        return AccessDecisionResult(
            request_id=request.request_id,
            decision=AccessDecision.ALLOW,
            trust_level=trust_level,
            reason="Access granted by policy",
            expires_at=datetime.now() + timedelta(minutes=15)
        )

    def _update_trust_score(self, identity_id: str, decision: AccessDecision):
        """Update trust score based on access decision"""
        current = self.trust_scores.get(identity_id, 50)

        if decision == AccessDecision.ALLOW:
            self.trust_scores[identity_id] = min(100, current + 2)
        elif decision == AccessDecision.MFA_REQUIRED:
            self.trust_scores[identity_id] = max(0, current - 5)
        elif decision == AccessDecision.DENY:
            self.trust_scores[identity_id] = max(0, current - 10)

    def get_trust_level(self, identity_id: str) -> TrustLevel:
        """Get current trust level for identity"""
        score = self.trust_scores.get(identity_id, 0)
        return self._score_to_level(score)

    def revoke_access(self, identity_id: str):
        """Revoke all access for identity"""
        self.trust_scores[identity_id] = 0

        # Invalidate session tokens
        if identity_id in self.session_tokens:
            del self.session_tokens[identity_id]


class ContinuousValidator:
    """
    Continuous Authentication Validator
    =====================================

    Continuously validates identity and trust during sessions.
    """

    def __init__(self, policy_engine: ZeroTrustPolicyEngine):
        self.policy_engine = policy_engine
        self.active_sessions: Dict[str, Dict] = {}
        self.behavior_baselines: Dict[str, Dict] = defaultdict(dict)

    def start_session(self, identity_id: str, request: AccessRequest) -> str:
        """Start a new authenticated session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "identity_id": identity_id,
            "start_time": datetime.now(),
            "last_verified": datetime.now(),
            "request_count": 0,
            "risk_score": 0
        }
        return session_id

    async def verify_session(self, session_id: str, request: AccessRequest) -> bool:
        """Continuously verify session validity"""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        session["request_count"] += 1

        # Check session age
        session_age = (datetime.now() - session["start_time"]).total_seconds()
        if session_age > 3600:  # 1 hour max
            self.end_session(session_id)
            return False

        # Periodic re-verification every 10 requests
        if session["request_count"] % 10 == 0:
            identity_id = session["identity_id"]
            trust_level = self.policy_engine.get_trust_level(identity_id)

            if trust_level == TrustLevel.UNTRUSTED:
                self.end_session(session_id)
                return False

            session["last_verified"] = datetime.now()

        # Check for anomalous behavior
        if self._detect_anomaly(session, request):
            session["risk_score"] += 10
            if session["risk_score"] > 50:
                self.end_session(session_id)
                return False

        return True

    def _detect_anomaly(self, session: Dict, request: AccessRequest) -> bool:
        """Detect anomalous behavior"""
        # Simple anomaly detection
        if request.action == "delete" and session["request_count"] < 5:
            return True

        if request.resource_type == ResourceType.SYSTEM:
            return True

        return False

    def end_session(self, session_id: str):
        """End a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        return self.active_sessions.get(session_id)


async def main():
    """Demonstrate Zero-Trust Architecture"""
    print("=" * 60)
    print("Zero-Trust Architecture - Day 88")
    print("=" * 60)

    # Initialize Zero-Trust engine
    zt_engine = ZeroTrustPolicyEngine()
    validator = ContinuousValidator(zt_engine)

    # Register identities
    identities = [
        Identity(
            identity_id="agent-001",
            identity_type="agent",
            name="Data Processing Agent",
            attributes={"role": "processor", "clearance": "internal"},
            mfa_enabled=False
        ),
        Identity(
            identity_id="admin-001",
            identity_type="user",
            name="Admin User",
            attributes={"role": "admin", "clearance": "high"},
            mfa_enabled=True
        ),
        Identity(
            identity_id="service-001",
            identity_type="service",
            name="Analytics Service",
            attributes={"service_type": "analytics"},
            mfa_enabled=False
        )
    ]

    for identity in identities:
        zt_engine.register_identity(identity)

    print(f"\n[1] Registered {len(identities)} identities")

    # Create micro-segments
    segments = [
        MicroSegment("seg-production", "Production"),
        MicroSegment("seg-development", "Development"),
        MicroSegment("seg-analytics", "Analytics")
    ]

    for seg in segments:
        zt_engine.create_segment(seg)

    print(f"Created {len(segments)} micro-segments")

    # Display trust scores
    print("\n[2] Initial Trust Scores")
    print("-" * 40)
    for identity in identities:
        level = zt_engine.get_trust_level(identity.identity_id)
        score = zt_engine.trust_scores[identity.identity_id]
        print(f"{identity.name}: {score} ({level.value})")

    # Test access requests
    print("\n[3] Access Control Evaluation")
    print("-" * 40)

    requests = [
        AccessRequest(
            request_id="req-001",
            identity_id="agent-001",
            resource_type=ResourceType.API,
            resource_path="/api/agents/status",
            action="read"
        ),
        AccessRequest(
            request_id="req-002",
            identity_id="agent-001",
            resource_type=ResourceType.PROCESS,
            resource_path="/system/config",
            action="execute"
        ),
        AccessRequest(
            request_id="req-003",
            identity_id="admin-001",
            resource_type=ResourceType.DATA,
            resource_path="/data/users/export.csv",
            action="read"
        ),
        AccessRequest(
            request_id="req-004",
            identity_id="agent-001",
            resource_type=ResourceType.DATA,
            resource_path="/data/sensitive/passwords.txt",
            action="read"
        )
    ]

    for req in requests:
        result = zt_engine.evaluate_access(req)
        print(f"\nRequest: {req.action.upper()} {req.resource_path}")
        print(f"  Identity: {req.identity_id}")
        print(f"  Decision: {result.decision.value}")
        print(f"  Reason: {result.reason}")
        print(f"  Trust Level: {result.trust_level.value}")

    # Test continuous validation
    print("\n[4] Continuous Authentication")
    print("-" * 40)

    session_id = validator.start_session("agent-001", requests[0])
    print(f"Session started: {session_id}")

    # Simulate requests in session
    for i in range(12):
        is_valid = await validator.verify_session(session_id, requests[0])
        print(f"Request {i+1}: {'Valid' if is_valid else 'Invalid'}")

    print(f"Session info: {validator.get_session_info(session_id)}")

    # Display final trust scores
    print("\n[5] Final Trust Scores")
    print("-" * 40)
    for identity in identities:
        level = zt_engine.get_trust_level(identity.identity_id)
        score = zt_engine.trust_scores[identity.identity_id]
        print(f"{identity.name}: {score} ({level.value})")

    # Test MFA requirement
    print("\n[6] MFA Requirement")
    print("-" * 40)

    mfa_request = AccessRequest(
        request_id="req-mfa",
        identity_id="agent-001",
        resource_type=ResourceType.PROCESS,
        resource_path="*",
        action="execute"
    )

    result = zt_engine.evaluate_access(mfa_request)
    print(f"Agent without MFA requesting process execution:")
    print(f"  Decision: {result.decision.value}")
    print(f"  Reason: {result.reason}")

    # Test with MFA-enabled identity
    mfa_request.identity_id = "admin-001"
    result = zt_engine.evaluate_access(mfa_request)
    print(f"\nAdmin with MFA requesting process execution:")
    print(f"  Decision: {result.decision.value}")
    print(f"  Reason: {result.reason}")

    print("\n" + "=" * 60)
    print("Zero-Trust Architecture complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())