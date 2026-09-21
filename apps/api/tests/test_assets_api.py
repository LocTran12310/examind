from app.core.images import Canvas
from tests.factories import login_as, make_org, make_user


def png_bytes():
    c = Canvas(4, 3)
    c.dot(1, 1)
    return c.encode()


def test_upload_and_fetch_with_org_check(client, db):
    teacher = login_as(client, db, "teacher")
    r = client.post("/api/assets", files={"file": ("a.png", png_bytes(), "image/png")})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["width"] == 4 and body["height"] == 3 and body["ref"].startswith("asset:")
    got = client.get(f"/api/assets/{body['id']}")
    assert got.status_code == 200 and got.headers["content-type"] == "image/png" and got.content == png_bytes()
    # other org cannot read it
    other = make_org(db, "orgb")
    make_user(db, other, "hsb")
    db.commit()
    stranger = client.__class__(client.app)
    stranger.post("/api/auth/login", json={"org_code": "orgb", "username": "hsb", "password": "Secret123!"})
    assert stranger.get(f"/api/assets/{body['id']}").status_code == 404


def test_rejects_svg_and_non_images(client, db):
    login_as(client, db, "teacher")
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    assert client.post("/api/assets", files={"file": ("x.svg", svg, "image/svg+xml")}).status_code == 422


def test_demo_question_seeded_for_new_org(client, db):
    login_as(client, db)
    created = client.post("/api/admin/orgs", json={"code": "ttdemo", "name": "Demo"}).json()
    admin = client.__class__(client.app)
    admin.post("/api/auth/login", json={"org_code": "ttdemo", "username": "admin", "password": created["admin"]["temp_password"]})
    admin.post("/api/auth/change-password", json={"current_password": created["admin"]["temp_password"], "new_password": "NewPass123"})
    q = admin.get("/api/questions/demo").json()
    assert q["answer"] == {"key": "C"} and "$y = x^2 - 4x + 3$" in q["stem"]
    import re

    refs = re.findall(r"asset:([0-9a-f-]{36})", q["options"][2]["content"] + q["solution"])
    assert len(refs) == 2
    for ref in refs:
        assert admin.get(f"/api/assets/{ref}").status_code == 200


def test_student_gets_no_answer(client, db):
    student = login_as(client, db, "student")
    from app.seed.bootstrap import seed_demo

    seed_demo(db, student.organization_id)
    db.commit()
    qid = db.execute(__import__("sqlalchemy").text("select id from questions limit 1")).scalar()
    q = client.get(f"/api/questions/{qid}").json()
    assert q["answer"] is None and q["solution"] == ""
