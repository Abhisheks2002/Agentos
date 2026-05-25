"""
Day 88: Agent Compliance & Audit Framework
==========================================

Implementing compliance management and audit trail for AI agents
including regulatory compliance, policy enforcement, and compliance
reporting.

Key Concepts:
- Regulatory Compliance (GDPR, SOC2, HIPAA)
- Policy Enforcement
- Audit Trail
- Compliance Reporting
- Data Governance
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import hashlib


class ComplianceStandard(Enum):
    """Compliance standards"""
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    CUSTOM = "custom"


class PolicyType(Enum):
    """Policy types"""
    DATA_RETENTION = "data_retention"
    DATA_ACCESS = "data_access"
    ENCRYPTION = "encryption"
    AUDIT_LOGGING = "audit_logging"
    USER_CONSENT = "user_consent"
    DATA_PROCESSING = "data_processing"


class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    IN_PROGRESS = "in_progress"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Policy:
    """Compliance policy"""
    policy_id: str
    name: str
    description: str
    standard: ComplianceStandard
    policy_type: PolicyType
    rules: Dict[str, Any]
    severity: str = "high"
    enabled: bool = True


@dataclass
class AuditEntry:
    """Audit trail entry"""
    entry_id: str
    timestamp: datetime
    agent_id: str
    action: str
    resource: str
    user: str
    result: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    data_classification: str = "internal"
    retention_days: int = 365


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    violation_id: str
    timestamp: datetime
    policy_id: str
    policy_name: str
    agent_id: str
    description: str
    severity: str
    status: str = "open"
    remediation: Optional[str] = None
    resolved_at: Optional[datetime] = None


class PolicyEngine:
    """
    Policy Enforcement Engine
    =========================

    Enforces compliance policies across agent operations.
    """

    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.violations: Dict[str, ComplianceViolation] = {}
        self._init_default_policies()

    def _init_default_policies(self):
        """Initialize default compliance policies"""
        policies = [
            Policy(
                policy_id="gdpr-001",
                name="Data Retention Policy",
                description="Personal data must be deleted after retention period",
                standard=ComplianceStandard.GDPR,
                policy_type=PolicyType.DATA_RETENTION,
                rules={"max_retention_days": 365, " personally_identifiable": True}
            ),
            Policy(
                policy_id="gdpr-002",
                name="User Consent Requirement",
                description="User consent required for data processing",
                standard=ComplianceStandard.GDPR,
                policy_type=PolicyType.USER_CONSENT,
                rules={"consent_required": True, "explicit_consent": True}
            ),
            Policy(
                policy_id="soc2-001",
                name="Audit Logging Policy",
                description="All access to sensitive data must be logged",
                standard=ComplianceStandard.SOC2,
                policy_type=PolicyType.AUDIT_LOGGING,
                rules={"log_all_access": True, "log_retention_years": 1}
            ),
            Policy(
                policy_id="soc2-002",
                name="Encryption Policy",
                description="Data must be encrypted at rest and in transit",
                standard=ComplianceStandard.SOC2,
                policy_type=PolicyType.ENCRYPTION,
                rules={"encryption_at_rest": True, "encryption_in_transit": True}
            ),
            Policy(
                policy_id="hipaa-001",
                name="PHI Access Control",
                description="PHI access restricted to authorized personnel",
                standard=ComplianceStandard.HIPAA,
                policy_type=PolicyType.DATA_ACCESS,
                rules={"minimize_access": True, "break_glass_enabled": True}
            )
        ]

        for policy in policies:
            self.policies[policy.policy_id] = policy

    def add_policy(self, policy: Policy):
        """Add a compliance policy"""
        self.policies[policy.policy_id] = policy

    def check_policy(self, agent_id: str, action: str, resource: str,
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if action complies with policies"""
        violations = []

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            # Check data retention policy
            if policy.policy_type == PolicyType.DATA_RETENTION:
                if "retention_days" in context:
                    max_days = policy.rules.get("max_retention_days", 365)
                    if context["retention_days"] > max_days:
                        violations.append({
                            "policy_id": policy.policy_id,
                            "policy_name": policy.name,
                            "description": f"Data retention exceeds {max_days} days"
                        })

            # Check audit logging policy
            if policy.policy_type == PolicyType.AUDIT_LOGGING:
                if not context.get("logged", True):
                    violations.append({
                        "policy_id": policy.policy_id,
                        "policy_name": policy.name,
                        "description": "Action not logged as required"
                    })

            # Check encryption policy
            if policy.policy_type == PolicyType.ENCRYPTION:
                if not context.get("encrypted", False):
                    violations.append({
                        "policy_id": policy.policy_id,
                        "policy_name": policy.name,
                        "description": "Data not encrypted"
                    })

        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }

    def get_policies_by_standard(self, standard: ComplianceStandard) -> List[Policy]:
        """Get policies for a specific standard"""
        return [p for p in self.policies.values() if p.standard == standard]

    def get_compliance_status(self, standard: ComplianceStandard) -> Dict[str, Any]:
        """Get compliance status for a standard"""
        policies = self.get_policies_by_standard(standard)
        violations = [v for v in self.violations.values()
                     if any(p.policy_id == v.policy_id for p in policies)]

        return {
            "standard": standard.value,
            "total_policies": len(policies),
            "enabled_policies": len([p for p in policies if p.enabled]),
            "total_violations": len(violations),
            "open_violations": len([v for v in violations if v.status == "open"])
        }


