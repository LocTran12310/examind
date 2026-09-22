import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.identity.application.dto import AccountView, MembershipView, OrgView, UserView, org_view
from app.modules.identity.domain.entities import Organization, User
from app.modules.identity.infrastructure import orm  # noqa: F401  (mapping)
from app.shared.application.search import Page, SearchRequest
from app.shared.infrastructure.schema.academic import class_members, classes
from app.shared.infrastructure.schema.identity import organization_members, organizations, users
from app.shared.infrastructure.sql_search import Col, search

u, m, o = users.c, organization_members.c, organizations.c

USER_COLS = {
    "username": Col(u.username),
    "full_name": Col(u.full_name),
    "email": Col(u.email),
    "role": Col(m.role, "exact"),  # role in the org being viewed
    "is_active": Col(u.is_active & m.is_active, "bool"),
    "must_change_password": Col(u.must_change_password, "bool"),
    "created_at": Col(u.created_at, "date"),
    "last_login_at": Col(u.last_login_at, "date"),
}

ORG_COLS = {"code": Col(o.code), "name": Col(o.name), "status": Col(o.status, "exact"), "created_at": Col(o.created_at, "date")}

_home = organizations.alias("home_org")
ORG_COUNT = (select(func.count()).where(m.user_id == u.id, m.is_active.is_(True)).correlate(users).scalar_subquery())
ACCOUNT_COLS = {"username": Col(u.username), "full_name": Col(u.full_name), "home_org_code": Col(_home.c.code),
                "is_active": Col(u.is_active, "bool"), "org_count": Col(ORG_COUNT, filterable=False)}

MEMBER_COLS = {"username": Col(u.username), "full_name": Col(u.full_name), "role": Col(m.role, "exact"), "is_active": Col(m.is_active, "bool")}
MEMBERSHIP_COLS = {"org_code": Col(o.code), "org_name": Col(o.name), "role": Col(m.role, "exact")}


class SqlUserReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, org_id: uuid.UUID, req: SearchRequest, class_id: uuid.UUID | None = None,
               students_only: bool = False) -> Page[UserView]:
        stmt = (select(u.id, u.username, u.full_name, u.email, m.role, (u.is_active & m.is_active), u.must_change_password,
                       u.last_login_at, u.created_at, u.organization_id, _home.c.code)
                .join(organization_members, m.user_id == u.id).join(_home, _home.c.id == u.organization_id)
                .where(m.organization_id == org_id))
        if students_only:
            stmt = stmt.where(m.role == "student")
        if class_id:
            stmt = stmt.where(u.id.in_(select(class_members.c.user_id).where(class_members.c.class_id == class_id)))
        rows, total = search(self.session, stmt, req, USER_COLS, text=[u.username, u.full_name, u.email], scalars=False,
                             default_sort=[u.full_name, u.id])
        by_user = self.class_ids(org_id, [r[0] for r in rows])
        data = [UserView(id=r[0], username=r[1], full_name=r[2], email=r[3], role=r[4], is_active=r[5], must_change_password=r[6],
                         last_login_at=r[7], created_at=r[8], class_ids=by_user.get(r[0], []), is_home=r[9] == org_id, home_org_code=r[10])
                for r in rows]
        return Page(data, total, req.page, req.limit)

    def class_ids(self, org_id: uuid.UUID, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[uuid.UUID]]:
        if not user_ids:
            return {}
        stmt = (select(class_members.c.class_id, class_members.c.user_id).join(classes, classes.c.id == class_members.c.class_id)
                .where(class_members.c.user_id.in_(user_ids), classes.c.organization_id == org_id))
        out: dict = {}
        for cid, uid in self.session.execute(stmt):
            out.setdefault(uid, []).append(cid)
        return out


class SqlOrgReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, req: SearchRequest, include_deleted: bool = False) -> Page[OrgView]:
        stmt = select(Organization)
        if not include_deleted:
            stmt = stmt.where(o.deleted_at.is_(None))
        rows, total = search(self.session, stmt, req, ORG_COLS, text=[o.code, o.name], default_sort=[o.is_system.desc(), o.created_at.desc()])
        counts = self.user_counts([org.id for org in rows])
        return Page([org_view(org, counts.get(org.id, 0)) for org in rows], total, req.page, req.limit)

    def user_counts(self, org_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not org_ids:
            return {}
        rows = self.session.execute(select(m.organization_id, func.count()).where(m.organization_id.in_(org_ids), m.is_active.is_(True))
                                    .group_by(m.organization_id))
        return dict(rows.all())


class SqlAccountReader:
    def __init__(self, session: Session):
        self.session = session

    def search(self, req: SearchRequest) -> Page[AccountView]:
        stmt = (select(u.id, u.username, u.full_name, _home.c.code, _home.c.name, u.is_active, ORG_COUNT)
                .join(_home, _home.c.id == u.organization_id).where(_home.c.is_system.is_(False)))
        rows, total = search(self.session, stmt, req, ACCOUNT_COLS, text=[u.username, u.full_name, _home.c.code], scalars=False,
                             default_sort=[u.full_name, u.id])
        return Page([AccountView(id=r[0], username=r[1], full_name=r[2], home_org_code=r[3], home_org_name=r[4], is_active=r[5],
                                 org_count=r[6] or 0) for r in rows], total, req.page, req.limit)


class SqlMembershipReader:
    def __init__(self, session: Session):
        self.session = session

    def of_org(self, org: Organization, req: SearchRequest) -> Page[MembershipView]:
        stmt = (select(u.id, u.username, u.full_name, _home.c.code, m.role, m.is_active, u.organization_id)
                .select_from(organization_members).join(users, u.id == m.user_id).join(_home, _home.c.id == u.organization_id)
                .where(m.organization_id == org.id))
        rows, total = search(self.session, stmt, req, MEMBER_COLS, text=[u.username, u.full_name], scalars=False,
                             default_sort=[u.full_name, u.id])
        data = [MembershipView(user_id=r[0], username=r[1], full_name=r[2], home_org_code=r[3], org_id=org.id, org_code=org.code,
                               org_name=org.name, role=r[4], is_active=r[5], is_home=r[6] == org.id) for r in rows]
        return Page(data, total, req.page, req.limit)

    def of_user(self, user: User, req: SearchRequest) -> Page[MembershipView]:
        home_code = self.session.scalar(select(o.code).where(o.id == user.organization_id))
        stmt = (select(o.id, o.code, o.name, m.role, m.is_active).select_from(organization_members)
                .join(organizations, o.id == m.organization_id).where(m.user_id == user.id))
        rows, total = search(self.session, stmt, req, MEMBERSHIP_COLS, scalars=False,
                             default_sort=[(o.id != user.organization_id), o.name])
        data = [MembershipView(user_id=user.id, username=user.username, full_name=user.full_name, home_org_code=home_code, org_id=r[0],
                               org_code=r[1], org_name=r[2], role=r[3], is_active=r[4], is_home=r[0] == user.organization_id)
                for r in rows]
        return Page(data, total, req.page, req.limit)
