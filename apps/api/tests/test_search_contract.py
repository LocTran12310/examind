"""The search contract (architecture-refactor AC-02), exercised on tags."""
from tests.factories import login_as


def names(r):
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"data", "total", "page", "limit"}
    return [t["name"] for t in body["data"]]


def test_string_operators_sort_paging_and_errors(client, db):
    login_as(client, db, "teacher")
    for group, name in [("method", "Phương trình"), ("method", "Phân số"), ("skill", "Đổi biến số"), ("custom", "Có hình vẽ")]:
        assert client.post("/api/tags", json={"group": group, "name": name}).status_code == 201
    s = lambda **b: client.post("/api/tags/search", json=b)  # noqa: E731
    assert names(s(filters={"name": {"operator": "+", "value": "ph"}}, sort=[{"field": "name"}])) == ["Phân số", "Phương trình"]
    assert names(s(filters={"name": {"operator": "-", "value": "so"}}, sort=[{"field": "name", "desc": True}])) == ["Phân số", "Đổi biến số"]
    assert names(s(filters={"name": {"operator": "=", "value": "PHAN SO"}})) == ["Phân số"]
    assert names(s(filters={"name": {"operator": "!", "value": "p"}}, sort=[{"field": "name"}])) == ["Có hình vẽ", "Đổi biến số"]
    assert names(s(filters={"group": {"value": ["method", "custom"]}}, sort=[{"field": "name"}])) == ["Có hình vẽ", "Phân số", "Phương trình"]
    assert names(s(q="bien")) == ["Đổi biến số"]
    body = s(limit=3, page=2, sort=[{"field": "name"}]).json()
    assert body["total"] == 4 and body["page"] == 2 and body["limit"] == 3 and len(body["data"]) == 1
    for bad, code in [({"filters": {"name": {"operator": ">", "value": "x"}}}, "bad_filter"),
                      ({"filters": {"nope": {"value": "x"}}}, "bad_filter"),
                      ({"sort": [{"field": "nope"}]}, "bad_sort")]:
        r = s(**bad)
        assert r.status_code == 422 and r.json()["code"] == code, bad
    assert s(limit=5000).status_code == 422
    assert client.get("/api/tags").status_code in (404, 405)  # the old GET list is gone
