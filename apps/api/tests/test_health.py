def test_health_reports_db_and_storage(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok", "storage": "ok"}


def test_app_error_shape(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
