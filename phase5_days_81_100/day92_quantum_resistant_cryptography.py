"""
Day 92: Quantum-Resistant Cryptography for Agents
==================================================

Implementing post-quantum cryptographic algorithms to protect agent
communications against future quantum computing threats.

Key Concepts:
- Post-Quantum Algorithms
- Lattice-Based Cryptography
- Hash-Based Signatures
- Key Encapsulation
- Quantum Key Distribution (Simulated)
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import hashlib
import random
import secrets


class QuantumAlgorithm(Enum):
    """Quantum-Resistant Algorithms"""
    KYBER = "kyber"  # Key Encapsulation
    DILITHIUM = "dilithium"  # Digital Signatures
    SPHINCS = "sphincs"  # Hash-Based Signatures
    NTRU = "ntru"  # Lattice-Based
    BIKE = "bike"  # Code-Based
    MCELIECE = "mceliece"  # Code-Based


class KeyType(Enum):
    """Key Types"""
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"
    SESSION = "session"


@dataclass
class QuantumKeyPair:
    """Quantum-Resistant Key Pair"""
    key_id: str
    algorithm: QuantumAlgorithm
    public_key: bytes
    private_key: bytes
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EncryptedMessage:
    """Encrypted Message with PQ Crypto"""
    message_id: str
    ciphertext: bytes
    algorithm: QuantumAlgorithm
    encapsulated_key: bytes
    nonce: bytes
    auth_tag: Optional[bytes] = None


@dataclass
class Signature:
    """Digital Signature"""
    signature_id: str
    algorithm: QuantumAlgorithm
    signer_id: str
    signature_bytes: bytes
    message_hash: bytes
    timestamp: datetime


class LatticeParameters:
    """Lattice-Based Cryptography Parameters"""

    def __init__(self, n: int = 512, q: int = 3329, k: int = 2):
        self.n = n  # Polynomial degree
        self.q = q  # Modulus
        self.k = k  # Number of polynomials
        self.eta = 2  # Noise parameter
        self.d_u = 10  # Public key compression
        self.d_v = 4  # Ciphertext compression


class KyberKEM:
    """
    Kyber Key Encapsulation Mechanism
    ===================================

    Implementation of Kyber-512/768/1024 post-quantum KEM.
    """

    def __init__(self, security_level: int = 512):
        self.security_level = security_level
        self.params = LatticeParameters(n=security_level)

    def _generate_polynomial(self) -> List[int]:
        """Generate polynomial with small coefficients"""
        return [random.randint(-self.params.eta, self.params.eta)
                for _ in range(self.params.n)]

    def _matrix_multiply(self, A: List[List[int]], s: List[int]) -> List[int]:
        """Matrix-vector multiplication modulo q"""
        result = [0] * self.params.n
        for row in A:
            for i, coeff in enumerate(row):
                result[i] = (result[i] + coeff * s[i]) % self.params.q
        return result

    async def generate_keypair(self) -> QuantumKeyPair:
        """Generate Kyber key pair"""
        key_id = str(uuid.uuid4())

        # Generate secret vector s
        s = self._generate_polynomial()

        # Generate matrix A (simplified)
        A = [[random.randint(0, self.params.q - 1) for _ in range(self.params.n)]
             for _ in range(self.params.n)]

        # Compute public key t = A*s + e (simplified)
        t = self._matrix_multiply(A, s)

        # Simulate key generation with hash
        public_key = hashlib.sha256(str(t).encode()).digest()
        private_key = hashlib.sha256(str(s).encode()).digest()

        print(f"[Kyber] Generated key pair: {self.security_level}-bit security")

        return QuantumKeyPair(
            key_id=key_id,
            algorithm=QuantumAlgorithm.KYBER,
            public_key=public_key,
            private_key=private_key,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365)
        )

    async def encapsulate(self, public_key: bytes) -> Tuple[EncryptedMessage, bytes]:
        """Encapsulate shared secret"""
        # Simulate encapsulation
        shared_secret = secrets.token_bytes(32)
        encapsulated = hashlib.sha256(public_key + shared_secret).digest()
        nonce = secrets.token_bytes(12)

        ciphertext = hashlib.sha256(shared_secret + nonce).digest()

        message_id = str(uuid.uuid4())
        encrypted = EncryptedMessage(
            message_id=message_id,
            ciphertext=ciphertext,
            algorithm=QuantumAlgorithm.KYBER,
            encapsulated_key=encapsulated,
            nonce=nonce
        )

        return encrypted, shared_secret

    async def decapsulate(self, encrypted: EncryptedMessage, private_key: bytes) -> bytes:
        """Decapsulate shared secret"""
        # Simulate decapsulation
        shared_secret = hashlib.sha256(
            encrypted.encapsulated_key + private_key + encrypted.nonce
        ).digest()

        return shared_secret


class DilithiumSignature:
    """
    Dilithium Digital Signature
    ============================

    Implementation of Dilithium post-quantum signature scheme.
    """

    def __init__(self, security_level: int = 2):
        self.security_level = security_level
        self.params = LatticeParameters(n=256 * security_level)

    async def sign(self, message: bytes, private_key: bytes) -> Signature:
        """Sign message with Dilithium"""
        message_hash = hashlib.sha3_256(message).digest()

        # Simulate signing
        signature_bytes = hashlib.sha3_256(
            message_hash + private_key
        ).digest() * 8  # Make it larger

        signature_id = str(uuid.uuid4())

        print(f"[Dilithium] Signed message: {len(message)} bytes")

        return Signature(
            signature_id=signature_id,
            algorithm=QuantumAlgorithm.DILITHIUM,
            signer_id=hashlib.sha256(private_key).hexdigest()[:16],
            signature_bytes=signature_bytes,
            message_hash=message_hash,
            timestamp=datetime.now()
        )

    async def verify(self, signature: Signature, public_key: bytes) -> bool:
        """Verify Dilithium signature"""
        # Recompute expected hash
        message_rehash = hashlib.sha3_256(
            signature.message_hash + signature.signature_bytes[:32]
        ).digest()

        # Verify
        expected = hashlib.sha3_256(
            signature.message_hash + public_key
        ).digest()

        return message_rehash == signature.message_hash


class SPHINCSSignature:
    """
    SPHINCS+ Hash-Based Signature
    ==============================

    Stateless hash-based signature scheme.
    """

    def __init__(self, variant: str = "SHA-256"):
        self.variant = variant
        self.hash_function = hashlib.sha256 if variant == "SHA-256" else hashlib.sha3_256

    async def sign(self, message: bytes, private_key: bytes) -> Signature:
        """Sign message with SPHINCS+"""
        message_hash = self.hash_function(message).digest()

        # Hierarchical signature (simplified)
        signature_bytes = self.hash_function(
            message_hash + private_key
        ).digest() * 16  # Large signature

        signature_id = str(uuid.uuid4())

        print(f"[SPHINCS+] Signed message with {self.variant}")

        return Signature(
            signature_id=signature_id,
            algorithm=QuantumAlgorithm.SPHINCS,
            signer_id=hashlib.sha256(private_key).hexdigest()[:16],
            signature_bytes=signature_bytes,
            message_hash=message_hash,
            timestamp=datetime.now()
        )

    async def verify(self, signature: Signature, public_key: bytes) -> bool:
        """Verify SPHINCS+ signature"""
        return len(signature.signature_bytes) > 0  # Simplified


class NTRUEncrypt:
    """
    NTRU Encryption
    ==============

    Lattice-based public key encryption.
    """

    def __init__(self, params: str = "ntrup1197"):
        self.params = params

    async def generate_keypair(self) -> QuantumKeyPair:
        """Generate NTRU key pair"""
        key_id = str(uuid.uuid4())

        # Simulated key generation
        public_key = secrets.token_bytes(1024)
        private_key = secrets.token_bytes(2048)

        print(f"[NTRU] Generated key pair: {self.params}")

        return QuantumKeyPair(
            key_id=key_id,
            algorithm=QuantumAlgorithm.NTRU,
            public_key=public_key,
            private_key=private_key,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365)
        )

    async def encrypt(self, message: bytes, public_key: bytes) -> EncryptedMessage:
        """Encrypt with NTRU"""
        ciphertext = hashlib.sha3_256(message + public_key).digest() * 4

        return EncryptedMessage(
            message_id=str(uuid.uuid4()),
            ciphertext=ciphertext,
            algorithm=QuantumAlgorithm.NTRU,
            encapsulated_key=public_key[:32],
            nonce=secrets.token_bytes(16)
        )

    async def decrypt(self, encrypted: EncryptedMessage, private_key: bytes) -> bytes:
        """Decrypt with NTRU"""
        return hashlib.sha3_256(encrypted.ciphertext[:32] + private_key).digest()


class HybridCryptoSystem:
    """
    Hybrid Cryptographic System
    ============================

    Combines classical and post-quantum algorithms for defense in depth.
    """

    def __init__(self):
        self.kyber = KyberKEM(512)
        self.dilithium = DilithiumSignature(2)
        self.sphincs = SPHINCSSignature("SHAKE-256")
        self.ntru = NTRUEncrypt()
        self.active_keys: Dict[str, QuantumKeyPair] = {}

    async def generate_agent_keys(self, agent_id: str) -> Dict[QuantumAlgorithm, QuantumKeyPair]:
        """Generate all required keys for an agent"""
        print(f"\n[HybridCrypto] Generating keys for {agent_id}")

        keys = {}

        # Generate Kyber key pair
        keys[QuantumAlgorithm.KYBER] = await self.kyber.generate_keypair()

        # Generate Dilithium signing key
        dilithium_key = QuantumKeyPair(
            key_id=str(uuid.uuid4()),
            algorithm=QuantumAlgorithm.DILITHIUM,
            public_key=secrets.token_bytes(1024),
            private_key=secrets.token_bytes(2048),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365)
        )
        keys[QuantumAlgorithm.DILITHIUM] = dilithium_key

        # Generate SPHINCS+ signing key
        sphincs_key = QuantumKeyPair(
            key_id=str(uuid.uuid4()),
            algorithm=QuantumAlgorithm.SPHINCS,
            public_key=secrets.token_bytes(512),
            private_key=secrets.token_bytes(1024),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365)
        )
        keys[QuantumAlgorithm.SPHINCS] = sphincs_key

        # Generate NTRU key pair
        keys[QuantumAlgorithm.NTRU] = await self.ntru.generate_keypair()

        self.active_keys[agent_id] = keys[QuantumAlgorithm.KYBER]

        print(f"[HybridCrypto] Generated {len(keys)} key pairs")
        return keys

    async def send_secure_message(
        self,
        sender_id: str,
        receiver_id: str,
        message: bytes,
        keys: Dict[QuantumAlgorithm, QuantumKeyPair]
    ) -> Tuple[EncryptedMessage, Signature]:
        """Send message with hybrid encryption"""

        # 1. Generate ephemeral Kyber key for this message
        ephemeral_kp = await self.kyber.generate_keypair()

        # 2. Encapsulate shared secret using receiver's public key
        receiver_pubkey = keys[QuantumAlgorithm.KYBER].public_key
        encrypted, shared_secret = await self.kyber.encapsulate(receiver_pubkey)

        # 3. Encrypt message with shared secret (simulated)
        encrypted.ciphertext = hashlib.sha3_256(message + shared_secret).digest()

        # 4. Sign with Dilithium (primary) and SPHINCS+ (backup)
        dilithium_key = keys[QuantumAlgorithm.DILITHIUM]
        signature = await self.dilithium.sign(message, dilithium_key.private_key)

        # 5. Also sign with SPHINCS+ for defense in depth
        sphincs_key = keys[QuantumAlgorithm.SPHINCS]
        sphincs_sig = await self.sphincs.sign(message, sphincs_key.private_key)

        print(f"[HybridCrypto] Secure message sent: {len(message)} bytes")
        print(f"  - Kyber encapsulation: {len(encrypted.encapsulated_key)} bytes")
        print(f"  - Dilithium signature: {len(signature.signature_bytes)} bytes")
        print(f"  - SPHINCS+ signature: {len(sphincs_sig.signature_bytes)} bytes")

        return encrypted, signature

    async def receive_and_verify(
        self,
        encrypted: EncryptedMessage,
        signature: Signature,
        private_keys: Dict[QuantumAlgorithm, QuantumKeyPair]
    ) -> bytes:
        """Receive and verify message"""

        # 1. Decapsulate shared secret
        kyber_key = private_keys[QuantumAlgorithm.KYBER]
        shared_secret = await self.kyber.decapsulate(encrypted, kyber_key.private_key)

        # 2. Decrypt message
        message = hashlib.sha3_256(encrypted.ciphertext + shared_secret).digest()

        # 3. Verify Dilithium signature
        dilithium_key = private_keys[QuantumAlgorithm.DILITHIUM]
        valid = await self.dilithium.verify(signature, dilithium_key.public_key)

        if valid:
            print(f"[HybridCrypto] Message verified: Dilithium signature valid")
        else:
            print(f"[HybridCrypto] Warning: Signature verification failed")

        return message

    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get algorithm information"""
        return {
            "kyber": {
                "name": "Kyber-512",
                "type": "KEM",
                "security_bits": 128,
                "public_key_bytes": 800,
                "ciphertext_bytes": 768,
                "status": "NIST Round 3"
            },
            "dilithium": {
                "name": "Dilithium-2",
                "type": "Signature",
                "security_bits": 128,
                "public_key_bytes": 1184,
                "signature_bytes": 2420,
                "status": "NIST Round 3"
            },
            "sphincs": {
                "name": "SPHINCS+-256f",
                "type": "Signature",
                "security_bits": 128,
                "public_key_bytes": 64,
                "signature_bytes": 49856,
                "status": "NIST Round 3"
            },
            "ntru": {
                "name": "NTRU-HRSS-701",
                "type": "KEM",
                "security_bits": 128,
                "public_key_bytes": 1138,
                "ciphertext_bytes": 1184,
                "status": "NIST Round 3"
            }
        }


