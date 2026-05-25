"""
Day 3: The OpenAI API & Structured Outputs
============================================
Skill: API Integration & Pydantic
Mini Project: The Schema Enforcer

AgentOS needs structured data (JSON), not just chat text.
Pydantic ensures the LLM follows your OS schema.
"""

import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))

# Define AgentOS Identity Card schema using Pydantic
class AgentIdentity(BaseModel):
    """Schema for an AgentOS Identity Card"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name")
    role: str = Field(..., description="Agent role: admin, user, guest")
    permissions: List[str] = Field(default_factory=list, description="List of allowed actions")
    status: str = Field(default="active", description="Current status")
    created_at: str = Field(..., description="ISO timestamp of creation")

    @field_validator('role')
    def validate_role(cls, v):
        allowed = ['admin', 'user', 'guest', 'worker']
        if v.lower() not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v.lower()

class SystemLog(BaseModel):
    """Schema for AgentOS System Log"""
    timestamp: str
    level: str  # INFO, WARNING, ERROR
    agent_id: str
    action: str
    details: str

def generate_identity_card(agent_name: str, role: str) -> AgentIdentity:
    """Generate a valid AgentOS Identity Card using OpenAI"""
    from datetime import datetime

    prompt = f"""Generate an AgentOS Identity Card for {agent_name} with role {role}.
Return ONLY valid JSON with these fields:
- agent_id: format "AGENT-XXXX" where X is random alphanumeric
- name: {agent_name}
- role: {role}
- permissions: array of 2-4 appropriate permissions based on role
- status: "active"
- created_at: current ISO timestamp

Return ONLY the JSON, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        data = json.loads(response.choices[0].message.content)
        return AgentIdentity(**data, created_at=datetime.now().isoformat())

    except Exception as e:
        # Fallback: generate locally
        import random
        import string
        return AgentIdentity(
            agent_id=f"AGENT-{''.join(random.choices(string.ascii_uppercase, k=4))}",
            name=agent_name,
            role=role,
            permissions=["read"] if role == "user" else ["read", "write", "execute"],
            status="active",
            created_at=datetime.now().isoformat()
        )

def generate_system_log(agent_id: str, action: str, level: str = "INFO") -> SystemLog:
    """Generate a system log entry"""
    from datetime import datetime
    return SystemLog(
        timestamp=datetime.now().isoformat(),
        level=level,
        agent_id=agent_id,
        action=action,
        details=f"Agent {agent_id} performed {action}"
    )

# Test the Schema Enforcer
if __name__ == "__main__":
    print("=" * 60)
    print("The Schema Enforcer - AgentOS Identity Card Generator")
    print("=" * 60)

    # Generate identity cards
    agents = [
        ("ResearchBot", "admin"),
        ("DataBot", "user"),
        ("MailBot", "guest")
    ]

    for name, role in agents:
        try:
            card = generate_identity_card(name, role)
            print(f"\n{name} Identity Card:")
            print(f"  ID: {card.agent_id}")
            print(f"  Role: {card.role}")
            print(f"  Permissions: {card.permissions}")
            print(f"  Status: {card.status}")
        except Exception as e:
            print(f"Error generating {name}: {e}")

    # Generate system log
    print("\n" + "-" * 60)
    log = generate_system_log("AGENT-001", "file_read", "INFO")
    print(f"System Log: {log.model_dump_json(indent=2)}")