"""Moved to the identity module's adapters (architecture-refactor); re-exported for the old layout. `now` stays here."""
from datetime import UTC, datetime

from app.modules.identity.infrastructure.adapters.passwords import hash_password, verify_password  # noqa: F401
from app.modules.identity.infrastructure.adapters.tokens import (  # noqa: F401
    ALGORITHM, create_access_token, decode_access_token, hash_token, new_refresh_token,
)


def now() -> datetime:
    return datetime.now(UTC)
