"""Sessions through the identity handlers on a real database (login, refresh rotation, logout, revocation, password)."""
from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.modules.identity.application.commands.change_password import ChangePassword, ChangePasswordHandler
from app.modules.identity.application.commands.login import Login, LoginHandler
from app.modules.identity.application.commands.logout import Logout, LogoutHandler
from app.modules.identity.application.commands.refresh_session import RefreshSession, RefreshSessionHandler
from app.modules.identity.domain.entities import User
from app.modules.identity.infrastructure.adapters.passwords import Argon2PasswordHasher
from app.modules.identity.infrastructure.adapters.tokens import TokenSecrets, decode_access_token
from app.modules.identity.infrastructure.repositories import SqlOrganizationRepository, SqlRefreshTokenRepository, SqlUserRepository
from app.modules.identity.interface import deps
from app.shared.application.actor import Actor
from app.shared.domain.clock import utcnow as now
from app.shared.domain.errors import DomainError
from app.shared.infrastructure.sql_unit_of_work import SqlUnitOfWork
from app.shared.interface.errors import status_of
from tests.factories import PASSWORD, make_org, make_user


class _NoThrottle:
    def hit(self, key: str) -> bool:
        return True


def _session(db, s):
    return SimpleNamespace(user=db.get(User, s.me.id), access_token=s.access_token, refresh_token=s.refresh_token)


class auth:  # noqa: N801  (reads like the calls it replaces)
    @staticmethod
    def login(db, org_code, username, password):
        handle = LoginHandler(SqlOrganizationRepository(db), SqlUserRepository(db), Argon2PasswordHasher(), deps._issuer(db), _NoThrottle(),
                              deps._policy(), SqlUnitOfWork(db))
        return _session(db, handle(Login(org_code, username, password)))

    @staticmethod
    def refresh(db, raw_token):
        handle = RefreshSessionHandler(SqlRefreshTokenRepository(db), SqlUserRepository(db), SqlOrganizationRepository(db), TokenSecrets(),
                                       deps._issuer(db), SqlUnitOfWork(db))
        return _session(db, handle(RefreshSession(raw_token)))

    @staticmethod
    def logout(db, raw_token):
        LogoutHandler(deps._issuer(db), SqlUnitOfWork(db))(Logout(raw_token))

    @staticmethod
    def revoke_org_tokens(db, org_id):
        SqlRefreshTokenRepository(db).revoke_org(org_id, now())

    @staticmethod
    def change_password(db, user, current_password, new_password):
        actor = Actor(user_id=user.id, org_id=user.organization_id, role=user.role, is_super=user.is_super)
        ChangePasswordHandler(SqlUserRepository(db), Argon2PasswordHasher(), SqlUnitOfWork(db))(actor, ChangePassword(current_password, new_password))


def _code(fn):
    with pytest.raises(DomainError) as e:
        fn()
    return e.value.code, status_of(e.value)


def test_login_is_case_insensitive(db):
    org = make_org(db)
    make_user(db, org)
    s = auth.login(db, "TrungtamA", "HS01", PASSWORD)
    claims = decode_access_token(s.access_token)
    assert claims["org_code"] == "trungtama" and claims["role"] == "student"
    assert s.refresh_token


def test_same_username_in_two_orgs(db):
    a, b = make_org(db, "orga"), make_org(db, "orgb")
    make_user(db, a, "hs01", password="PassA1234")
    make_user(db, b, "hs01", password="PassB1234")
    assert auth.login(db, "orgb", "hs01", "PassB1234").user.organization_id == b.id
    assert _code(lambda: auth.login(db, "orga", "hs01", "PassB1234")) == ("invalid_credentials", 401)


@pytest.mark.parametrize("org,user,pw", [("nope", "hs01", PASSWORD), ("trungtama", "nobody", PASSWORD), ("trungtama", "hs01", "wrong")])
def test_generic_failure(db, org, user, pw):
    o = make_org(db)
    make_user(db, o)
    assert _code(lambda: auth.login(db, org, user, pw)) == ("invalid_credentials", 401)


def test_inactive_user_is_generic_failure(db):
    o = make_org(db)
    make_user(db, o, is_active=False)
    assert _code(lambda: auth.login(db, "trungtama", "hs01", PASSWORD)) == ("invalid_credentials", 401)


def test_suspended_and_deleted_org(db):
    o = make_org(db, status="suspended")
    make_user(db, o)
    assert _code(lambda: auth.login(db, "trungtama", "hs01", PASSWORD)) == ("org_suspended", 403)
    o.status, o.deleted_at = "active", now()
    db.flush()
    assert _code(lambda: auth.login(db, "trungtama", "hs01", PASSWORD)) == ("org_suspended", 403)


def test_lockout_after_five_failures(db):
    o = make_org(db)
    u = make_user(db, o)
    for _ in range(5):
        _code(lambda: auth.login(db, "trungtama", "hs01", "bad"))
    assert _code(lambda: auth.login(db, "trungtama", "hs01", PASSWORD)) == ("locked", 429)
    u.locked_until = now() - timedelta(seconds=1)
    db.flush()
    assert auth.login(db, "trungtama", "hs01", PASSWORD).user.id == u.id


def test_refresh_rotates_and_detects_reuse(db):
    o = make_org(db)
    make_user(db, o)
    first = auth.login(db, "trungtama", "hs01", PASSWORD)
    db.commit()
    second = auth.refresh(db, first.refresh_token)
    db.commit()
    assert second.refresh_token != first.refresh_token
    # replaying the rotated token revokes everything
    assert _code(lambda: auth.refresh(db, first.refresh_token)) == ("unauthenticated", 401)
    assert _code(lambda: auth.refresh(db, second.refresh_token)) == ("unauthenticated", 401)


def test_logout_and_org_suspend_revoke(db):
    o = make_org(db)
    make_user(db, o)
    s1 = auth.login(db, "trungtama", "hs01", PASSWORD)
    s2 = auth.login(db, "trungtama", "hs01", PASSWORD)
    db.commit()
    auth.logout(db, s1.refresh_token)
    db.commit()
    assert _code(lambda: auth.refresh(db, s1.refresh_token))[0] == "unauthenticated"
    auth.revoke_org_tokens(db, o.id)
    db.commit()
    assert _code(lambda: auth.refresh(db, s2.refresh_token))[0] == "unauthenticated"


def test_change_password(db):
    o = make_org(db)
    u = make_user(db, o, must_change_password=True)
    assert _code(lambda: auth.change_password(db, u, "wrong", "NewPass123"))[0] == "validation_error"
    assert _code(lambda: auth.change_password(db, u, PASSWORD, "short"))[0] == "validation_error"
    assert _code(lambda: auth.change_password(db, u, PASSWORD, PASSWORD))[0] == "validation_error"
    auth.change_password(db, u, PASSWORD, "NewPass123")
    assert u.must_change_password is False
    assert auth.login(db, "trungtama", "hs01", "NewPass123")
