"""Identity failures. Login failures share one message whatever went wrong (ADR-05: no account enumeration)."""
from app.shared.domain.errors import Forbidden, NotFound, Throttled, Unauthenticated


def invalid_credentials() -> Unauthenticated:
    return Unauthenticated("Sai tổ chức, tên đăng nhập hoặc mật khẩu", code="invalid_credentials")


def org_suspended() -> Forbidden:
    return Forbidden("Tổ chức đang bị khóa", code="org_suspended")


def session_expired() -> Unauthenticated:
    return Unauthenticated("Phiên đăng nhập đã hết hạn")


def no_org_open() -> Unauthenticated:
    return Unauthenticated("Tổ chức của bạn đang bị khóa")


def account_locked(minutes: int) -> Throttled:
    return Throttled(f"Tài khoản tạm khóa, thử lại sau {minutes} phút", code="locked")


def too_many_logins() -> Throttled:
    return Throttled("Quá nhiều lần đăng nhập, thử lại sau 1 phút", code="locked")


def password_change_required() -> Forbidden:
    return Forbidden("Bạn cần đổi mật khẩu trước khi tiếp tục", code="password_change_required")


def user_not_found() -> NotFound:
    return NotFound("Không tìm thấy người dùng")


def org_not_found() -> NotFound:
    return NotFound("Không tìm thấy tổ chức")
