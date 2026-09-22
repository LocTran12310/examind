"""One rule set for every screen that adds, changes or removes a membership (school-years ADR-04)."""
import uuid

from app.modules.identity.application.common import home_code, load_account, load_org
from app.modules.identity.application.dto import MembershipView
from app.modules.identity.application.ports import ClassDirectory
from app.modules.identity.domain.entities import ORG_ROLES, Membership, Organization, User
from app.modules.identity.domain.ports import MembershipRepository, OrganizationRepository, UserRepository
from app.modules.identity.domain.services.accounts import check_role
from app.shared.application.actor import Actor
from app.shared.application.audit import AuditTrail
from app.shared.domain.errors import Conflict, Invalid, NotFound


def membership_view(orgs: OrganizationRepository, m: Membership, user: User, org: Organization) -> MembershipView:
    return MembershipView(user_id=user.id, username=user.username, full_name=user.full_name, home_org_code=home_code(orgs, user),
                          org_id=org.id, org_code=org.code, org_name=org.name, role=m.role, is_active=m.is_active,
                          is_home=user.organization_id == org.id)


def load_side(users: UserRepository, orgs: OrganizationRepository, org_id: uuid.UUID, user_id: uuid.UUID, side: str) -> None:
    """The admin screens load the side they start from first: org → members (404 org), user → orgs (404 account)."""
    if side == "org":
        load_org(orgs, org_id)
    else:
        load_account(users, user_id)


def target_org(orgs: OrganizationRepository, org_id: uuid.UUID) -> Organization:
    org = orgs.get(org_id)
    if org is None or org.deleted_at is not None:
        raise NotFound("Không tìm thấy tổ chức")
    if org.is_system:
        raise Invalid("Không thêm thành viên vào tổ chức hệ thống", "org_id")
    return org


def add(orgs: OrganizationRepository, members: MembershipRepository, audit: AuditTrail, actor: Actor, org_id: uuid.UUID, user: User,
        role: str) -> Membership:
    check_role(role)
    target_org(orgs, org_id)
    existing = members.get(user.id, org_id)
    if existing is not None and existing.is_active:
        raise Conflict("Tài khoản đã là thành viên của tổ chức", "username")
    if existing is None:
        existing = Membership(user_id=user.id, organization_id=org_id, role=role, is_active=True)
        members.add(existing)
    else:
        existing.role, existing.is_active = role, True
    audit.record(actor, org_id, "member.link", "user", user.id, home=home_code(orgs, user), role=role, username=user.username)
    return existing


def update(users: UserRepository, members: MembershipRepository, audit: AuditTrail, actor: Actor, org_id: uuid.UUID, user_id: uuid.UUID,
           role: str | None = None, is_active: bool | None = None) -> tuple[User, Membership]:
    m = members.get(user_id, org_id)
    user = users.get(user_id)
    if m is None or user is None:
        raise NotFound("Không tìm thấy thành viên")
    home = user.organization_id == org_id
    changes = {}
    if role and role != m.role:
        if role not in ORG_ROLES:
            raise Invalid("Vai trò không hợp lệ", "role")
        changes["role"] = [m.role, role]
        m.role = role
        if home:
            user.role = role  # keeps users.role = home role (A-06)
    if is_active is not None and is_active != m.is_active:
        if home:
            raise Invalid("Khóa tài khoản ở tổ chức gốc bằng màn Người dùng của tổ chức đó", "is_active")
        changes["is_active"] = [m.is_active, is_active]
        m.is_active = is_active
    if changes:
        audit.record(actor, org_id, "member.update", "user", user_id, changes=changes, username=user.username)
    return user, m


def remove(users: UserRepository, members: MembershipRepository, classes: ClassDirectory, audit: AuditTrail, actor: Actor,
           org_id: uuid.UUID, user_id: uuid.UUID) -> None:
    m = members.get(user_id, org_id)
    user = users.get(user_id)
    if m is None or user is None:
        raise NotFound("Không tìm thấy thành viên")
    if user.organization_id == org_id:
        raise Invalid("Không gỡ được tổ chức gốc của tài khoản", "user_id")
    classes.leave_org_classes(org_id, user_id)
    members.remove(m)
    if user.last_org_id == org_id:
        user.last_org_id = None
    audit.record(actor, org_id, "member.unlink", "user", user_id, username=user.username)
