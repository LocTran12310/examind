from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, fields: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.fields = code, message, status, fields


def not_found(what: str = "Không tìm thấy") -> AppError:
    return AppError("not_found", what, 404)


def forbidden() -> AppError:
    return AppError("forbidden", "Bạn không có quyền thực hiện thao tác này", 403)


def conflict(message: str, field: str | None = None) -> AppError:
    return AppError("conflict", message, 409, {field: message} if field else None)


def validation(message: str, field: str | None = None) -> AppError:
    return AppError("validation_error", message, 422, {field: message} if field else None)


def _body(code: str, message: str, fields: dict | None = None) -> dict:
    err = {"code": code, "message": message}
    if fields:
        err["fields"] = fields
    return {"error": err}


def install(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(_body(exc.code, exc.message, exc.fields), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        fields = {}
        for e in exc.errors():
            loc = [str(p) for p in e["loc"] if p not in ("body", "query", "path")]
            fields[".".join(loc) or "_"] = e["msg"]
        return JSONResponse(_body("validation_error", "Dữ liệu không hợp lệ", fields), status_code=422)
