from tests.factories import login_as, make_org


def setup(client, db, role="teacher"):
    user = login_as(client, db, role)
    from app.seed.org_template import seed_org

    seed_org(db, user.organization_id)
    db.commit()
    topics = client.get("/api/topics").json()
    by_name = {t["name"]: t for t in topics}
    return user, by_name


def test_list_has_depth_and_child_count(client, db):
    _, t = setup(client, db)
    assert t["Giải tích"]["depth"] == 1 and t["Giải tích"]["level_kind"] == "strand"
    assert t["Nguyên hàm"]["depth"] == 2 and t["Nguyên hàm"]["child_count"] == 2
    tax = client.get("/api/taxonomy").json()
    assert [g["level"] for g in tax["grades"]] == list(range(6, 13))


def test_add_rename_move_and_back(client, db):
    _, t = setup(client, db)
    r = client.post("/api/topics", json={"name": "Nguyên hàm từng phần", "parent_id": t["Nguyên hàm"]["id"]})
    assert r.status_code == 201, r.text
    new = r.json()
    assert new["depth"] == 3 and new["level_kind"] == "subtopic" and new["path"].startswith(t["Nguyên hàm"]["path"] + ".")
    r = client.patch(f"/api/topics/{new['id']}", json={"name": "Phương pháp từng phần"})
    assert r.json()["name"] == "Phương pháp từng phần"
    r = client.post(f"/api/topics/{new['id']}/move", json={"parent_id": t["Tích phân"]["id"]})
    assert r.status_code == 200 and r.json()["path"].startswith(t["Tích phân"]["path"] + ".")
    r = client.post(f"/api/topics/{new['id']}/move", json={"parent_id": t["Nguyên hàm"]["id"]})
    assert r.json()["parent_id"] == t["Nguyên hàm"]["id"]


def test_move_subtree_rewrites_descendant_paths(client, db):
    _, t = setup(client, db)
    nh = t["Nguyên hàm"]
    r = client.post(f"/api/topics/{nh['id']}/move", json={"parent_id": t["Tích phân"]["id"]})
    assert r.status_code == 200
    after = {x["name"]: x for x in client.get("/api/topics").json()}
    assert after["Nguyên hàm cơ bản"]["path"].startswith(after["Nguyên hàm"]["path"] + ".")
    assert after["Nguyên hàm"]["path"].startswith(t["Tích phân"]["path"] + ".")
    assert after["Nguyên hàm cơ bản"]["depth"] == 4


def test_move_into_own_descendant_refused(client, db):
    _, t = setup(client, db)
    r = client.post(f"/api/topics/{t['Giải tích']['id']}/move", json={"parent_id": t["Nguyên hàm"]["id"]})
    assert r.status_code == 409


def test_delete_guard_and_merge(client, db):
    _, t = setup(client, db)
    r = client.delete(f"/api/topics/{t['Nguyên hàm']['id']}")
    assert r.status_code == 409 and r.json()["code"] == "topic_has_children"
    leaf = client.post("/api/topics", json={"name": "Tạm", "parent_id": t["Tích phân"]["id"]}).json()
    assert client.delete(f"/api/topics/{leaf['id']}").status_code == 204
    r = client.post(f"/api/topics/{t['Nguyên hàm']['id']}/merge", json={"target_id": t["Tích phân"]["id"]})
    assert r.status_code == 200
    after = {x["name"]: x for x in client.get("/api/topics").json()}
    assert "Nguyên hàm" not in after
    assert after["Nguyên hàm cơ bản"]["parent_id"] == t["Tích phân"]["id"]
    assert after["Tích phân"]["child_count"] == 5


def test_depth_limit(client, db):
    _, t = setup(client, db)
    parent = t["Nguyên hàm cơ bản"]["id"]  # depth 3
    d4 = client.post("/api/topics", json={"name": "d4", "parent_id": parent}).json()
    d5 = client.post("/api/topics", json={"name": "d5", "parent_id": d4["id"]}).json()
    assert d5["depth"] == 5
    assert client.post("/api/topics", json={"name": "d6", "parent_id": d5["id"]}).status_code == 422


def test_students_read_only_and_isolation(client, db):
    student, t = setup(client, db, "student")
    assert client.post("/api/topics", json={"name": "x", "parent_id": t["Giải tích"]["id"]}).status_code == 403
    other = make_org(db, "orgb")
    from app.seed.org_template import seed_org

    seed_org(db, other.id)
    db.commit()
    names = [x["name"] for x in client.get("/api/topics").json()]
    assert names.count("Giải tích") == 1
