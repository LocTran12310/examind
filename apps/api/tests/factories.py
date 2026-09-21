from app.core.security import hash_password
from app.models import Organization, User

PASSWORD = "Secret123!"


def make_org(db, code="trungtama", name="Trung tâm A", **kw) -> Organization:
    org = Organization(code=code, name=name, **kw)
    db.add(org)
    db.flush()
    return org


def make_user(db, org, username="hs01", role="student", password=PASSWORD, **kw) -> User:
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        full_name=kw.pop("full_name", username.upper()),
        role=role,
        **kw,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def login_as(client, db, role="super_admin", org=None, username=None):
    """Create (if needed) and log in a user; returns the user."""
    from sqlalchemy import select

    from app.models.org import SYSTEM_ORG_CODE

    if role == "super_admin":
        org = db.scalar(select(Organization).where(Organization.code == SYSTEM_ORG_CODE))
        username = username or "root"
    org = org or make_org(db)
    user = make_user(db, org, username or f"{role}1", role=role)
    db.commit()
    r = client.post("/api/auth/login", json={"org_code": org.code, "username": user.username, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return user
