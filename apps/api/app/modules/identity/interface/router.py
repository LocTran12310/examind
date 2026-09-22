"""Identity routes: sessions (/auth), the header's org list (/me/orgs), users of the org (/users), platform admin (/admin)."""
import uuid

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from app.shared.infrastructure.config import get_settings
from app.modules.identity.application.commands.add_membership import AddMembership, AddMembershipHandler
from app.modules.identity.application.commands.change_org_status import ChangeOrgStatus, ChangeOrgStatusHandler
from app.modules.identity.application.commands.change_password import ChangePassword, ChangePasswordHandler
from app.modules.identity.application.commands.create_org import CreateOrg, CreateOrgHandler
from app.modules.identity.application.commands.create_user import CreateUser, CreateUserHandler
from app.modules.identity.application.commands.delete_org import DeleteOrg, DeleteOrgHandler
from app.modules.identity.application.commands.import_users import CommitImport, CommitImportHandler, PreviewImport, PreviewImportHandler
from app.modules.identity.application.commands.link_account import LinkAccount, LinkAccountHandler
from app.modules.identity.application.commands.login import Login, LoginHandler
from app.modules.identity.application.commands.logout import Logout, LogoutHandler
from app.modules.identity.application.commands.refresh_session import RefreshSession, RefreshSessionHandler
from app.modules.identity.application.commands.remove_membership import RemoveMembership, RemoveMembershipHandler
from app.modules.identity.application.commands.reset_password import ResetPassword, ResetPasswordHandler
from app.modules.identity.application.commands.switch_org import SwitchOrg, SwitchOrgHandler
from app.modules.identity.application.commands.unlink_account import UnlinkAccount, UnlinkAccountHandler
from app.modules.identity.application.commands.update_membership import UpdateMembership, UpdateMembershipHandler
from app.modules.identity.application.commands.update_org import UpdateOrg, UpdateOrgHandler
from app.modules.identity.application.commands.update_user import UpdateUser, UpdateUserHandler
from app.modules.identity.application.dto import SessionView
from app.modules.identity.application.queries.get_me import GetMeHandler
from app.modules.identity.application.queries.get_org import GetOrg, GetOrgHandler
from app.modules.identity.application.queries.get_user import GetUser, GetUserHandler
from app.modules.identity.application.queries.my_orgs import MyOrgsHandler
from app.modules.identity.application.queries.search_accounts import SearchAccounts, SearchAccountsHandler
from app.modules.identity.application.queries.search_memberships import (
    SearchOrgMembers, SearchOrgMembersHandler, SearchUserMemberships, SearchUserMembershipsHandler,
)
from app.modules.identity.application.queries.search_orgs import SearchOrgs, SearchOrgsHandler
from app.modules.identity.application.queries.search_users import SearchUsers, SearchUsersHandler
from app.modules.identity.interface import deps
from app.modules.identity.interface.deps import ACCESS_COOKIE, REFRESH_COOKIE, client_ip, super_actor
from app.modules.identity.interface.schemas import (
    AccountOut, ChangePasswordIn, Credential, ImportRowsIn, LinkIn, LoginIn, MemberIn, MembershipIn, MembershipOut, MembershipPatch, MeOut,
    MyOrgOut, OrgCreate, OrgCreated, OrgOut, OrgSearchBody, OrgUpdate, SwitchOrgIn, UserCreate, UserCreated, UserOut, UserSearchBody,
    UserUpdate, AdminCredential, account_out, me_out, membership_out, org_out, user_out,
)
from app.shared.application.actor import Actor
from app.shared.interface.auth import current_actor, staff_actor
from app.shared.interface.search_schemas import PageOut, SearchBody

router = APIRouter(tags=["identity"])


def _page(page, out) -> PageOut:
    return PageOut(data=[out(v) for v in page.data], total=page.total, page=page.page, limit=page.limit)


def _set_cookies(response: Response, session: SessionView) -> None:
    s = get_settings()
    common = dict(httponly=True, samesite="lax", secure=s.cookie_secure)
    response.set_cookie(ACCESS_COOKIE, session.access_token, max_age=s.access_token_minutes * 60, path="/", **common)
    response.set_cookie(REFRESH_COOKIE, session.refresh_token, max_age=s.refresh_token_days * 86400, path="/api/auth", **common)


