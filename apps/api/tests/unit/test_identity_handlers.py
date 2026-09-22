"""Identity handlers against in-memory ports: sessions, accounts, import, memberships, organisations (ADR-02)."""
from datetime import UTC, datetime, timedelta
import uuid

import pytest

from app.modules.identity.application.commands.add_membership import AddMembership, AddMembershipHandler
from app.modules.identity.application.commands.change_password import ChangePassword, ChangePasswordHandler
from app.modules.identity.application.commands.create_org import CreateOrg, CreateOrgHandler
from app.modules.identity.application.commands.create_user import CreateUser, CreateUserHandler
from app.modules.identity.application.commands.delete_org import DeleteOrg, DeleteOrgHandler
from app.modules.identity.application.commands.import_users import CommitImport, CommitImportHandler
from app.modules.identity.application.commands.login import Login, LoginHandler
from app.modules.identity.application.commands.refresh_session import RefreshSession, RefreshSessionHandler
from app.modules.identity.application.commands.remove_membership import RemoveMembership, RemoveMembershipHandler
from app.modules.identity.application.commands.switch_org import SwitchOrg, SwitchOrgHandler
from app.modules.identity.application.commands.update_user import UpdateUser, UpdateUserHandler
from app.modules.identity.application.common import SessionIssuer
from app.modules.identity.application.ports import AuthPolicy
from app.modules.identity.application.queries.resolve_principal import ResolvePrincipal, ResolvePrincipalHandler
from app.modules.identity.domain.entities import Membership, Organization, User
from app.shared.application.actor import Actor
from app.shared.domain.errors import Conflict, DomainError, Forbidden, Invalid, Throttled, Unauthenticated
from tests.unit.fakes import FakeAudit, FakeUow

NOW = datetime(2026, 9, 22, 8, 0, tzinfo=UTC)
POLICY = AuthPolicy(refresh_token_days=30, login_max_failures=5, login_lock_minutes=15)


def clock():
    return NOW


class FakeOrgs:
    def __init__(self):
        self.rows: dict = {}

    def get(self, org_id):
        return self.rows.get(org_id)

    def by_code(self, code):
        return next((o for o in self.rows.values() if o.code == code.lower()), None)

    def code_taken(self, code, exclude_id=None):
        return any(o.code == code and o.id != exclude_id for o in self.rows.values())

    def active(self):
        return sorted((o for o in self.rows.values() if o.deleted_at is None), key=lambda o: (not o.is_system, o.name))

    def add(self, org):
        self.rows[org.id] = org

    def purge(self, org):
        del self.rows[org.id]


class FakeMembers:
    def __init__(self, orgs):
        self.orgs, self.rows = orgs, {}

    def get(self, user_id, org_id):
        return self.rows.get((user_id, org_id))

    def of_user(self, user_id):
        out = [(self.orgs.get(o), m.role) for (u, o), m in self.rows.items() if u == user_id and m.is_active]
        return sorted(((o, r) for o, r in out if o.deleted_at is None), key=lambda x: x[0].name)

    def roles(self, org_id, user_ids):
        return {u: m.role for (u, o), m in self.rows.items() if o == org_id and u in user_ids and m.is_active}

    def add(self, m):
        self.rows[(m.user_id, m.organization_id)] = m

    def remove(self, m):
        del self.rows[(m.user_id, m.organization_id)]


class FakeUsers:
    def __init__(self, members):
        self.members, self.rows = members, {}

    def get(self, user_id):
        return self.rows.get(user_id)

    def by_username(self, org_id, username):
        return next((u for u in self.rows.values() if u.organization_id == org_id and u.username.lower() == username.lower()), None)

    def taken_usernames(self, org_id, usernames):
        return {u.username for u in self.rows.values() if u.organization_id == org_id and u.username in usernames}

    def usernames_like(self, org_id, prefix):
        return {u.username for u in self.rows.values() if u.organization_id == org_id and u.username.startswith(prefix)}

    def non_admin_count(self, org_id):
        return sum(1 for u in self.rows.values() if u.organization_id == org_id and u.role != "org_admin")

    def add(self, user):
        self.rows[user.id] = user
        self.members.add(Membership(user.id, user.organization_id, user.role))  # the home membership comes with the account


class FakeTokens:
    def __init__(self):
        self.rows: dict = {}

    def by_hash(self, token_hash):
        return self.rows.get(token_hash)

    def add(self, token):
        self.rows[token.token_hash] = token

    def revoke(self, token_hash, at):
        t = self.rows.get(token_hash)
        if t is not None and t.revoked_at is None:
            t.revoked_at = at

    def revoke_user(self, user_id, at):
        for t in self.rows.values():
            if t.user_id == user_id and t.revoked_at is None:
                t.revoked_at = at

    def revoke_org(self, org_id, at):
        raise NotImplementedError