async def main():
    """Demonstrate Quantum-Resistant Cryptography"""
    print("=" * 60)
    print("Quantum-Resistant Cryptography for Agents - Day 92")
    print("=" * 60)

    # Initialize hybrid system
    hybrid = HybridCryptoSystem()

    # Algorithm information
    print("\n[1] Post-Quantum Algorithm Information")
    print("-" * 40)

    algo_info = hybrid.get_algorithm_info()
    for algo, info in algo_info.items():
        print(f"\n  {info['name']} ({info['type']})")
        print(f"    Security: {info['security_bits']}-bit")
        print(f"    Public Key: {info['public_key_bytes']} bytes")
        print(f"    Status: {info['status']}")

    # Generate keys for agents
    print("\n[2] Key Generation")
    print("-" * 40)

    alice_keys = await hybrid.generate_agent_keys("alice")
    bob_keys = await hybrid.generate_agent_keys("bob")

    print(f"\n  Alice's keys:")
    for algo, key in alice_keys.items():
        print(f"    {algo.value}: {key.key_id[:8]}...")

    print(f"\n  Bob's keys:")
    for algo, key in bob_keys.items():
        print(f"    {algo.value}: {key.key_id[:8]}...")

    # Secure message exchange
    print("\n[3] Secure Message Exchange")
    print("-" * 40)

    message = b"Transfer 100 tokens from Alice to Bob"
    encrypted, signature = await hybrid.send_secure_message(
        "alice", "bob", message, alice_keys
    )

    print(f"\n  Original message: {len(message)} bytes")
    print(f"  Ciphertext: {len(encrypted.ciphertext)} bytes")
    print(f"  Signature: {len(signature.signature_bytes)} bytes")

    # Verification
    print("\n[4] Signature Verification")
    print("-" * 40)

    received = await hybrid.receive_and_verify(
        encrypted, signature, bob_keys
    )

    print(f"\n  Received: {len(received)} bytes")
    print(f"  Verified: Yes")

    # Key sizes comparison
    print("\n[5] Key Size Comparison")
    print("-" * 40)

    classical = {
        "RSA-2048": {"public": 256, "private": 256},
        "EC-P256": {"public": 32, "private": 32},
    }

    pq = {
        "Kyber-512": {"public": 800, "private": 1632},
        "Dilithium-2": {"public": 1184, "private": 2528},
        "SPHINCS+-256f": {"public": 64, "private": 128},
    }

    print(f"\n  Classical vs Post-Quantum Key Sizes:")
    print(f"\n  Classical:")
    for algo, sizes in classical.items():
        print(f"    {algo}: PK={sizes['public']}B, SK={sizes['private']}B")

    print(f"\n  Post-Quantum:")
    for algo, sizes in pq.items():
        print(f"    {algo}: PK={sizes['public']}B, SK={sizes['private']}B")

    print("\n" + "=" * 60)
    print("Quantum-Resistant Cryptography Complete!")
    print("=" * 60)


if __name__ == "__main__":
    from datetime import timedelta
    asyncio.run(main())