def _clear_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")


# ------------------------------------------------------------------ sessions


@router.post("/auth/login", response_model=MeOut, tags=["auth"])
def login(body: LoginIn, request: Request, response: Response, handle: LoginHandler = Depends(deps.login)):
    session = handle(Login(body.org_code, body.username, body.password, client_ip(request)))
    _set_cookies(response, session)
    return me_out(session.me)


@router.post("/auth/refresh", status_code=204, tags=["auth"])
def refresh(request: Request, response: Response, handle: RefreshSessionHandler = Depends(deps.refresh_session)):
    _set_cookies(response, handle(RefreshSession(request.cookies.get(REFRESH_COOKIE, ""))))
    response.status_code = 204
    return response


@router.post("/auth/logout", status_code=204, tags=["auth"])
def logout(request: Request, response: Response, handle: LogoutHandler = Depends(deps.logout)):
    handle(Logout(request.cookies.get(REFRESH_COOKIE)))
    _clear_cookies(response)
    response.status_code = 204
    return response


@router.get("/auth/me", response_model=MeOut, tags=["auth"])
def me(actor: Actor = Depends(current_actor), handle: GetMeHandler = Depends(deps.get_me)):
    """Also answered while a password change is pending (the web redirects to the change form)."""
    return me_out(handle(actor))


@router.post("/auth/switch-org", response_model=MeOut, tags=["auth"])
def switch_org(body: SwitchOrgIn, request: Request, response: Response, actor: Actor = Depends(current_actor),
               handle: SwitchOrgHandler = Depends(deps.switch_org)):
    session = handle(actor, SwitchOrg(body.org_id, request.cookies.get(REFRESH_COOKIE)))
    _set_cookies(response, session)
    return me_out(session.me)


@router.post("/auth/change-password", status_code=204, tags=["auth"])
def change_password(body: ChangePasswordIn, response: Response, actor: Actor = Depends(current_actor),
                    handle: ChangePasswordHandler = Depends(deps.change_password)):
    handle(actor, ChangePassword(body.current_password, body.new_password))
    response.status_code = 204
    return response


@router.get("/me/orgs", response_model=list[MyOrgOut], tags=["me"])
def my_orgs(actor: Actor = Depends(current_actor), handle: MyOrgsHandler = Depends(deps.my_orgs)):
    """Organisations the header selector offers (all active ones for super admin)."""
    return [MyOrgOut(id=o.id, code=o.code, name=o.name, role=o.role, is_home=o.is_home) for o in handle(actor)]


# ------------------------------------------------------------------ users of the org


@router.post("/users/search", response_model=PageOut[UserOut], tags=["users"])
def search_users(body: UserSearchBody, actor: Actor = Depends(staff_actor), handle: SearchUsersHandler = Depends(deps.search_users)):
    """Filters: username, full_name, email (text) · role (enum) · is_active, must_change_password (bool) · created_at, last_login_at (date).
    `class_id` keeps the members of one class; teachers see students only."""
    return _page(handle(actor, SearchUsers(body.to_request(), body.class_id)), user_out)


@router.post("/users", response_model=UserCreated, status_code=201, tags=["users"])
def create_user(body: UserCreate, actor: Actor = Depends(staff_actor), handle: CreateUserHandler = Depends(deps.create_user)):
    r = handle(actor, CreateUser(body.full_name, body.role, body.username, body.email, body.password))
    return UserCreated(user=user_out(r.user), temp_password=r.temp_password)


@router.post("/users/link", response_model=UserOut, status_code=201, tags=["users"])
def link_account(body: LinkIn, actor: Actor = Depends(staff_actor), handle: LinkAccountHandler = Depends(deps.link_account)):
    """Add an existing account from another organisation (A-10)."""
    return user_out(handle(actor, LinkAccount(body.org_code, body.username, body.role)))


@router.delete("/users/{user_id}/membership", status_code=204, tags=["users"])
def unlink_account(user_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: UnlinkAccountHandler = Depends(deps.unlink_account)):
    handle(actor, UnlinkAccount(user_id))
    return Response(status_code=204)


