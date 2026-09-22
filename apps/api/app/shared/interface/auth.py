"""The calling Actor. The identity module registers how a request is authenticated (composition root);
every other module only asks for an Actor, so no module depends on identity's internals."""
from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.shared.application.actor import Actor
from app.shared.domain.errors import Forbidden
from app.shared.infrastructure.db import get_db

_resolver: Callable[[Request, Session], Actor] | None = None


def register_actor_resolver(fn: Callable[[Request, Session], Actor]) -> None:
    global _resolver
    _resolver = fn


def current_actor(request: Request, db: Session = Depends(get_db)) -> Actor:
    if _resolver is None:
        raise RuntimeError("no actor resolver registered")
    return _resolver(request, db)


def staff_actor(actor: Actor = Depends(current_actor)) -> Actor:
    if not actor.is_staff:
        raise Forbidden()
    return actor
