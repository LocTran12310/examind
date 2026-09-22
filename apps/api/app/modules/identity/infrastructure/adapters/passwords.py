"""Argon2 password hashing and one-time passwords (PasswordHasher, Secrets.temp_password)."""
import secrets

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# time_cost/memory tuned so a verify stays well under 100 ms on Apple M-series and Ampere A1.
_hasher = PasswordHash((Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1),))
_DUMMY_HASH = _hasher.hash("examind-timing-equaliser")
# No 0/O, 1/l/I — temp passwords are read off paper by students.
ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Always spends one argon2 verify, so unknown users cost the same as wrong passwords."""
    try:
        return _hasher.verify(password, password_hash or _DUMMY_HASH) and password_hash is not None
    except Exception:
        return False


def temp_password(length: int = 10) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


class Argon2PasswordHasher:
    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, password: str, password_hash: str | None) -> bool:
        return verify_password(password, password_hash)