@router.post("/users/import/preview", tags=["users"])
async def import_preview(file: UploadFile = File(...), actor: Actor = Depends(staff_actor),
                         handle: PreviewImportHandler = Depends(deps.preview_import)):
    p = handle(actor, PreviewImport(file.filename or "", await file.read()))
    return {"rows": p.rows, "valid_count": p.valid_count, "error_count": p.error_count}


@router.post("/users/import/commit", status_code=201, tags=["users"])
def import_commit(body: ImportRowsIn, actor: Actor = Depends(staff_actor), handle: CommitImportHandler = Depends(deps.commit_import)):
    return {"created": handle(actor, CommitImport(body.rows))}


@router.get("/users/{user_id}", response_model=UserOut, tags=["users"])
def get_user(user_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: GetUserHandler = Depends(deps.get_user)):
    return user_out(handle(actor, GetUser(user_id)))


@router.patch("/users/{user_id}", response_model=UserOut, tags=["users"])
def update_user(user_id: uuid.UUID, body: UserUpdate, actor: Actor = Depends(staff_actor), handle: UpdateUserHandler = Depends(deps.update_user)):
    return user_out(handle(actor, UpdateUser(user_id, body.full_name, body.email, body.role, body.is_active)))


@router.post("/users/{user_id}/reset-password", response_model=Credential, tags=["users"])
def reset_password(user_id: uuid.UUID, actor: Actor = Depends(staff_actor), handle: ResetPasswordHandler = Depends(deps.reset_password)):
    c = handle(actor, ResetPassword(user_id))
    return Credential(user_id=c.user_id, username=c.username, full_name=c.full_name, temp_password=c.temp_password)


# ------------------------------------------------------------------ platform admin: organisations


@router.post("/admin/orgs/search", response_model=PageOut[OrgOut], tags=["admin"])
def search_orgs(body: OrgSearchBody, actor: Actor = Depends(super_actor), handle: SearchOrgsHandler = Depends(deps.search_orgs)):
    """Filters: code, name (text) · status (enum) · created_at (date); `include_deleted` also lists deleted orgs."""
    return _page(handle(actor, SearchOrgs(body.to_request(), body.include_deleted)), org_out)


@router.post("/admin/orgs", response_model=OrgCreated, status_code=201, tags=["admin"])
def create_org(body: OrgCreate, actor: Actor = Depends(super_actor), handle: CreateOrgHandler = Depends(deps.create_org)):
    r = handle(actor, CreateOrg(body.code, body.name, body.admin_username, body.admin_full_name))
    return OrgCreated(org=org_out(r.org), admin=AdminCredential(username=r.admin_username, temp_password=r.temp_password))


@router.get("/admin/orgs/{org_id}", response_model=OrgOut, tags=["admin"])
def get_org(org_id: uuid.UUID, actor: Actor = Depends(super_actor), handle: GetOrgHandler = Depends(deps.get_org)):
    return org_out(handle(actor, GetOrg(org_id)))


@router.patch("/admin/orgs/{org_id}", response_model=OrgOut, tags=["admin"])
def update_org(org_id: uuid.UUID, body: OrgUpdate, actor: Actor = Depends(super_actor), handle: UpdateOrgHandler = Depends(deps.update_org)):
    return org_out(handle(actor, UpdateOrg(org_id, body.code, body.name)))


@router.post("/admin/orgs/{org_id}/suspend", response_model=OrgOut, tags=["admin"])
def suspend_org(org_id: uuid.UUID, actor: Actor = Depends(super_actor), handle: ChangeOrgStatusHandler = Depends(deps.change_org_status)):
    return org_out(handle(actor, ChangeOrgStatus(org_id, "suspended")))


@router.post("/admin/orgs/{org_id}/activate", response_model=OrgOut, tags=["admin"])
def activate_org(org_id: uuid.UUID, actor: Actor = Depends(super_actor), handle: ChangeOrgStatusHandler = Depends(deps.change_org_status)):
    return org_out(handle(actor, ChangeOrgStatus(org_id, "active")))


@router.delete("/admin/orgs/{org_id}", status_code=204, tags=["admin"])
def delete_org(org_id: uuid.UUID, hard: bool = False, actor: Actor = Depends(super_actor), handle: DeleteOrgHandler = Depends(deps.delete_org)):
    handle(actor, DeleteOrg(org_id, hard))
    return Response(status_code=204)


