"""security.py - password hashing and password rules.

We NEVER store a real password. We store a hash: a one-way scrambled
version that cannot be turned back into the password.

Method used: PBKDF2-HMAC-SHA256 (built into Python's hashlib)
- a random salt per user, so two users with the same password get different hashes
- 200,000 iterations, which makes guessing passwords slow for an attacker
"""

import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 200_000


def hash_password(password):
    """Return a single string: algorithm$iterations$salt$hash"""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):
    """Check a typed password against the stored hash. Returns True or False."""
    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algorithm != ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, AttributeError):
        return False
    # compare_digest takes the same time however many characters match,
    # which stops "timing attacks"
    return hmac.compare_digest(digest.hex(), hash_hex)


def check_password_strength(password):
    """Return (ok, message). Rules: 8+ characters, at least one letter and one digit."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not any(ch.isalpha() for ch in password):
        return False, "Password must contain at least one letter."
    if not any(ch.isdigit() for ch in password):
        return False, "Password must contain at least one number."
    return True, "OK"
