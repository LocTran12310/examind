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