class PlainHasher:
    def hash(self, password):
        return "h:" + password

    def verify(self, password, password_hash):
        return password_hash is not None and password_hash == "h:" + password


class CountingSecrets:
    def __init__(self):
        self.n = 0

    def temp_password(self):
        return "Temp234567"

    def refresh_token(self):
        self.n += 1
        return f"raw{self.n}", f"d:raw{self.n}"

    def digest(self, raw):
        return "d:" + raw


class FakeAccess:
    def issue(self, user_id, org_id, org_code, role):
        return f"{user_id}|{org_code}|{role}"


class Throttle:
    def __init__(self, allow=True):
        self.allow = allow

    def hit(self, key):
        return self.allow


class FakeClasses:
    def __init__(self):
        self.created, self.enrolled, self.left = {}, [], []

    def find_or_create(self, actor, name):
        return self.created.setdefault(name, uuid.uuid4())

    def enroll(self, actor, class_id, user_ids):
        self.enrolled += [(class_id, u) for u in user_ids]

    def leave_org_classes(self, org_id, user_id):
        self.left.append((org_id, user_id))


class FakeSeeder:
    def __init__(self):
        self.seeded = []

    def seed_reference(self, org_id):
        self.seeded.append(("reference", org_id))

    def seed_demo(self, org_id):
        self.seeded.append(("demo", org_id))


class FakeUserReader:
    def class_ids(self, org_id, user_ids):
        return {}


class World:
    def __init__(self):
        self.orgs = FakeOrgs()
        self.members = FakeMembers(self.orgs)
        self.users = FakeUsers(self.members)
        self.tokens, self.secrets, self.audit, self.uow = FakeTokens(), CountingSecrets(), FakeAudit(), FakeUow()
        self.issuer = SessionIssuer(self.orgs, self.members, self.tokens, self.secrets, FakeAccess(), POLICY, clock)

    def org(self, code, name=None, **kw):
        o = Organization(code=code, name=name or code.upper(), **kw)
        self.orgs.add(o)
        return o

    def user(self, org, username, role="student", password="Secret123!", **kw):
        u = User(organization_id=org.id, username=username, password_hash="h:" + password, full_name=username.upper(), role=role, **kw)
        self.users.add(u)
        return u

    def login(self, throttle=True):
        return LoginHandler(self.orgs, self.users, PlainHasher(), self.issuer, Throttle(throttle), POLICY, self.uow, clock)


def actor(user, org, role=None):
    return Actor(user_id=user.id, org_id=org.id, role=role or user.role, is_super=user.role == "super_admin")


# ------------------------------------------------------------------ sessions


def test_login_opens_home_org_and_every_failure_looks_the_same():
    w = World()
    a = w.org("tta")
    w.user(a, "hs01")
    s = w.login()(Login("TTA", " hs01 ", "Secret123!"))
    assert (s.me.org.code, s.me.role, s.refresh_token) == ("tta", "student", "raw1") and s.access_token.endswith("|tta|student")
    errs = []
    for code, username, pw in (("nope", "hs01", "Secret123!"), ("tta", "x", "Secret123!"), ("tta", "hs01", "bad")):
        with pytest.raises(Unauthenticated) as e:
            w.login()(Login(code, username, pw))
        errs.append((e.value.code, e.value.message, e.value.fields))
    assert len(set(map(repr, errs))) == 1 and errs[0][0] == "invalid_credentials"


def test_lockout_after_max_failures_and_ip_throttle():
    w = World()
    u = w.user(w.org("tta"), "hs01")
    for _ in range(5):
        with pytest.raises(Unauthenticated):
            w.login()(Login("tta", "hs01", "bad"))
    assert u.failed_logins == 5 and u.locked_until == NOW + timedelta(minutes=15) and w.uow.commits == 5
    with pytest.raises(Throttled) as e:
        w.login()(Login("tta", "hs01", "Secret123!"))
    assert e.value.code == "locked" and "16 phút" in e.value.message  # rounded up, as before
    with pytest.raises(Throttled) as e:
        w.login(throttle=False)(Login("tta", "hs01", "Secret123!"))
    assert e.value.message == "Quá nhiều lần đăng nhập, thử lại sau 1 phút"


def test_suspended_org_refuses_a_right_password():
    w = World()
    w.user(w.org("tta", status="suspended"), "hs01")
    with pytest.raises(Forbidden) as e:
        w.login()(Login("tta", "hs01", "Secret123!"))
    assert (e.value.code, e.value.message) == ("org_suspended", "Tổ chức đang bị khóa")


