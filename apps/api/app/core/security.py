from datetime import UTC, datetime, timedelta
import hashlib
import secrets
import uuid

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import get_settings

# time_cost/memory tuned so a verify stays well under 100 ms on Apple M-series and Ampere A1.
_hasher = PasswordHash((Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1),))
_DUMMY_HASH = _hasher.hash("examind-timing-equaliser")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Always spends one argon2 verify, so unknown users cost the same as wrong passwords."""
    try:
        return _hasher.verify(password, password_hash or _DUMMY_HASH) and password_hash is not None
    except Exception:
        return False


def now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: uuid.UUID, org_id: uuid.UUID, org_code: str, role: str) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "org_code": org_code,
        "role": role,
        "iat": now(),
        "exp": now() + timedelta(minutes=s.access_token_minutes),
        "typ": "access",
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        data = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    return data if data.get("typ") == "access" else None


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
