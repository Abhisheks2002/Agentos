"""
Day 92: Quantum-Resistant Cryptography for Agents
===================================================

Implementing post-quantum cryptographic algorithms to secure agent
communications against future quantum computing threats.

Key Concepts:
- Post-Quantum Algorithms
- Lattice-Based Cryptography
- Hash-Based Signatures
- Key Encapsulation
- Quantum-Safe Key Exchange
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import hashlib
import random
import base64


class CryptoAlgorithm(Enum):
    """Post-Quantum Cryptographic Algorithms"""
    KYBER = "kyber"           # Key encapsulation
    DILITHIUM = "dilithium"   # Digital signatures
    FALCON = "falcon"         # Digital signatures
    SPHINCS = "sphincs"       # Hash-based signatures
    BIKE = "bike"             # Key encapsulation
    NTRU = "ntru"             # Lattice-based


class KeyType(Enum):
    """Key Types"""
    ENCRYPTION = "encryption"
    SIGNING = "signing"
    KEY_EXCHANGE = "key_exchange"
    SESSION = "session"


class KeyStatus(Enum):
    """Key Status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPROMISED = "compromised"


@dataclass
class QuantumKey:
    """Quantum-Resistant Key"""
    key_id: str
    key_type: KeyType
    algorithm: CryptoAlgorithm
    public_key: bytes
    private_key: Optional[bytes]
    key_status: KeyStatus
    created_at: datetime
    expires_at: datetime
    key_size_bits: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KeyPair:
    """Key Pair"""
    public_key: bytes
    private_key: bytes
    algorithm: CryptoAlgorithm
    key_id: str


@dataclass
class EncryptedMessage:
    """Encrypted Message"""
    message_id: str
    ciphertext: bytes
    algorithm: CryptoAlgorithm
    encapsulation: bytes  # For key encapsulation
    nonce: bytes
    auth_tag: Optional[bytes]


@dataclass
class SignedMessage:
    """Signed Message"""
    message_id: str
    content: bytes
    signature: bytes
    algorithm: CryptoAlgorithm
    public_key_id: str


class LatticeParameters:
    """Lattice-based Cryptography Parameters"""

    # Kyber-768 security level (NIST Round 3)
    KYBER_512_PARAMS = {
        "n": 512,
        "k": 2,
        "q": 3329,
        "eta": 3,
        "du": 10,
        "dv": 4
    }

    KYBER_768_PARAMS = {
        "n": 512,
        "k": 3,
        "q": 3329,
        "eta": 2,
        "du": 10,
        "dv": 4
    }

    KYBER_1024_PARAMS = {
        "n": 512,
        "k": 4,
        "q": 3329,
        "eta": 2,
        "du": 11,
        "dv": 5
    }


