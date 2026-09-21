from tests.factories import login_as


def test_tag_crud_and_uniqueness(client, db):
    login_as(client, db, "teacher")
    r = client.post("/api/tags", json={"group": "method", "name": "đổi biến"})
    assert r.status_code == 201
    tid = r.json()["id"]
    assert client.post("/api/tags", json={"group": "method", "name": "ĐỔI BIẾN"}).status_code == 409
    assert client.post("/api/tags", json={"group": "skill", "name": "đổi biến"}).status_code == 201
    assert client.post("/api/tags", json={"group": "bogus", "name": "x"}).status_code == 422
    r = client.patch(f"/api/tags/{tid}", json={"name": "Đổi biến số"})
    assert r.json()["name"] == "Đổi biến số"
    assert [t["name"] for t in client.get("/api/tags", params={"group": "method"}).json()] == ["Đổi biến số"]
    assert client.delete(f"/api/tags/{tid}").status_code == 204
    assert client.get("/api/tags", params={"group": "method"}).json() == []
