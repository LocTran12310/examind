from tests.factories import login_as, make_org, make_user


def test_class_crud_and_members(client, db):
    admin = login_as(client, db, "org_admin")
    a, b = make_user(db, admin.organization, "hs01"), make_user(db, admin.organization, "hs02")
    db.commit()
    r = client.post("/api/classes", json={"name": "10A1", "grade": 10, "school_year": "2026-2027"})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    assert client.post("/api/classes", json={"name": "10A1", "school_year": "2026-2027"}).status_code == 409
    assert client.post("/api/classes", json={"name": "10A2", "school_year": "2026-2028"}).status_code == 422
    assert client.post(f"/api/classes/{cid}/members", json={"user_ids": [str(a.id), str(b.id)]}).status_code == 204
    assert client.post(f"/api/classes/{cid}/members", json={"user_ids": [str(a.id)]}).status_code == 204  # idempotent
    detail = client.get(f"/api/classes/{cid}").json()
    assert detail["member_count"] == 2 and {m["username"] for m in detail["members"]} == {"hs01", "hs02"}
    assert client.delete(f"/api/classes/{cid}/members/{a.id}").status_code == 204
    assert client.get("/api/classes").json()["items"][0]["member_count"] == 1
    # a student can be in several classes
    c2 = client.post("/api/classes", json={"name": "Toán nâng cao", "school_year": "2026-2027"}).json()["id"]
    client.post(f"/api/classes/{c2}/members", json={"user_ids": [str(b.id)]})
    user = client.get(f"/api/users/{b.id}").json()
    assert len(user["class_ids"]) == 2
    assert client.get("/api/users", params={"class_id": c2}).json()["total"] == 1
    assert client.patch(f"/api/classes/{cid}", json={"name": "10A1-CLC"}).json()["name"] == "10A1-CLC"
    assert client.delete(f"/api/classes/{cid}").status_code == 204


def test_class_isolation(client, db):
    login_as(client, db, "teacher")
    other = make_org(db, "orgb")
    stranger = make_user(db, other, "hsb")
    db.commit()
    mine = client.post("/api/classes", json={"name": "11B"}).json()["id"]
    assert client.post(f"/api/classes/{mine}/members", json={"user_ids": [str(stranger.id)]}).status_code == 404
    from app.models import SchoolClass

    theirs = SchoolClass(organization_id=other.id, name="X", school_year="2026-2027")
    db.add(theirs)
    db.commit()
    assert client.get(f"/api/classes/{theirs.id}").status_code == 404
    assert client.delete(f"/api/classes/{theirs.id}").status_code == 404
    assert [c["name"] for c in client.get("/api/classes").json()["items"]] == ["11B"]