# ------------------------------------------------------------------ platform admin: memberships from both sides


@router.post("/admin/orgs/{org_id}/members/search", response_model=PageOut[MembershipOut], tags=["admin"])
def search_org_members(org_id: uuid.UUID, body: SearchBody, actor: Actor = Depends(super_actor),
                       handle: SearchOrgMembersHandler = Depends(deps.search_org_members)):
    """Org → users (school-years AC-13). Filters: username, full_name (text) · role (enum) · is_active (bool)."""
    return _page(handle(actor, SearchOrgMembers(org_id, body.to_request())), membership_out)


@router.post("/admin/orgs/{org_id}/members", response_model=MembershipOut, status_code=201, tags=["admin"])
def add_org_member(org_id: uuid.UUID, body: MemberIn, actor: Actor = Depends(super_actor),
                   handle: AddMembershipHandler = Depends(deps.add_membership)):
    return membership_out(handle(actor, AddMembership(org_id, body.role, org_code=body.org_code, username=body.username)))


@router.patch("/admin/orgs/{org_id}/members/{user_id}", response_model=MembershipOut, tags=["admin"])
def update_org_member(org_id: uuid.UUID, user_id: uuid.UUID, body: MembershipPatch, actor: Actor = Depends(super_actor),
                      handle: UpdateMembershipHandler = Depends(deps.update_membership)):
    return membership_out(handle(actor, UpdateMembership(org_id, user_id, body.role, body.is_active, side="org")))


@router.delete("/admin/orgs/{org_id}/members/{user_id}", status_code=204, tags=["admin"])
def remove_org_member(org_id: uuid.UUID, user_id: uuid.UUID, actor: Actor = Depends(super_actor),
                      handle: RemoveMembershipHandler = Depends(deps.remove_membership)):
    handle(actor, RemoveMembership(org_id, user_id, side="org"))
    return Response(status_code=204)


@router.post("/admin/users/search", response_model=PageOut[AccountOut], tags=["admin"])
def search_accounts(body: SearchBody, actor: Actor = Depends(super_actor), handle: SearchAccountsHandler = Depends(deps.search_accounts)):
    """Every account of every org (school-years AC-14). Filters: username, full_name, home_org_code (text) · is_active (bool);
    sort also by org_count."""
    return _page(handle(actor, SearchAccounts(body.to_request())), account_out)


@router.post("/admin/users/{user_id}/memberships/search", response_model=PageOut[MembershipOut], tags=["admin"])
def search_user_memberships(user_id: uuid.UUID, body: SearchBody, actor: Actor = Depends(super_actor),
                            handle: SearchUserMembershipsHandler = Depends(deps.search_user_memberships)):
    """User → orgs, home org first. Filters: org_code, org_name (text) · role (enum)."""
    return _page(handle(actor, SearchUserMemberships(user_id, body.to_request())), membership_out)


@router.post("/admin/users/{user_id}/memberships", response_model=MembershipOut, status_code=201, tags=["admin"])
def add_user_membership(user_id: uuid.UUID, body: MembershipIn, actor: Actor = Depends(super_actor),
                        handle: AddMembershipHandler = Depends(deps.add_membership)):
    return membership_out(handle(actor, AddMembership(body.org_id, body.role, user_id=user_id)))


@router.patch("/admin/users/{user_id}/memberships/{org_id}", response_model=MembershipOut, tags=["admin"])
def update_user_membership(user_id: uuid.UUID, org_id: uuid.UUID, body: MembershipPatch, actor: Actor = Depends(super_actor),
                           handle: UpdateMembershipHandler = Depends(deps.update_membership)):
    return membership_out(handle(actor, UpdateMembership(org_id, user_id, body.role, body.is_active, side="user")))


@router.delete("/admin/users/{user_id}/memberships/{org_id}", status_code=204, tags=["admin"])
def remove_user_membership(user_id: uuid.UUID, org_id: uuid.UUID, actor: Actor = Depends(super_actor),
                           handle: RemoveMembershipHandler = Depends(deps.remove_membership)):
    handle(actor, RemoveMembership(org_id, user_id, side="user"))
    return Response(status_code=204)
