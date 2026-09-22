"""Access JWTs (HS256) and opaque refresh tokens stored as SHA-256 digests (AccessTokens, Secrets)."""
from datetime import UTC, datetime, timedelta
import hashlib
import secrets
import uuid

import jwt

from app.core.config import get_settings
from app.modules.identity.infrastructure.adapters.passwords import temp_password

ALGORITHM = "HS256"


def create_access_token(user_id: uuid.UUID, org_id: uuid.UUID, org_code: str, role: str) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "org_code": org_code,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=s.access_token_minutes),
        "typ": "access",
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        data = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    return data if data.get("typ") == "access" else None


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


class JwtAccessTokens:
    def issue(self, user_id: uuid.UUID, org_id: uuid.UUID, org_code: str, role: str) -> str:
        return create_access_token(user_id, org_id, org_code, role)

    def decode(self, token: str) -> dict | None:
        """The claims of a valid, unexpired access token."""
        return decode_access_token(token)


class TokenSecrets:
    def temp_password(self) -> str:
        return temp_password()

    def refresh_token(self) -> tuple[str, str]:
        return new_refresh_token()

    def digest(self, raw: str) -> str:
        return hash_token(raw)
