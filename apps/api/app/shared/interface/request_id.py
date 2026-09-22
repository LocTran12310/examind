"""Every response carries X-Request-Id (architecture-refactor ADR-04); a sane incoming id is kept."""
import re
import uuid

from fastapi import FastAPI, Request

HEADER = "X-Request-Id"
_VALID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def _request_id(request: Request, call_next):
        incoming = request.headers.get(HEADER, "")
        request.state.request_id = incoming if _VALID.match(incoming) else uuid.uuid4().hex
        response = await call_next(request)
        response.headers[HEADER] = request.state.request_id
        return response
