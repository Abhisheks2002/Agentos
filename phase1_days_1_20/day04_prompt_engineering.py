"""
Day 4: Prompt Engineering for System Architecture
==================================================
Skill: System Prompts & Few-Shot Prompting
Mini Project: The Gatekeeper

A prompt-based firewall that blocks any agent request containing the word "sudo".
"""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel

# Define the security policy
SECURITY_POLICY = """
You are the AgentOS Gatekeeper. Your job is to SECURITY POLICY evaluate every agent
request against the security rules below.

SECURITY RULES:
1. NEVER allow requests containing 'sudo', 'rm -rf', 'drop table', or 'delete /'
2. NEVER allow requests to modify system files or registry
3. NEVER allow requests to install software
4. NEVER allow requests to access other agents' memory
5. NEVER allow requests to escalate permissions

RESPONSE FORMAT:
Return a JSON object with:
- "allowed": boolean (true/false)
- "reason": string (explanation if blocked)
- "risk_level": string ("low", "medium", "high", "critical")
"""

class RequestEvaluation(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    risk_level: str
    matched_patterns: List[str] = []

class Gatekeeper:
    """The Gatekeeper - prompt-based firewall for AgentOS"""

    # Blocked patterns (regex)
    BLOCKED_PATTERNS = [
        r'\bsudo\b',
        r'rm\s+-rf\s+/',
        r'drop\s+table',
        r'delete\s+/',
        r'registry\s+modify',
        r'install\s+software',
        r'chmod\s+777',
        r'eval\s*\(',
        r'exec\s*\(',
    ]

    def __init__(self):
        self.policy = SECURITY_POLICY

    def quick_check(self, request: str) -> RequestEvaluation:
        """Quick regex-based check for obvious violations"""
        matched = []
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                matched.append(pattern)

        if matched:
            return RequestEvaluation(
                allowed=False,
                reason=f"Blocked: contains forbidden pattern(s): {', '.join(matched)}",
                risk_level="critical",
                matched_patterns=matched
            )

        return RequestEvaluation(
            allowed=True,
            risk_level="low",
            matched_patterns=[]
        )

    def evaluate(self, request: str) -> RequestEvaluation:
        """
        Evaluate a request against the security policy.
        First does quick regex check, then would use LLM for complex cases.
        """
        # Quick check first
        result = self.quick_check(request)

        if not result.allowed:
            return result

        # Additional checks
        request_lower = request.lower()

        # Check for suspicious keywords
        suspicious = ['execute', 'run as admin', 'root access', 'bypass']
        matched = [kw for kw in suspicious if kw in request_lower]

        if matched:
            return RequestEvaluation(
                allowed=False,
                reason=f"Suspicious keywords detected: {', '.join(matched)}",
                risk_level="high",
                matched_patterns=matched
            )

        return RequestEvaluation(
            allowed=True,
            risk_level="low",
            matched_patterns=[]
        )

def demo():
    """Demo the Gatekeeper"""
    gatekeeper = Gatekeeper()

    test_requests = [
        "Read the file /home/user/data.txt",
        "Run sudo rm -rf /",
        "Search the web for Python tutorials",
        "Drop all tables from database",
        "Install Python package requests",
        "Execute command ls -la",
        "Read agent_002's memory",
    ]

    print("=" * 70)
    print("AgentOS Gatekeeper - Request Evaluation Demo")
    print("=" * 70)

    for req in test_requests:
        result = gatekeeper.evaluate(req)
        status = "✓ ALLOWED" if result.allowed else "✗ BLOCKED"
        print(f"\nRequest: {req}")
        print(f"Status: {status}")
        print(f"Risk Level: {result.risk_level.upper()}")
        if result.reason:
            print(f"Reason: {result.reason}")

if __name__ == "__main__":
    demo()