def test_refresh_rotates_and_a_replayed_token_ends_every_session():
    w = World()
    w.user(w.org("tta"), "hs01")
    first = w.login()(Login("tta", "hs01", "Secret123!"))
    refresh = RefreshSessionHandler(w.tokens, w.users, w.orgs, w.secrets, w.issuer, w.uow, clock)
    second = refresh(RefreshSession(first.refresh_token))
    assert second.refresh_token != first.refresh_token
    with pytest.raises(Unauthenticated):
        refresh(RefreshSession(first.refresh_token))
    with pytest.raises(Unauthenticated) as e:
        refresh(RefreshSession(second.refresh_token))
    assert e.value.message == "Phiên đăng nhập đã hết hạn"


def test_switch_org_needs_a_membership_and_rotates_the_refresh_token():
    w = World()
    a, b, c = w.org("tta"), w.org("ttb"), w.org("ttc")
    lan = w.user(b, "gvlan", role="teacher")
    w.members.add(Membership(lan.id, a.id, "org_admin"))
    s = w.login()(Login("ttb", "gvlan", "Secret123!"))
    switch = SwitchOrgHandler(w.users, w.orgs, w.members, w.issuer, w.audit, w.uow)
    with pytest.raises(Forbidden):
        switch(actor(lan, b), SwitchOrg(c.id, s.refresh_token))
    moved = switch(actor(lan, b), SwitchOrg(a.id, s.refresh_token))
    assert (moved.me.org.code, moved.me.role, moved.me.home_org.code) == ("tta", "org_admin", "ttb")
    assert lan.last_org_id == a.id and w.tokens.by_hash("d:" + s.refresh_token).revoked_at == NOW
    assert w.audit.actions() == ["org.switch"]
    # the next login opens the last org
    assert w.login()(Login("ttb", "gvlan", "Secret123!")).me.org.code == "tta"


def test_principal_is_refused_when_the_membership_is_disabled():
    w = World()
    a, b = w.org("tta"), w.org("ttb")
    lan = w.user(b, "gvlan", role="teacher")
    w.members.add(Membership(lan.id, a.id, "teacher"))
    resolve = ResolvePrincipalHandler(w.users, w.orgs, w.members)
    assert resolve(ResolvePrincipal(lan.id, a.id)).role == "teacher"
    w.members.get(lan.id, a.id).is_active = False
    with pytest.raises(Unauthenticated):
        resolve(ResolvePrincipal(lan.id, a.id))
    assert resolve(ResolvePrincipal(lan.id)).org_id == b.id


def test_super_admin_works_in_any_org_as_org_admin():
    w = World()
    system, a = w.org("system", is_system=True), w.org("tta")
    root = w.user(system, "root", role="super_admin")
    resolve = ResolvePrincipalHandler(w.users, w.orgs, w.members)
    assert (resolve(ResolvePrincipal(root.id, a.id)).role, resolve(ResolvePrincipal(root.id)).role) == ("org_admin", "super_admin")


def test_change_password_rules():
    w = World()
    a = w.org("tta")
    u = w.user(a, "hs01", must_change_password=True)
    change = ChangePasswordHandler(w.users, PlainHasher(), w.uow)
    for current, new, field in (("wrong", "NewPass123", "current_password"), ("Secret123!", "short", "new_password"),
                                ("Secret123!", "Secret123!", "new_password")):
        with pytest.raises(Invalid) as e:
            change(actor(u, a), ChangePassword(current, new))
        assert field in e.value.fields
    change(actor(u, a), ChangePassword("Secret123!", "NewPass123"))
    assert u.password_hash == "h:NewPass123" and u.must_change_password is False


# ------------------------------------------------------------------ accounts of the org


def test_create_user_generates_usernames_and_a_temp_password():
    w = World()
    a = w.org("tta")
    admin = w.user(a, "admin", role="org_admin")
    create = CreateUserHandler(w.users, w.orgs, PlainHasher(), w.secrets, w.audit, w.uow)
    first = create(actor(admin, a), CreateUser("Lê An"))
    second = create(actor(admin, a), CreateUser("Lê An"))
    assert (first.user.username, second.user.username, first.temp_password) == ("lean", "lean2", "Temp234567")
    assert first.user.must_change_password and first.user.home_org_code == "tta"
    with pytest.raises(Conflict):
        create(actor(admin, a), CreateUser("X", username="LEAN"))
    teacher = w.user(a, "gv", role="teacher")
    with pytest.raises(Forbidden):
        create(actor(teacher, a), CreateUser("GV mới", role="teacher"))


