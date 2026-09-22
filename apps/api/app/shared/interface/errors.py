"""Errors → HTTP: `{code, message, details: {fields?, requestId}}` (architecture-refactor ADR-04)."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.shared.domain.errors import Conflict, DomainError, Forbidden, Invalid, Misconfigured, NotFound, Throttled, Unauthenticated
from app.shared.interface.request_id import HEADER, request_id

STATUS = {NotFound: 404, Conflict: 409, Invalid: 422, Forbidden: 403, Unauthenticated: 401, Throttled: 429, Misconfigured: 500}


def status_of(exc: DomainError) -> int:
    for cls in type(exc).__mro__:
        if cls in STATUS:
            return STATUS[cls]
    return 400


def error_response(request: Request, status: int, code: str, message: str, fields: dict | None = None) -> JSONResponse:
    rid = request_id(request)
    details: dict = {"requestId": rid}
    if fields:
        details["fields"] = fields
    return JSONResponse({"code": code, "message": message, "details": details}, status_code=status, headers={HEADER: rid} if rid else None)


def install(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError):
        return error_response(request, status_of(exc), exc.code, exc.message, exc.fields)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        fields = {}
        for e in exc.errors():
            loc = [str(p) for p in e["loc"] if p not in ("body", "query", "path")]
            fields[".".join(loc) or "_"] = e["msg"]
        return error_response(request, 422, "validation_error", "Dữ liệu không hợp lệ", fields)
