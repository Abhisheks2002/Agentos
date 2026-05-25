"""
Day 87: Agent Security & Threat Detection
==========================================

Implementing comprehensive security monitoring and threat detection
for AI agents including anomaly detection, behavior analysis, and
real-time threat response.

Key Concepts:
- Anomaly Detection
- Behavioral Analysis
- Threat Intelligence
- Real-time Alerting
- Security Posture Assessment
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
import re


class ThreatLevel(Enum):
    """Threat severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatCategory(Enum):
    """Categories of threats"""
    MALICIOUS_ACTION = "malicious_action"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    RESOURCE_ABUSE = "resource_abuse"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    POLICY_VIOLATION = "policy_violation"
    CREDENTIAL_COMPROMISE = "credential_compromise"
    EXTERNAL_ATTACK = "external_attack"


class AlertStatus(Enum):
    """Alert status"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class SecurityEvent:
    """Security event log entry"""
    event_id: str
    timestamp: datetime
    agent_id: str
    event_type: str
    severity: ThreatLevel
    description: str
    source_ip: Optional[str] = None
    target_resource: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    indicators: List[str] = field(default_factory=list)


@dataclass
class ThreatIndicator:
    """Threat indicator (IOC)"""
    indicator_id: str
    indicator_type: str  # ip, hash, domain, behavior
    value: str
    threat_category: ThreatCategory
    confidence: float  # 0-1
    first_seen: datetime
    last_seen: datetime
    related_events: List[str] = field(default_factory=list)


@dataclass
class SecurityAlert:
    """Security alert"""
    alert_id: str
    threat_level: ThreatLevel
    category: ThreatCategory
    title: str
    description: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.NEW
    affected_agents: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None


class BehaviorProfile:
    """
    Agent Behavior Profile
    ======================

    Tracks normal behavior patterns for anomaly detection.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.action_counts: Dict[str, int] = defaultdict(int)
        self.resource_usage: Dict[str, List[float]] = defaultdict(list)
        self.api_call_patterns: List[str] = []
        self.file_access_patterns: List[str] = []
        self.network_patterns: List[str] = []
        self.time_series_data: List[datetime] = []
        self.baseline_calculated = False

    def record_action(self, action_type: str, resource: str = "", network: str = ""):
        """Record an action for profiling"""
        self.action_counts[action_type] += 1
        if resource:
            self.file_access_patterns.append(resource)
        if network:
            self.network_patterns.append(network)
        self.time_series_data.append(datetime.now())

    def calculate_baseline(self):
        """Calculate baseline behavior metrics"""
        # Calculate average action counts
        self.baseline = {
            "avg_actions_per_hour": sum(self.action_counts.values()) / max(1, len(self.time_series_data)),
            "top_actions": sorted(self.action_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "unique_resources": len(set(self.file_access_patterns)),
            "unique_networks": len(set(self.network_patterns))
        }
        self.baseline_calculated = True

    def detect_anomaly(self, current_action: str, resources: List[str], networks: List[str]) -> float:
        """Detect anomaly score (0-1)"""
        if not self.baseline_calculated:
            self.calculate_baseline()

        anomaly_score = 0.0

        # Check if action is in baseline
        if current_action not in self.action_counts:
            anomaly_score += 0.3

        # Check for unusual resource access
        unusual_resources = set(resources) - set(self.file_access_patterns)
        if unusual_resources:
            anomaly_score += min(0.4, len(unusual_resources) * 0.1)

        # Check for unusual network destinations
        unusual_networks = set(networks) - set(self.network_patterns)
        if unusual_networks:
            anomaly_score += min(0.3, len(unusual_networks) * 0.1)

        return min(1.0, anomaly_score)


class ThreatDetector:
    """
    Threat Detection Engine
    ========================

    Analyzes security events and detects potential threats.
    """

    def __init__(self):
        self.indicators: Dict[str, ThreatIndicator] = {}
        self.event_history: List[SecurityEvent] = []
        self.threat_rules: Dict[str, Dict[str, Any]] = {}
        self.ml_model = None  # Placeholder for ML model
        self._init_rules()

    def _init_rules(self):
        """Initialize detection rules"""
        self.threat_rules = {
            "rapid_api_calls": {
                "threshold": 100,
                "window": 60,  # seconds
                "severity": ThreatLevel.MEDIUM,
                "description": "Rapid API calls detected"
            },
            "unauthorized_file_access": {
                "patterns": [r"\.ssh", r"\.aws", r"\.env", r"\.git"],
                "severity": ThreatLevel.HIGH,
                "description": "Attempted access to sensitive files"
            },
            "suspicious_process": {
                "patterns": [r"powershell.*-enc", r"cmd.*/c", r"bash.*-i"],
                "severity": ThreatLevel.CRITICAL,
                "description": "Suspicious process execution"
            },
            "data_exfiltration": {
                "threshold_mb": 100,
                "window": 300,
                "severity": ThreatLevel.HIGH,
                "description": "Large data transfer detected"
            }
        }

    def add_indicator(self, indicator: ThreatIndicator):
        """Add threat indicator"""
        self.indicators[indicator.indicator_id] = indicator

    def analyze_event(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Analyze a security event for threats"""
        self.event_history.append(event)

        # Check against rules
        alert = self._check_rules(event)

        if not alert:
            # Check for behavioral anomalies
            alert = self._check_anomaly(event)

        if not alert:
            # Check against known indicators
            alert = self._check_indicators(event)

        return alert

    def _check_rules(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check event against detection rules"""
        # Check rapid API calls
        if event.event_type == "api_call":
            recent_calls = [
                e for e in self.event_history[-100:]
                if e.event_type == "api_call"
                and (datetime.now() - e.timestamp).total_seconds() < 60
            ]
            if len(recent_calls) > self.threat_rules["rapid_api_calls"]["threshold"]:
                return SecurityAlert(
                    alert_id=str(uuid.uuid4()),
                    threat_level=ThreatLevel.MEDIUM,
                    category=ThreatCategory.RESOURCE_ABUSE,
                    title="Rapid API Calls Detected",
                    description=self.threat_rules["rapid_api_calls"]["description"],
                    timestamp=datetime.now(),
                    affected_agents=[event.agent_id]
                )

        # Check unauthorized file access
        if event.event_type == "file_access":
            for pattern in self.threat_rules["unauthorized_file_access"]["patterns"]:
                if re.search(pattern, event.target_resource or ""):
                    return SecurityAlert(
                        alert_id=str(uuid.uuid4()),
                        threat_level=ThreatLevel.HIGH,
                        category=ThreatCategory.UNAUTHORIZED_ACCESS,
                        title="Unauthorized File Access Attempt",
                        description=self.threat_rules["unauthorized_file_access"]["description"],
                        timestamp=datetime.now(),
                        affected_agents=[event.agent_id],
                        indicators=[event.target_resource or ""]
                    )

        # Check suspicious process
        if event.event_type == "process_start":
            for pattern in self.threat_rules["suspicious_process"]["patterns"]:
                if re.search(pattern, event.description, re.IGNORECASE):
                    return SecurityAlert(
                        alert_id=str(uuid.uuid4()),
                        threat_level=ThreatLevel.CRITICAL,
                        category=ThreatCategory.MALICIOUS_ACTION,
                        title="Suspicious Process Execution",
                        description=self.threat_rules["suspicious_process"]["description"],
                        timestamp=datetime.now(),
                        affected_agents=[event.agent_id],
                        remediation="Isolate agent and investigate"
                    )

        return None

    def _check_anomaly(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check for behavioral anomalies"""
        # Simplified anomaly check
        if event.severity == ThreatLevel.HIGH:
            return SecurityAlert(
                alert_id=str(uuid.uuid4()),
                threat_level=ThreatLevel.MEDIUM,
                category=ThreatCategory.ANOMALOUS_BEHAVIOR,
                title="Anomalous Behavior Detected",
                description=f"Unusual pattern detected: {event.description}",
                timestamp=datetime.now(),
                affected_agents=[event.agent_id]
            )
        return None

    def _check_indicators(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Check against known threat indicators"""
        # Check if event source matches any indicators
        for indicator in self.indicators.values():
            if indicator.indicator_type == "ip" and event.source_ip:
                if event.source_ip == indicator.value:
                    return SecurityAlert(
                        alert_id=str(uuid.uuid4()),
                        threat_level=ThreatLevel.CRITICAL,
                        category=indicator.threat_category,
                        title="Known Malicious IP Detected",
                        description=f"Event from known malicious source: {indicator.value}",
                        timestamp=datetime.now(),
                        affected_agents=[event.agent_id],
                        indicators=[indicator.value]
                    )
        return None


class SecurityOperationsCenter:
    """
    Security Operations Center (SOC)
    ===============================

    Centralized security monitoring and response.
    """

    def __init__(self):
        self.detector = ThreatDetector()
        self.alerts: Dict[str, SecurityAlert] = {}
        self.behavior_profiles: Dict[str, BehaviorProfile] = {}
        self.incident_response_playbooks: Dict[str, Dict] = {}
        self.security_metrics: Dict[str, Any] = defaultdict(int)
        self._init_playbooks()

    def _init_playbooks(self):
        """Initialize incident response playbooks"""
        self.incident_response_playbooks = {
            "malicious_action": {
                "steps": [
                    "Isolate affected agent",
                    "Collect forensic data",
                    "Block malicious indicators",
                    "Notify security team",
                    "Investigate root cause"
                ],
                "automated": True
            },
            "unauthorized_access": {
                "steps": [
                    "Revoke access credentials",
                    "Review access logs",
                    "Reset affected credentials",
                    "Update access policies"
                ],
                "automated": False
            },
            "data_breach": {
                "steps": [
                    "Contain breach",
                    "Identify data affected",
                    "Notify data subjects",
                    "Report to authorities",
                    "Remediate vulnerability"
                ],
                "automated": False
            }
        }

    def register_agent(self, agent_id: str):
        """Register agent for security monitoring"""
        self.behavior_profiles[agent_id] = BehaviorProfile(agent_id)

    def process_event(self, event: SecurityEvent) -> Optional[SecurityAlert]:
        """Process security event"""
        # Update behavior profile
        if event.agent_id in self.behavior_profiles:
            profile = self.behavior_profiles[event.agent_id]
            profile.record_action(
                event.event_type,
                event.target_resource or "",
                event.source_ip or ""
            )

        # Analyze for threats
        alert = self.detector.analyze_event(event)

        if alert:
            self.alerts[alert.alert_id] = alert
            self.security_metrics["total_alerts"] += 1
            self.security_metrics[f"alerts_{alert.threat_level.value}"] += 1

            # Execute automated response if available
            if alert.category.value in self.incident_response_playbooks:
                playbook = self.incident_response_playbooks[alert.category.value]
                if playbook["automated"]:
                    await self._execute_playbook(alert, playbook)

        return alert

    async def _execute_playbook(self, alert: SecurityAlert, playbook: Dict):
        """Execute incident response playbook"""
        print(f"[SOC] Executing playbook for {alert.category.value}")
        print(f"Alert: {alert.title}")

        for step in playbook["steps"]:
            print(f"  - {step}")
            await asyncio.sleep(0.1)

        alert.status = AlertStatus.CONTAINED

    def get_alerts(self, threat_level: Optional[ThreatLevel] = None,
                   status: Optional[AlertStatus] = None) -> List[SecurityAlert]:
        """Get filtered alerts"""
        alerts = list(self.alerts.values())

        if threat_level:
            alerts = [a for a in alerts if a.threat_level == threat_level]

        if status:
            alerts = [a for a in alerts if a.status == status]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_security_posture(self) -> Dict[str, Any]:
        """Get overall security posture"""
        return {
            "total_alerts": len(self.alerts),
            "active_threats": len([a for a in self.alerts.values()
                                  if a.status in [AlertStatus.NEW, AlertStatus.INVESTIGATING]]),
            "critical_alerts": self.security_metrics.get("alerts_critical", 0),
            "high_alerts": self.security_metrics.get("alerts_high", 0),
            "medium_alerts": self.security_metrics.get("alerts_medium", 0),
            "monitored_agents": len(self.behavior_profiles),
            "threat_indicators": len(self.detector.indicators),
            "security_score": self._calculate_security_score()
        }

    def _calculate_security_score(self) -> float:
        """Calculate security score (0-100)"""
        base_score = 100.0

        # Deduct for active threats
        critical = self.security_metrics.get("alerts_critical", 0)
        high = self.security_metrics.get("alerts_high", 0)
        medium = self.security_metrics.get("alerts_medium", 0)

        deductions = (critical * 15) + (high * 10) + (medium * 5)
        return max(0, base_score - deductions)


async def main():
    """Demonstrate Agent Security & Threat Detection"""
    print("=" * 60)
    print("Agent Security & Threat Detection - Day 87")
    print("=" * 60)

    # Initialize SOC
    soc = SecurityOperationsCenter()

    # Register agents
    for agent_id in ["agent-001", "agent-002", "agent-003"]:
        soc.register_agent(agent_id)

    print(f"\n[1] Security Operations Center initialized")
    print(f"Registered {len(soc.behavior_profiles)} agents for monitoring")

    # Simulate security events
    print("\n[2] Processing Security Events")
    print("-" * 40)

    events = [
        SecurityEvent(
            event_id="evt-001",
            timestamp=datetime.now(),
            agent_id="agent-001",
            event_type="file_access",
            severity=ThreatLevel.INFO,
            description="Accessing data file",
            target_resource="/data/users/file.csv"
        ),
        SecurityEvent(
            event_id="evt-002",
            timestamp=datetime.now(),
            agent_id="agent-001",
            event_type="file_access",
            severity=ThreatLevel.HIGH,
            description="Unauthorized access attempt",
            target_resource="/home/user/.ssh/id_rsa"
        ),
        SecurityEvent(
            event_id="evt-003",
            timestamp=datetime.now(),
            agent_id="agent-002",
            event_type="process_start",
            severity=ThreatLevel.CRITICAL,
            description="Starting suspicious process",
            target_resource="powershell -enc YWJj"
        ),
        SecurityEvent(
            event_id="evt-004",
            timestamp=datetime.now(),
            agent_id="agent-003",
            event_type="api_call",
            severity=ThreatLevel.INFO,
            description="Making API request"
        )
    ]

    alerts_generated = []
    for event in events:
        alert = await soc.process_event(event)
        status = "ALERT" if alert else "OK"
        print(f"Event {event.event_id} ({event.event_type}): {status}")
        if alert:
            alerts_generated.append(alert)

    # Display alerts
    print("\n[3] Generated Security Alerts")
    print("-" * 40)
    for alert in alerts_generated:
        print(f"\n[{alert.threat_level.value.upper()}] {alert.title}")
        print(f"  Category: {alert.category.value}")
        print(f"  Description: {alert.description}")
        print(f"  Affected Agents: {', '.join(alert.affected_agents)}")
        if alert.remediation:
            print(f"  Remediation: {alert.remediation}")

    # Display threat indicators
    print("\n[4] Threat Intelligence")
    print("-" * 40)

    # Add some threat indicators
    indicator = ThreatIndicator(
        indicator_id="ioc-001",
        indicator_type="ip",
        value="192.168.1.100",
        threat_category=ThreatCategory.EXTERNAL_ATTACK,
        confidence=0.9,
        first_seen=datetime.now() - timedelta(days=7),
        last_seen=datetime.now()
    )
    soc.detector.add_indicator(indicator)

    print(f"Active Threat Indicators: {len(soc.detector.indicators)}")
    for ioc in soc.detector.indicators.values():
        print(f"  - {ioc.indicator_type}: {ioc.value}")
        print(f"    Category: {ioc.threat_category.value}, Confidence: {ioc.confidence}")

    # Security Posture
    print("\n[5] Security Posture")
    print("-" * 40)
    posture = soc.get_security_posture()
    print(f"Security Score: {posture['security_score']}/100")
    print(f"Monitored Agents: {posture['monitored_agents']}")
    print(f"Total Alerts: {posture['total_alerts']}")
    print(f"Active Threats: {posture['active_threats']}")
    print(f"  Critical: {posture['critical_alerts']}")
    print(f"  High: {posture['high_alerts']}")
    print(f"  Medium: {posture['medium_alerts']}")

    print("\n" + "=" * 60)
    print("Agent Security & Threat Detection complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())