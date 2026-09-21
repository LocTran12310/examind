from datetime import timedelta

import pytest

from app.core.errors import AppError
from app.core.security import decode_access_token, now
from app.services import auth
from tests.factories import PASSWORD, make_org, make_user


def _code(fn):
    with pytest.raises(AppError) as e:
        fn()
    return e.value.code, e.value.status


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
