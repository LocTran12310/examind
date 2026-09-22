"""History panel data = the audit log (school-years ADR-05, AC-16)."""
import uuid

from app.shared.infrastructure.sql_audit import SqlAuditTrail
from tests.factories import login_as, make_org, make_user


def test_org_admin_sees_only_their_org_and_related_entries(client, db):
    admin = login_as(client, db, "org_admin")
    k = client.post("/api/classes", json={"name": "10A1"}).json()
    s = make_user(db, admin.organization, "hs01")
    other = make_org(db, "ttz")
    db.commit()
    client.post(f"/api/classes/{k['id']}/members", json={"user_ids": [str(s.id)]})
    # an entry in another org must not leak
    SqlAuditTrail(db).record(None, other.id, "class.create", "class", uuid.UUID(k["id"]), name="x")
    db.commit()
    rows = client.post("/api/audit/search", json={"target_id": k["id"]}).json()["data"]
    assert {r["organization_code"] for r in rows} == {"trungtama"}
    assert rows[0]["action"] == "class.members_add" and rows[0]["actor_name"] == admin.full_name
    related = client.post("/api/audit/search", json={"related": str(s.id)}).json()["data"]
    assert [r["action"] for r in related] == ["class.members_add"]


def test_super_admin_reads_every_org(client, db):
    org = make_org(db, "tty")
    SqlAuditTrail(db).record(None, org.id, "member.link", "user", None)
    db.commit()
    login_as(client, db)
    assert "tty" in {r["organization_code"] for r in client.post("/api/audit/search", json={}).json()["data"]}