class KyberKEM:
    """
    Kyber Key Encapsulation Mechanism
    ===================================

    Implements Kyber-768 for quantum-resistant key exchange.
    """

    def __init__(self, params: Dict = None):
        self.params = params or LatticeParameters.KYBER_768_PARAMS
        self.n = self.params["n"]
        self.q = self.params["q"]
        self.k = self.params["k"]

    def generate_keypair(self) -> KeyPair:
        """Generate Kyber key pair"""
        # Simplified key generation (actual Kyber is more complex)
        seed = random.randbytes(32)

        # Generate public/private keys
        public_key = self._generate_polynomial(seed, self.k * self.n)
        private_key = hashlib.sha256(public_key + seed).digest()

        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=CryptoAlgorithm.KYBER,
            key_id=str(uuid.uuid4())
        )

    def _generate_polynomial(self, seed: bytes, size: int) -> bytes:
        """Generate polynomial from seed"""
        # Simplified polynomial generation
        result = bytearray(size)
        for i in range(size):
            result[i] = seed[i % len(seed)] ^ (i * 17 % 256)
        return bytes(result)

    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate shared secret"""
        # Simulate encapsulation
        ciphertext = hashlib.sha256(public_key + b"encapsulation").digest()[:32]
        shared_secret = hashlib.sha256(public_key + b"shared").digest()[:32]
        return ciphertext, shared_secret

    def decapsulate(self, private_key: bytes, encapsulation: bytes) -> bytes:
        """Decapsulate shared secret"""
        # Simulate decapsulation
        shared_secret = hashlib.sha256(private_key + encapsulation).digest()[:32]
        return shared_secret


class DilithiumSignature:
    """
    Dilithium Digital Signature
    ============================

    Implements Dilithium for quantum-resistant signatures.
    """

    def __init__(self, security_level: str = "medium"):
        self.security_level = security_level
        self.params = {
            "low": {"k": 2, "l": 2, "eta": 2, "beta": 4},
            "medium": {"k": 3, "l": 3, "eta": 2, "beta": 4},
            "high": {"k": 4, "l": 4, "eta": 2, "beta": 6}
        }.get(security_level, {"k": 3, "l": 3, "eta": 2, "beta": 4})

    def generate_keypair(self) -> KeyPair:
        """Generate Dilithium key pair"""
        seed = random.randbytes(32)

        # Generate signature keys
        public_key = hashlib.sha512(seed + b"public").digest()[:32]
        private_key = hashlib.sha512(seed + b"private").digest()[:32]

        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=CryptoAlgorithm.DILITHIUM,
            key_id=str(uuid.uuid4())
        )

    def sign(self, message: bytes, private_key: bytes) -> bytes:
        """Sign message"""
        # Simplified signature
        msg_hash = hashlib.sha512(message + private_key).digest()
        signature = hashlib.sha512(msg_hash + b"signature").digest()[:64]
        return signature

    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify signature"""
        expected_sig = hashlib.sha512(
            hashlib.sha512(message + public_key).digest() + b"signature"
        ).digest()[:64]
        return signature == expected_sig