def test_update_user_outside_the_home_org_changes_only_role_and_access():
    w = World()
    a, b = w.org("tta"), w.org("ttb")
    admin = w.user(a, "admin", role="org_admin")
    lan = w.user(b, "gvlan", role="teacher")
    w.members.add(Membership(lan.id, a.id, "org_admin"))
    update = UpdateUserHandler(w.users, w.members, w.orgs, w.tokens, FakeUserReader(), w.audit, w.uow, clock)
    with pytest.raises(Forbidden) as e:
        update(actor(admin, a), UpdateUser(lan.id, full_name="X"))
    assert e.value.message == "Thông tin tài khoản do tổ chức gốc quản lý"
    view = update(actor(admin, a), UpdateUser(lan.id, role="teacher", is_active=False))
    assert (view.role, view.is_active, view.is_home) == ("teacher", False, False)
    assert lan.is_active and lan.role == "teacher" and w.members.get(lan.id, a.id).is_active is False
    with pytest.raises(Forbidden):
        update(actor(admin, a), UpdateUser(admin.id, is_active=False))


def test_import_is_all_or_nothing_and_puts_accounts_in_classes():
    w = World()
    a = w.org("tta")
    admin = w.user(a, "admin", role="org_admin")
    classes = FakeClasses()
    commit = CommitImportHandler(w.users, classes, PlainHasher(), w.secrets, w.audit, w.uow)
    with pytest.raises(Invalid) as e:
        commit(actor(admin, a), CommitImport([{"full_name": "Lê An", "role": "hs"}, {"full_name": "", "username": "admin"}]))
    assert e.value.code == "import_invalid" and e.value.fields["rows"][0]["errors"] == ["Thiếu họ tên", "Tên đăng nhập đã tồn tại"]
    assert len(w.users.rows) == 1
    created = commit(actor(admin, a), CommitImport([{"full_name": "Lê An", "class": "10A1"}, {"full_name": "Lê An", "role": "gv"}]))
    assert [(c["username"], c["role"]) for c in created] == [("lean", "student"), ("lean2", "teacher")]
    assert list(classes.created) == ["10A1"] and len(classes.enrolled) == 1
    assert w.audit.entries[-1][0] == "user.import" and w.audit.entries[-1][2] == {"count": 2}


# ------------------------------------------------------------------ memberships and organisations


def test_memberships_keep_the_home_org_and_refuse_duplicates():
    w = World()
    a, b = w.org("tta"), w.org("ttb")
    root = w.user(w.org("system", is_system=True), "root", role="super_admin")
    lan = w.user(a, "lan", role="teacher")
    add = AddMembershipHandler(w.users, w.orgs, w.members, w.audit, w.uow)
    view = add(actor(root, a), AddMembership(b.id, "student", org_code="TTA", username="lan"))
    assert (view.org_code, view.is_home, view.home_org_code) == ("ttb", False, "tta")
    with pytest.raises(Conflict):
        add(actor(root, a), AddMembership(b.id, "teacher", user_id=lan.id))
    classes = FakeClasses()
    remove = RemoveMembershipHandler(w.users, w.orgs, w.members, classes, w.audit, w.uow)
    with pytest.raises(Invalid):
        remove(actor(root, a), RemoveMembership(a.id, lan.id, side="user"))
    remove(actor(root, a), RemoveMembership(b.id, lan.id))
    assert w.members.get(lan.id, b.id) is None and classes.left == [(b.id, lan.id)]
    assert w.audit.actions() == ["member.link", "member.unlink"]


def test_create_and_delete_org():
    w = World()
    root = w.user(w.org("system", is_system=True), "root", role="super_admin")
    seeder = FakeSeeder()
    create = CreateOrgHandler(w.orgs, w.users, seeder, PlainHasher(), w.secrets, w.audit, w.uow)
    with pytest.raises(Invalid) as e:
        create(actor(root, w.orgs.by_code("system")), CreateOrg("trung tam!", "X"))
    assert "code" in e.value.fields
    made = create(actor(root, w.orgs.by_code("system")), CreateOrg("TrungtamA", "Trung tâm A"))
    assert (made.org.code, made.admin_username, made.temp_password) == ("trungtama", "admin", "Temp234567")
    assert [k for k, _ in seeder.seeded] == ["reference", "demo"]
    org = w.orgs.by_code("trungtama")
    w.user(org, "hs01")
    delete = DeleteOrgHandler(w.orgs, w.users, w.tokens, w.audit, w.uow, clock)
    with pytest.raises(Conflict) as e:
        delete(actor(root, org), DeleteOrg(org.id, hard=True))
    assert e.value.code == "org_not_empty"
    with pytest.raises(DomainError) as e:
        delete(actor(root, org), DeleteOrg(w.orgs.by_code("system").id))
    assert e.value.message == "Không thể thay đổi tổ chức hệ thống"
