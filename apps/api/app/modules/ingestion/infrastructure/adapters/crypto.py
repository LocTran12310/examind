"""Encryption of provider API keys at rest (exam-ingestion ADR-07): Fernet with APP_ENCRYPTION_KEY."""
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.shared.domain.errors import Misconfigured


def _fernet() -> Fernet:
    key = get_settings().app_encryption_key
    if not key:
        raise Misconfigured("Máy chủ chưa cấu hình APP_ENCRYPTION_KEY nên không lưu được khóa API", code="encryption_unavailable")
    return Fernet(key.encode())


def encrypt(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return None


class FernetKeyCipher:
    """KeyCipher port."""

    def encrypt(self, plain: str) -> str:
        return encrypt(plain)

    def decrypt(self, token: str | None) -> str | None:
        return decrypt(token)
