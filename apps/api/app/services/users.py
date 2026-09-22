# moved to app.modules.identity (architecture-refactor); the username rules are re-exported for the old layout
from app.modules.identity.domain.services.accounts import USERNAME_MSG, USERNAME_RE, base_username, can_manage  # noqa: F401
