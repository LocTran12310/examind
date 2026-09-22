from app.modules.identity.domain.entities import Organization
from app.shared.domain.errors import Forbidden


def guard_system(org: Organization) -> None:
    if org.is_system:
        raise Forbidden("Không thể thay đổi tổ chức hệ thống")