class AuditManager:
    """
    Audit Trail Manager
    ====================

    Manages comprehensive audit logging for all agent activities.
    """

    def __init__(self):
        self.entries: List[AuditEntry] = []
        self.encryption_key = "audit-secret-key"  # In production, use proper key management

    def log_entry(self, agent_id: str, action: str, resource: str,
                  user: str, result: str, metadata: Dict[str, Any] = None,
                  data_classification: str = "internal"):
        """Log an audit entry"""
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            agent_id=agent_id,
            action=action,
            resource=resource,
            user=user,
            result=result,
            metadata=metadata or {},
            data_classification=data_classification
        )

        # Encrypt sensitive data
        entry.metadata["hash"] = self._hash_entry(entry)

        self.entries.append(entry)
        return entry

    def _hash_entry(self, entry: AuditEntry) -> str:
        """Create hash of audit entry for tamper detection"""
        data = f"{entry.entry_id}{entry.timestamp}{entry.agent_id}{entry.action}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def query_entries(self, agent_id: str = None, action: str = None,
                      start_date: datetime = None, end_date: datetime = None,
                      data_classification: str = None) -> List[AuditEntry]:
        """Query audit entries with filters"""
        results = self.entries

        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        if action:
            results = [e for e in results if action.lower() in e.action.lower()]
        if start_date:
            results = [e for e in results if e.timestamp >= start_date]
        if end_date:
            results = [e for e in results if e.timestamp <= end_date]
        if data_classification:
            results = [e for e in results if e.data_classification == data_classification]

        return sorted(results, key=lambda e: e.timestamp, reverse=True)

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify audit trail integrity"""
        hashes = [e.metadata.get("hash") for e in self.entries]
        tampered = []

        for entry in self.entries:
            expected_hash = self._hash_entry(entry)
            if entry.metadata.get("hash") != expected_hash:
                tampered.append(entry.entry_id)

        return {
            "total_entries": len(self.entries),
            "tampered_entries": len(tampered),
            "integrity_verified": len(tampered) == 0
        }

    def export_audit_log(self, format: str = "json") -> str:
        """Export audit log"""
        if format == "json":
            return json.dumps([
                {
                    "entry_id": e.entry_id,
                    "timestamp": e.timestamp.isoformat(),
                    "agent_id": e.agent_id,
                    "action": e.action,
                    "resource": e.resource,
                    "user": e.user,
                    "result": e.result,
                    "data_classification": e.data_classification
                }
                for e in self.entries
            ], indent=2)
        return str(self.entries)


class ComplianceReporter:
    """
    Compliance Reporting
    ====================

    Generates compliance reports for various standards.
    """

    def __init__(self, policy_engine: PolicyEngine, audit_manager: AuditManager):
        self.policy_engine = policy_engine
        self.audit_manager = audit_manager
        self.reports: Dict[str, Dict] = {}

    def generate_compliance_report(self, standard: ComplianceStandard,
                                   start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for a standard"""
        policies = self.policy_engine.get_policies_by_standard(standard)
        status = self.policy_engine.get_compliance_status(standard)

        # Get relevant audit entries
        entries = self.audit_manager.query_entries(
            start_date=start_date,
            end_date=end_date
        )

        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "standard": standard.value,
            "summary": status,
            "policies": [
                {
                    "policy_id": p.policy_id,
                    "name": p.name,
                    "enabled": p.enabled,
                    "type": p.policy_type.value
                }
                for p in policies
            ],
            "audit_statistics": {
                "total_entries": len(entries),
                "by_action": self._count_by_action(entries),
                "by_agent": self._count_by_agent(entries)
            }
        }

        self.reports[report["report_id"]] = report
        return report

    def _count_by_action(self, entries: List[AuditEntry]) -> Dict[str, int]:
        """Count entries by action"""
        counts = {}
        for entry in entries:
            counts[entry.action] = counts.get(entry.action, 0) + 1
        return counts

    def _count_by_agent(self, entries: List[AuditEntry]) -> Dict[str, int]:
        """Count entries by agent"""
        counts = {}
        for entry in entries:
            counts[entry.agent_id] = counts.get(entry.agent_id, 0) + 1
        return counts

    def generate_data_subject_report(self, subject_id: str) -> Dict[str, Any]:
        """Generate GDPR data subject report"""
        entries = self.audit_manager.query_entries()

        subject_entries = [
            e for e in entries
            if e.metadata.get("subject_id") == subject_id
        ]

        return {
            "subject_id": subject_id,
            "data_access_count": len(subject_entries),
            "first_access": min(e.timestamp for e in subject_entries).isoformat() if subject_entries else None,
            "last_access": max(e.timestamp for e in subject_entries).isoformat() if subject_entries else None,
            "access_types": list(set(e.action for e in subject_entries))
        }


