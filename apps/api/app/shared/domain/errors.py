"""Domain errors: what went wrong, in the business' words. The interface layer turns them into HTTP."""


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str, field: str | None = None, *, code: str | None = None, fields: dict | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.fields = fields if fields is not None else ({field: message} if field else None)


class NotFound(DomainError):
    code = "not_found"

    def __init__(self, message: str = "Không tìm thấy", field: str | None = None, **kw):
        super().__init__(message, field, **kw)


class Conflict(DomainError):
    code = "conflict"


class Invalid(DomainError):
    code = "validation_error"


class Forbidden(DomainError):
    code = "forbidden"

    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này", field: str | None = None, **kw):
        super().__init__(message, field, **kw)


class Unauthenticated(DomainError):
    code = "unauthenticated"

    def __init__(self, message: str = "Bạn cần đăng nhập", field: str | None = None, **kw):
        super().__init__(message, field, **kw)


class Throttled(DomainError):
    """Too many attempts: try again later."""
    code = "throttled"
