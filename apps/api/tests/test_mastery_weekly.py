from datetime import timedelta

from sqlalchemy import select, text

from app.modules.analytics.domain.entities import TopicMastery
from app.modules.analytics.domain.services.weeks import week_start
from app.modules.analytics.interface.deps import analytics_api
from app.seed.bootstrap import backfill_mastery_weeks_if_missing
from app.shared.infrastructure.schema.analytics import student_topic_week
from app.shared.infrastructure.timezone import business_today
from tests.exam_helpers import login
from tests.test_mastery import ENOUGH, take


def rows(db) -> list:
    db.expire_all()
    return db.execute(select(student_topic_week).order_by(student_topic_week.c.week_start)).mappings().all()


def test_the_backfill_derives_the_past_weeks_and_the_series_reads_them(client, db):
    take(client, db, right=False, rounds=ENOUGH)
    # the answers belong to last week (7 days back keeps the weekday), so the series has something to trend over
    db.execute(text("update answer_facts set created_at = created_at - interval '7 days'"))
    db.commit()
    assert analytics_api(db).rebuild_mastery(None) == 4 * ENOUGH
    db.commit()

    written = backfill_mastery_weeks_if_missing(db)
    db.commit()
    kept = rows(db)
    live = {(m.student_id, m.topic_id): m for m in db.scalars(select(TopicMastery))}
    weeks = sorted({r["week_start"] for r in kept})
    assert weeks == [week_start(business_today()) - timedelta(days=7), week_start(business_today())]
    assert written == len(kept) == 2 * len(live)  # every tracked topic, in both weeks
    assert backfill_mastery_weeks_if_missing(db) == 0  # already kept

    last = {(r["student_id"], r["topic_id"]): r for r in kept if r["week_start"] == weeks[-1]}
    assert set(last) == set(live)
    for key, r in last.items():
        assert r["mastery"] < 0.5 and r["answers"] == 0  # nothing answered this week; the value decayed on its own
        assert r["mastery"] > live[key].mastery  # …back toward the middle
    assert sum(r["answers"] for r in kept if r["week_start"] == weeks[0]) == 4 * ENOUGH


def test_the_weekly_job_writes_the_running_week_and_can_run_again(client, db):
    take(client, db, right=False, rounds=ENOUGH)
    from app.worker.handlers import snapshot_mastery_week

    written = snapshot_mastery_week(db)
    db.commit()
    kept = rows(db)
    assert written == len(kept) >= 1
    assert {r["week_start"] for r in kept} == {week_start(business_today())}
    assert sum(r["answers"] for r in kept) == 4 * ENOUGH
    live = {(m.student_id, m.topic_id): round(m.mastery, 4) for m in db.scalars(select(TopicMastery))}
    assert {(r["student_id"], r["topic_id"]): round(r["mastery"], 4) for r in kept} == live
    assert snapshot_mastery_week(db) == written  # idempotent: the week is rewritten, not doubled
    db.commit()
    assert len(rows(db)) == written


def test_the_series_endpoints_are_org_scoped(client, db):
    take(client, db, right=False, rounds=ENOUGH)
    backfill_mastery_weeks_if_missing(db)
    db.commit()
    s = login(client, "trungtama", "hs01")
    body = s.get("/api/me/mastery/weekly").json()
    assert body["weeks"] and all(t["answers"] >= 0 and 0 <= t["mastery"] <= 1 for w in body["weeks"] for t in w["topics"])
    student_id = s.get("/api/auth/me").json()["id"]
    assert client.get(f"/api/students/{student_id}/mastery/weekly").json() == body
    assert s.get(f"/api/students/{student_id}/mastery/weekly").status_code == 403  # a student only sees their own
    assert client.get("/api/me/mastery/weekly").status_code == 403  # staff use the per-student endpoint
