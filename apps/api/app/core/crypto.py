"""Encryption of provider API keys at rest (exam-ingestion ADR-07)."""
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.core.errors import AppError


def _fernet() -> Fernet:
    key = get_settings().app_encryption_key
    if not key:
        raise AppError("encryption_unavailable", "Máy chủ chưa cấu hình APP_ENCRYPTION_KEY nên không lưu được khóa API", 500)
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
