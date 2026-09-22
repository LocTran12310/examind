from app.shared.domain.errors import Forbidden


def check_reader(role: str, is_super: bool) -> None:
    """History is for org admins (their org) and the platform admin."""
    if role != "org_admin" and not is_super:
        raise Forbidden()


def reads_every_org(role: str, is_super: bool) -> bool:
    """The platform admin working as super_admin (the system org) sees every org's history."""
    return is_super and role == "super_admin"
