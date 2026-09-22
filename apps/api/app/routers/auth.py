# moved to app.modules.identity (architecture-refactor); the login rate limiter is re-exported for the old test fixtures
from app.modules.identity.interface.deps import ip_limiter  # noqa: F401
