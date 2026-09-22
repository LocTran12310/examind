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
