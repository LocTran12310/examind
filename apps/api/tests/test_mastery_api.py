from tests.exam_helpers import login
from tests.test_mastery import take


def test_mastery_endpoints(client, db):
    admin = take(client, db, right=True)
    s = login(client, "trungtama", "hs01")
    rows = s.get("/api/me/mastery").json()
    tracked = [r for r in rows if r["tracked"]]
    assert tracked and all(r["mastery"] > 0.5 for r in tracked)
    parents = [r for r in rows if not r["tracked"]]
    assert all(p["answers"] >= 1 for p in parents)
    assert client.get("/api/me/mastery").status_code == 403  # staff use the per-student endpoint
    student_id = s.get("/api/auth/me").json()["id"]
    assert client.get(f"/api/students/{student_id}/mastery").json() == rows
    assert s.get(f"/api/students/{student_id}/mastery").status_code == 403
    klass = client.post("/api/classes/search", json={}).json()["data"][0]
    ov = client.get(f"/api/classes/{klass['id']}/overview").json()
    assert ov[0]["username"] == "hs01" and len(ov[0]["weakest"]) >= 1 and ov[0]["review"] is None
