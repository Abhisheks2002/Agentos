"""
Day 19: Security Basics - Protecting AgentOS
============================================
Skill: Security Best Practices
Mini Project: Secure Agent Configuration

Learn to secure your AI agents - from environment variables to
vault integration and secure agent communication.
"""

import os
import hashlib
import hmac
import secrets
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import base64

# Note: Production systems should use proper secrets management
# like HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault


class SecretLevel(str, Enum):
    """Classification of secret sensitivity"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class Secret:
    """Secret metadata"""
    key: str
    level: SecretLevel
    description: str
    created_at: str
    expires_at: Optional[str] = None
    last_rotated: Optional[str] = None


@dataclass
class AgentPermission:
    """Agent permission definition"""
    agent_id: str
    resource: str
    actions: List[str]
    expires_at: Optional[str] = None


class SecureConfig:
    """
    Secure Configuration Manager
    ============================

    Manages environment variables and secrets securely
    """

    def __init__(self):
        self.secrets: Dict[str, Secret] = {}
        self._secret_store: Dict[str, str] = {}

    def load_from_env(self, prefix: str = "AGENTOS_"):
        """Load secrets from environment variables"""
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Store without prefix
                clean_key = key[len(prefix):]
                self._secret_store[clean_key] = value

                self.secrets[clean_key] = Secret(
                    key=clean_key,
                    level=self._classify_secret(clean_key),
                    description=f"Loaded from env: {key}",
                    created_at=datetime.now().isoformat()
                )

    def _classify_secret(self, key: str) -> SecretLevel:
        """Classify secret sensitivity"""
        key_lower = key.lower()

        # Check key name for classification
        if any(word in key_lower for word in ["password", "key", "secret", "token", "private"]):
            return SecretLevel.RESTRICTED
        elif any(word in key_lower for word in ["api_key", "apikey", "auth"]):
            return SecretLevel.CONFIDENTIAL
        elif any(word in key_lower for word in ["internal", "config"]):
            return SecretLevel.INTERNAL
        return SecretLevel.PUBLIC

    def get(self, key: str, default: str = None) -> Optional[str]:
        """Get secret value"""
        return self._secret_store.get(key, default)

    def set(self, key: str, value: str, level: SecretLevel = SecretLevel.INTERNAL):
        """Set secret value"""
        self._secret_store[key] = value
        self.secrets[key] = Secret(
            key=key,
            level=level,
            description="Set via SecureConfig",
            created_at=datetime.now().isoformat()
        )

    def delete(self, key: str):
        """Delete secret"""
        self._secret_store.pop(key, None)
        self.secrets.pop(key, None)

    def rotate(self, key: str, new_value: str):
        """Rotate secret"""
        if key in self._secret_store:
            old_value = self._secret_store[key]
            # In production: log rotation for audit
            self._secret_store[key] = new_value
            self.secrets[key].last_rotated = datetime.now().isoformat()

    def list_secrets(self) -> List[Dict[str, Any]]:
        """List secret metadata (not values)"""
        return [
            {
                "key": s.key,
                "level": s.level.value,
                "description": s.description,
                "created_at": s.created_at
            }
            for s in self.secrets.values()
        ]


class AgentVault:
    """
    Agent Vault - Secrets Management for AI Agents
    ==============================================

    Provides secure storage and retrieval of:
    - API keys
    - Credentials
    - Certificates
    - Encryption keys
    """

    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.environ.get("VAULT_MASTER_KEY", "default_key_change_me")
        self._vault: Dict[str, Dict[str, Any]] = {}
        self._access_log: List[Dict[str, Any]] = []

    def _encrypt(self, value: str) -> str:
        """Encrypt value (simplified - use proper encryption in production)"""
        # In production: use proper encryption (AES-256)
        # This is a demonstration only
        encoded = base64.b64encode(value.encode()).decode()
        return encoded

    def _decrypt(self, encrypted: str) -> str:
        """Decrypt value"""
        return base64.b64decode(encrypted.encode()).decode()

    def store(self, key: str, value: str, metadata: Dict[str, Any] = None):
        """Store a secret"""
        encrypted = self._encrypt(value)

        self._vault[key] = {
            "encrypted_value": encrypted,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "version": 1
        }

        self._log_access("store", key)

    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve a secret"""
        if key not in self._vault:
            return None

        self._log_access("retrieve", key)
        encrypted = self._vault[key]["encrypted_value"]
        return self._decrypt(encrypted)

    def delete(self, key: str):
        """Delete a secret"""
        if key in self._vault:
            del self._vault[key]
            self._log_access("delete", key)

    def list_keys(self) -> List[str]:
        """List all secret keys (not values)"""
        return list(self._vault.keys())

    def _log_access(self, action: str, key: str):
        """Log access for audit"""
        self._access_log.append({
            "action": action,
            "key": key,
            "timestamp": datetime.now().isoformat()
        })

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get access audit log"""
        return self._access_log.copy()


class AgentAuth:
    """
    Agent Authentication
    ====================

    Provides authentication and authorization for agents
    """

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.api_keys: Dict[str, str] = {}  # key -> agent_id

    def register_agent(
        self,
        agent_id: str,
        name: str,
        permissions: List[str] = None,
        api_key: str = None
    ) -> str:
        """Register an agent"""
        # Generate API key if not provided
        if not api_key:
            api_key = self._generate_api_key()

        self.agents[agent_id] = {
            "name": name,
            "permissions": permissions or [],
            "api_key_hash": self._hash_key(api_key),
            "created_at": datetime.now().isoformat(),
            "active": True
        }

        self.api_keys[api_key] = agent_id
        return api_key

    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"agentos_{secrets.token_urlsafe(32)}"

    def _hash_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def authenticate(self, api_key: str) -> Optional[str]:
        """Authenticate via API key"""
        key_hash = self._hash_key(api_key)

        for agent_id, agent in self.agents.items():
            if agent["api_key_hash"] == key_hash and agent["active"]:
                return agent_id

        return None

    def authorize(self, agent_id: str, resource: str, action: str) -> bool:
        """Check if agent is authorized for action"""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        return resource in agent.get("permissions", []) or "admin" in agent["permissions"]

    def revoke_agent(self, agent_id: str):
        """Revoke agent access"""
        if agent_id in self.agents:
            self.agents[agent_id]["active"] = False


class RequestSigner:
    """
    Request Signing for Agent Communication
    =========================================

    Ensures message integrity and authenticity
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def sign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sign a request payload"""
        # Create signature
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            **payload,
            "_signature": signature,
            "_timestamp": datetime.now().isoformat()
        }

    def verify(self, payload: Dict[str, Any]) -> bool:
        """Verify request signature"""
        if "_signature" not in payload:
            return False

        # Extract signature
        provided_sig = payload.pop("_signature")

        # Recompute
        message = json.dumps(payload, sort_keys=True)
        expected_sig = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(provided_sig, expected_sig)


class RateLimiter:
    """
    Rate Limiting for Agent API
    ============================

    Prevents abuse by limiting request rates
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[str]] = {}

    def check(self, client_id: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                ts for ts in self.requests[client_id]
                if datetime.fromisoformat(ts) > window_start
            ]
        else:
            self.requests[client_id] = []

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        # Record request
        self.requests[client_id].append(now.isoformat())
        return True

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests"""
        if client_id not in self.requests:
            return self.max_requests

        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)

        current = [
            ts for ts in self.requests[client_id]
            if datetime.fromisoformat(ts) > window_start
        ]

        return max(0, self.max_requests - len(current))


# Demo runner
def run_security_demo():
    """Demonstrate security features"""

    print("=" * 70)
    print("AgentOS Security Framework Demo")
    print("=" * 70)

    # Test SecureConfig
    print("\n[1] Secure Configuration")
    print("-" * 40)

    config = SecureConfig()

    # Set secrets
    config.set("OPENAI_API_KEY", "sk-xxx...", SecretLevel.RESTRICTED)
    config.set("DATABASE_URL", "postgresql://...", SecretLevel.CONFIDENTIAL)
    config.set("APP_NAME", "AgentOS", SecretLevel.PUBLIC)

    print("Stored secrets:")
    for secret in config.list_secrets():
        print(f"  {secret['key']}: {secret['level']}")

    print(f"API Key retrieved: {config.get('OPENAI_API_KEY')[:10]}...")

    # Test Vault
    print("\n[2] Agent Vault")
    print("-" * 40)

    vault = AgentVault("my_master_key")

    vault.store("database_password", "supersecret123", {"env": "prod"})
    vault.store("api_token", "token_abc", {"service": "openai"})

    print("Stored keys:", vault.list_keys())
    print(f"Retrieved password: {vault.retrieve('database_password')}")

    # Test Authentication
    print("\n[3] Agent Authentication")
    print("-" * 40)

    auth = AgentAuth()

    api_key = auth.register_agent(
        "agent_001",
        "DataProcessor",
        permissions=["read", "process"]
    )

    print(f"Registered agent with API key: {api_key[:30]}...")

    # Authenticate
    agent_id = auth.authenticate(api_key)
    print(f"Authenticated: {agent_id}")

    # Authorize
    can_read = auth.authorize(agent_id, "read", "process")
    print(f"Can read: {can_read}")

    # Test Request Signing
    print("\n[4] Request Signing")
    print("-" * 40)

    signer = RequestSigner("shared_secret")

    payload = {"action": "process", "data": "test"}
    signed = signer.sign(payload)

    print(f"Signed payload has signature: {'_signature' in signed}")

    is_valid = signer.verify(signed)
    print(f"Verification: {is_valid}")

    # Test Rate Limiting
    print("\n[5] Rate Limiting")
    print("-" * 40)

    limiter = RateLimiter(max_requests=5, window_seconds=60)

    for i in range(7):
        allowed = limiter.check("client_001")
        print(f"Request {i+1}: {'Allowed' if allowed else 'Blocked'}")
        print(f"  Remaining: {limiter.get_remaining('client_001')}")

    print("\n" + "=" * 70)
    print("Security demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    run_security_demo()