class SPHINCSSignature:
    """
    SPHINCS+ Hash-Based Signature
    =============================

    Stateless hash-based signature scheme.
    """

    def __init__(self, variant: str = "sha256"):
        self.variant = variant

    def generate_keypair(self) -> KeyPair:
        """Generate SPHINCS key pair"""
        seed = random.randbytes(48)

        public_key = hashlib.sha3_512(seed + b"pk").digest()[:32]
        private_key = hashlib.sha3_512(seed + b"sk").digest()[:32]

        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=CryptoAlgorithm.SPHINCS,
            key_id=str(uuid.uuid4())
        )

    def sign(self, message: bytes, private_key: bytes) -> bytes:
        """Sign message with SPHINCS"""
        # Hash-based signature simulation
        msg_hash = hashlib.sha3_512(message + private_key).digest()

        # Multiple hash iterations for Merkle tree structure
        sig = msg_hash
        for _ in range(64):
            sig = hashlib.sha3_512(sig + private_key).digest()

        return sig[:48]  # SPHINCS signature size

    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify SPHINCS signature"""
        # Verify using public key
        msg_hash = hashlib.sha3_512(message + public_key).digest()

        # Reconstruct expected signature
        expected_sig = msg_hash
        for _ in range(64):
            expected_sig = hashlib.sha3_512(expected_sig + public_key).digest()

        expected_sig = expected_sig[:48]
        return signature == expected_sig


class NTRUEncrypt:
    """
    NTRU Lattice-Based Encryption
    =============================

    Alternative lattice-based encryption scheme.
    """

    def __init__(self, security_level: int = 743):
        self.security_level = security_level

    def generate_keypair(self) -> KeyPair:
        """Generate NTRU key pair"""
        seed = random.randbytes(32)

        public_key = hashlib.sha256(seed + b"ntru_pk").digest()[:32]
        private_key = hashlib.sha256(seed + b"ntru_sk").digest()[:32]

        return KeyPair(
            public_key=public_key,
            private_key=private_key,
            algorithm=CryptoAlgorithm.NTRU,
            key_id=str(uuid.uuid4())
        )

    def encrypt(self, message: bytes, public_key: bytes) -> bytes:
        """Encrypt message"""
        # Simplified NTRU encryption
        ciphertext = bytearray(len(message) + 32)

        for i, byte in enumerate(message):
            ciphertext[i] = byte ^ public_key[i % len(public_key)]

        # Add randomness
        random.seed(public_key)
        for i in range(len(message), len(ciphertext)):
            ciphertext[i] = random.randint(0, 255)

        return bytes(ciphertext)

    def decrypt(self, ciphertext: bytes, private_key: bytes) -> bytes:
        """Decrypt message"""
        # Simplified decryption
        private_key_hash = hashlib.sha256(private_key).digest()

        message = bytearray(len(ciphertext) - 32)
        for i in range(len(message)):
            message[i] = ciphertext[i] ^ private_key_hash[i % len(private_key_hash)]

        return bytes(message)


class QuantumKeyManager:
    """
    Quantum-Resistant Key Manager
    ==============================

    Manages quantum-resistant keys across the agent system.
    """

    def __init__(self):
        self.keys: Dict[str, QuantumKey] = {}
        self.kyber = KyberKEM()
        self.dilithium = DilithiumSignature()
        self.sphincs = SPHINCSSignature()
        self.ntru = NTRUEncrypt()
        self.session_keys: Dict[str, bytes] = {}

    def generate_key(
        self,
        key_type: KeyType,
        algorithm: CryptoAlgorithm,
        validity_days: int = 365
    ) -> QuantumKey:
        """Generate quantum-resistant key"""
        key_id = str(uuid.uuid4())

        if algorithm == CryptoAlgorithm.KYBER:
            keypair = self.kyber.generate_keypair()
        elif algorithm == CryptoAlgorithm.DILITHIUM:
            keypair = self.dilithium.generate_keypair()
        elif algorithm == CryptoAlgorithm.SPHINCS:
            keypair = self.sphincs.generate_keypair()
        elif algorithm == CryptoAlgorithm.NTRU:
            keypair = self.ntru.generate_keypair()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        now = datetime.now()
        key = QuantumKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=algorithm,
            public_key=keypair.public_key,
            private_key=keypair.private_key,
            key_status=KeyStatus.ACTIVE,
            created_at=now,
            expires_at=now.replace(year=now.year + 1) if validity_days > 365 else
                       datetime.now().timestamp() + validity_days * 86400,
            key_size_bits=len(keypair.public_key) * 8,
            metadata={"keypair_id": keypair.key_id}
        )

        self.keys[key_id] = key
        print(f"[QKM] Generated {algorithm.value} key: {key_id[:8]}...")
        return key

    def encrypt_message(
        self,
        message: bytes,
        recipient_key_id: str,
        algorithm: CryptoAlgorithm = CryptoAlgorithm.KYBER
    ) -> EncryptedMessage:
        """Encrypt message with quantum-resistant encryption"""
        if recipient_key_id not in self.keys:
            raise ValueError(f"Key not found: {recipient_key_id}")

        key = self.keys[recipient_key_id]
        encapsulation, shared_secret = self.kyber.encapsulate(key.public_key)

        # Derive encryption key
        encryption_key = hashlib.sha256(shared_secret).digest()

        # Encrypt message (simplified)
        ciphertext = bytearray(len(message))
        for i, byte in enumerate(message):
            ciphertext[i] = byte ^ encryption_key[i % len(encryption_key)]

        return EncryptedMessage(
            message_id=str(uuid.uuid4()),
            ciphertext=bytes(ciphertext),
            algorithm=algorithm,
            encapsulation=encapsulation,
            nonce=shared_secret[:12]
        )

    def decrypt_message(
        self,
        encrypted: EncryptedMessage,
        recipient_key_id: str
    ) -> bytes:
        """Decrypt quantum-resistant message"""
        if recipient_key_id not in self.keys:
            raise ValueError(f"Key not found: {recipient_key_id}")

        key = self.keys[recipient_key_id]
        if not key.private_key:
            raise ValueError("No private key available")

        shared_secret = self.kyber.decapsulate(
            key.private_key,
            encrypted.encapsulation
        )

        encryption_key = hashlib.sha256(shared_secret).digest()

        # Decrypt
        message = bytearray(len(encrypted.ciphertext))
        for i, byte in enumerate(encrypted.ciphertext):
            message[i] = byte ^ encryption_key[i % len(encryption_key)]

        return bytes(message)

    def sign_message(
        self,
        message: bytes,
        signer_key_id: str,
        algorithm: CryptoAlgorithm = CryptoAlgorithm.DILITHIUM
    ) -> SignedMessage:
        """Sign message with quantum-resistant signature"""
        if signer_key_id not in self.keys:
            raise ValueError(f"Key not found: {signer_key_id}")

        key = self.keys[signer_key_id]
        if not key.private_key:
            raise ValueError("No private key available")

        if algorithm == CryptoAlgorithm.DILITHIUM:
            signature = self.dilithium.sign(message, key.private_key)
        elif algorithm == CryptoAlgorithm.SPHINCS:
            signature = self.sphincs.sign(message, key.private_key)
        else:
            raise ValueError(f"Unsupported signing algorithm: {algorithm}")

        return SignedMessage(
            message_id=str(uuid.uuid4()),
            content=message,
            signature=signature,
            algorithm=algorithm,
            public_key_id=key_id
        )

    def verify_signature(self, signed: SignedMessage) -> bool:
        """Verify quantum-resistant signature"""
        if signed.public_key_id not in self.keys:
            return False

        key = self.keys[signed.public_key_id]

        if signed.algorithm == CryptoAlgorithm.DILITHIUM:
            return self.dilithium.verify(signed.content, signed.signature, key.public_key)
        elif signed.algorithm == CryptoAlgorithm.SPHINCS:
            return self.sphincs.verify(signed.content, signed.signature, key.public_key)

        return False

    def establish_session(
        self,
        agent_a_id: str,
        agent_b_id: str,
        agent_a_key_id: str,
        agent_b_key_id: str
    ) -> str:
        """Establish quantum-resistant session"""
        key_a = self.keys.get(agent_a_key_id)
        key_b = self.keys.get(agent_b_key_id)

        if not key_a or not key_b:
            raise ValueError("Keys not found")

        # Create session key via Kyber
        encapsulation, shared_secret = self.kyber.encapsulate(key_b.public_key)
        session_key = hashlib.sha256(shared_secret + key_a.public_key).digest()

        session_id = str(uuid.uuid4())
        self.session_keys[session_id] = session_key

        print(f"[QKM] Established quantum-resistant session: {session_id[:8]}...")
        return session_id

    def rotate_key(self, key_id: str) -> QuantumKey:
        """Rotate key with new quantum-resistant key"""
        if key_id not in self.keys:
            raise ValueError(f"Key not found: {key_id}")

        old_key = self.keys[key_id]
        new_key = self.generate_key(old_key.key_type, old_key.algorithm)

        # Revoke old key
        old_key.key_status = KeyStatus.REVOKED

        return new_key


async def main():
    """Demonstrate Quantum-Resistant Cryptography"""
    print("=" * 60)
    print("Quantum-Resistant Cryptography - Day 92")
    print("=" * 60)

    # Initialize quantum key manager
    qkm = QuantumKeyManager()

    # Generate keys
    print("\n[1] Key Generation")
    print("-" * 40)

    kyber_key = qkm.generate_key(KeyType.KEY_EXCHANGE, CryptoAlgorithm.KYBER)
    dilithium_key = qkm.generate_key(KeyType.SIGNING, CryptoAlgorithm.DILITHIUM)
    sphincs_key = qkm.generate_key(KeyType.SIGNING, CryptoAlgorithm.SPHINCS)
    ntru_key = qkm.generate_key(KeyType.ENCRYPTION, CryptoAlgorithm.NTRU)

    print(f"  Kyber key: {kyber_key.key_size_bits}-bit")
    print(f"  Dilithium key: {dilithium_key.key_size_bits}-bit")
    print(f"  SPHINCS key: {sphincs_key.key_size_bits}-bit")
    print(f"  NTRU key: {ntru_key.key_size_bits}-bit")

    # Encryption
    print("\n[2] Quantum-Resistant Encryption")
    print("-" * 40)

    message = b"Confidential agent message"
    encrypted = qkm.encrypt_message(message, kyber_key.key_id, CryptoAlgorithm.KYBER)
    print(f"  Original: {message[:30]}...")
    print(f"  Algorithm: {encrypted.algorithm.value}")
    print(f"  Encapsulation: {encrypted.encapsulation[:16].hex()}...")

    decrypted = qkm.decrypt_message(encrypted, kyber_key.key_id)
    print(f"  Decrypted: {decrypted[:30]}...")

    # Digital Signatures
    print("\n[3] Quantum-Resistant Signatures")
    print("-" * 40)

    # Dilithium signature
    signed_dilithium = qkm.sign_message(message, dilithium_key.key_id, CryptoAlgorithm.DILITHIUM)
    dilithium_valid = qkm.verify_signature(signed_dilithium)
    print(f"  Dilithium signature: {'VALID' if dilithium_valid else 'INVALID'}")

    # SPHINCS signature
    signed_sphincs = qkm.sign_message(message, sphincs_key.key_id, CryptoAlgorithm.SPHINCS)
    sphincs_valid = qkm.verify_signature(signed_sphincs)
    print(f"  SPHINCS signature: {'VALID' if sphincs_valid else 'INVALID'}")

    # Session establishment
    print("\n[4] Quantum-Resistant Session")
    print("-" * 40)

    session_id = qkm.establish_session(
        "agent-001",
        "agent-002",
        kyber_key.key_id,
        kyber_key.key_id  # Using same key for demo
    )
    print(f"  Session ID: {session_id}")
    print(f"  Active sessions: {len(qkm.session_keys)}")

    # Key management
    print("\n[5] Key Management")
    print("-" * 40)

    all_keys = list(qkm.keys.keys())
    print(f"  Total keys: {len(all_keys)}")

    # Key rotation
    new_kyber = qkm.rotate_key(kyber_key.key_id)
    print(f"  Key rotated: {kyber_key.key_id[:8]} -> {new_kyber.key_id[:8]}")

    active_keys = sum(1 for k in qkm.keys.values() if k.key_status == KeyStatus.ACTIVE)
    print(f"  Active keys: {active_keys}")

    # Multiple algorithms comparison
    print("\n[6] Algorithm Comparison")
    print("-" * 40)

    algorithms = [
        ("Kyber-768", CryptoAlgorithm.KYBER),
        ("Dilithium-3", CryptoAlgorithm.DILITHIUM),
        ("SPHINCS+-256s", CryptoAlgorithm.SPHINCS),
        ("NTRU-743", CryptoAlgorithm.NTRU)
    ]

    for name, algo in algorithms:
        key = qkm.generate_key(KeyType.ENCRYPTION, algo)
        sizes = {
            CryptoAlgorithm.KYBER: ("1184 bytes", "1088 bytes"),
            CryptoAlgorithm.DILITHIUM: ("1952 bytes", "4000 bytes"),
            CryptoAlgorithm.SPHINCS: ("64 bytes", "128 bytes"),
            CryptoAlgorithm.NTRU: ("1138 bytes", "1178 bytes")
        }
        pub, priv = sizes.get(algo, ("?", "?"))
        print(f"  {name}: Public={pub}, Private={priv}")

    print("\n" + "=" * 60)
    print("Quantum-Resistant Cryptography complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())