class ComplianceManager:
    """
    Compliance Management
    =====================

    Centralized compliance management.
    """

    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.audit_manager = AuditManager()
        self.reporter = ComplianceReporter(self.policy_engine, self.audit_manager)

    def enforce_compliance(self, agent_id: str, action: str, resource: str,
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce compliance on agent action"""
        # Check policies
        policy_check = self.policy_engine.check_policy(agent_id, action, resource, context)

        # Log the action
        self.audit_manager.log_entry(
            agent_id=agent_id,
            action=action,
            resource=resource,
            user=context.get("user", "system"),
            result="blocked" if not policy_check["compliant"] else "allowed",
            metadata=context,
            data_classification=context.get("data_classification", "internal")
        )

        return {
            "allowed": policy_check["compliant"],
            "violations": policy_check["violations"]
        }


async def main():
    """Demonstrate Compliance & Audit Framework"""
    print("=" * 60)
    print("Agent Compliance & Audit Framework - Day 88")
    print("=" * 60)

    # Initialize compliance manager
    compliance = ComplianceManager()

    # Display policies
    print("\n[1] Compliance Policies")
    print("-" * 40)
    for policy in compliance.policy_engine.policies.values():
        print(f"{policy.standard.value.upper()}: {policy.name}")
        print(f"  Type: {policy.policy_type.value}")
        print(f"  Enabled: {policy.enabled}")
        print()

    # Enforce compliance
    print("[2] Compliance Enforcement")
    print("-" * 40)

    test_cases = [
        {
            "agent_id": "agent-001",
            "action": "read_file",
            "resource": "/data/customers.csv",
            "context": {"user": "john", "logged": True, "encrypted": True, "retention_days": 30}
        },
        {
            "agent_id": "agent-001",
            "action": "write_file",
            "resource": "/data/export.csv",
            "context": {"user": "john", "logged": True, "encrypted": False, "retention_days": 400}
        },
        {
            "agent_id": "agent-002",
            "action": "process_data",
            "resource": "/data/phi/medical.csv",
            "context": {"user": "admin", "logged": True, "encrypted": True, "consent": True}
        }
    ]

    for i, test in enumerate(test_cases, 1):
        result = compliance.enforce_compliance(
            test["agent_id"],
            test["action"],
            test["resource"],
            test["context"]
        )
        status = "ALLOWED" if result["allowed"] else "BLOCKED"
        print(f"Test {i}: {status}")
        if result["violations"]:
            for v in result["violations"]:
                print(f"  Violation: {v['policy_name']} - {v['description']}")

    # Audit trail
    print("\n[3] Audit Trail")
    print("-" * 40)
    print(f"Total entries: {len(compliance.audit_manager.entries)}")

    # Query audit entries
    query_result = compliance.audit_manager.query_entries()
    print("\nRecent entries:")
    for entry in query_result[:5]:
        print(f"  [{entry.timestamp.strftime('%H:%M:%S')}] {entry.agent_id}: {entry.action} -> {entry.result}")

    # Verify integrity
    print("\n[4] Audit Integrity")
    print("-" * 40)
    integrity = compliance.audit_manager.verify_integrity()
    print(f"Total entries: {integrity['total_entries']}")
    print(f"Tampered: {integrity['tampered_entries']}")
    print(f"Verified: {integrity['integrity_verified']}")

    # Compliance status
    print("\n[5] Compliance Status")
    print("-" * 40)
    for standard in [ComplianceStandard.GDPR, ComplianceStandard.SOC2, ComplianceStandard.HIPAA]:
        status = compliance.policy_engine.get_compliance_status(standard)
        print(f"\n{standard.value.upper()}:")
        print(f"  Policies: {status['total_policies']}")
        print(f"  Violations: {status['total_violations']}")

    # Compliance report
    print("\n[6] Compliance Report")
    print("-" * 40)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    report = compliance.reporter.generate_compliance_report(
        ComplianceStandard.GDPR, start_date, end_date
    )
    print(f"Report ID: {report['report_id']}")
    print(f"Standard: {report['standard']}")
    print(f"Period: {report['period']['start']} to {report['period']['end']}")
    print(f"Total Policies: {report['summary']['total_policies']}")

    print("\n" + "=" * 60)
    print("Compliance & Audit Framework complete!")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())