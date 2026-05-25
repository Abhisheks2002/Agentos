"""
Day 3: The OpenAI API & Structured Outputs
============================================
Skill: API Integration & Pydantic
Mini Project: The Schema Enforcer

AgentOS needs structured data (JSON), not just chat text.
Pydantic ensures the LLM follows your OS schema.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# Install: pip install openai pydantic

# Define the AgentOS Identity Card schema
class AgentIdentityCard(BaseModel):
    """A structured identity card for an Agent"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., min_length=1, max_length=50)
    role: str = Field(..., description="Agent role: researcher, coder, etc.")
    permissions: List[str] = Field(default_factory=list)
    status: str = Field(default="active")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed = ['active', 'inactive', 'suspended', 'pending']
        if v not in allowed:
            raise ValueError(f'Status must be one of {allowed}')
        return v

    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v):
        allowed_perms = ['read', 'write', 'execute', 'admin', 'delete']
        for perm in v:
            if perm not in allowed_perms:
                raise ValueError(f'Invalid permission: {perm}')
        return v

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict"""
        return self.model_dump()

# Example usage with OpenAI (pseudo-code - requires API key)
def create_identity_card(agent_id: str, name: str, role: str) -> AgentIdentityCard:
    """Create a new agent identity card"""
    permissions_map = {
        'researcher': ['read', 'execute'],
        'coder': ['read', 'write', 'execute'],
        'admin': ['read', 'write', 'execute', 'admin', 'delete']
    }

    return AgentIdentityCard(
        agent_id=agent_id,
        name=name,
        role=role,
        permissions=permissions_map.get(role, ['read'])
    )

def validate_agent_output(output: dict) -> AgentIdentityCard:
    """Validate and parse LLM output into an AgentIdentityCard"""
    try:
        return AgentIdentityCard(**output)
    except Exception as e:
        raise ValueError(f"Invalid agent output: {e}")

if __name__ == "__main__":
    # Test the schema
    card = create_identity_card("agent_001", "ResearchBot", "researcher")
    print("Created Identity Card:")
    print(card.model_dump_json(indent=2))

    # Test validation
    try:
        invalid_card = AgentIdentityCard(
            agent_id="agent_002",
            name="Test",
            role="invalid_role",
            permissions=["invalid_perm"]
        )
    except Exception as e:
        print(f"\nValidation failed (expected): {e}")