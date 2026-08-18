"""
Security utilities for password/PIN hashing and secure verification using PBKDF2-HMAC-SHA256.
"""

import hashlib
import hmac
import os
from typing import Tuple

ITERATIONS = 100_000
SALT_SIZE = 16

def hash_secret(secret: str, salt: str = None) -> Tuple[str, str]:
    """
    Hashes a secret (PIN or password) using PBKDF2-HMAC-SHA256.
    Returns a tuple of (hash_hex, salt_hex).
    """
    if salt is None:
        salt_bytes = os.urandom(SALT_SIZE)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt)
        salt_hex = salt

    derived = hashlib.pbkdf2_hmac(
        'sha256',
        secret.encode('utf-8'),
        salt_bytes,
        ITERATIONS
    )
    return derived.hex(), salt_hex


def verify_secret(secret: str, stored_hash: str, stored_salt: str) -> bool:
    """
    Verifies a plain secret against a stored hash and salt.
    Uses constant-time comparison to prevent timing attacks.
    """
    new_hash, _ = hash_secret(secret, stored_salt)
    return hmac.compare_digest(new_hash, stored_hash)
