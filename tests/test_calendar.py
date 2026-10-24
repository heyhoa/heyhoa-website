"""Board calendar: occurrences, lead windows, done marking, reminders into the board lane, roster terms."""
import datetime as dt

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import BoardMember, CalendarItem, WorkItem
from app.services import calendar as cal


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


def test_occurrences_and_status(client):
    with client.application.app_context():
        it = CalendarItem(community_id="1001", title="Budget", repeats="annual", month=10, day=15, lead_days=60, owner="treasurer")
        q = CalendarItem(community_id="1001", title="Reserve check", repeats="quarterly", month=1, day=10, lead_days=7, owner="treasurer")
        m = CalendarItem(community_id="1001", title="Package", repeats="monthly", day=5, lead_days=0, owner="hey")
        db.session.add_all([it, q, m])
        db.session.commit()
        today = dt.date(2026, 9, 1)
        rows = cal.upcoming("1001", today=today)
        budget = [r for r in rows if r["item"].id == it.id]
        assert budget[0]["due"] == dt.date(2026, 10, 15) and budget[0]["status"] == "due" and budget[0]["period"] == "2026"  # 44 days out, inside the 60-day window
        quarters = [r["period"] for r in rows if r["item"].id == q.id]
        assert quarters[:2] == ["2026-Q4", "2027-Q1"] and [r["due"] for r in rows if r["item"].id == q.id][0] == dt.date(2026, 10, 10)
        monthly = [r for r in rows if r["item"].id == m.id]
        assert monthly[0]["due"] == dt.date(2026, 9, 5) and monthly[0]["status"] == "upcoming" and len(monthly) >= 12
        cal.mark_done(it.id, "2026", "Dana Whitfield")
        assert [r for r in cal.upcoming("1001", today=today) if r["item"].id == it.id][0]["status"] == "done"
        assert [r for r in cal.upcoming("1001", today=dt.date(2026, 11, 1)) if r["item"].id == it.id][0]["status"] == "done"
        cal.unmark(it.id, "2026")
        assert [r for r in cal.upcoming("1001", today=dt.date(2026, 11, 1)) if r["item"].id == it.id][0]["status"] == "overdue"


def test_standard_calendar_and_reminders_email_the_owner(client):
    client.post("/login/board")
    client.post("/board/calendar", data={"intent": "seed"})
    assert CalendarItem.query.filter_by(community_id="1001").count() == len(cal.STANDARD)
    client.post("/board/calendar", data={"intent": "member", "name": "Dana Whitfield", "role": "treasurer", "email": "treasurer@willowcreek.example", "term_start": "2026-02-15", "term_years": "2", "signer": "on"})
    m = BoardMember.query.filter_by(name="Dana Whitfield").first()
    assert m.term_end == dt.date(2028, 2, 15) and m.signer
    r = client.get("/board/calendar")
    assert r.status_code == 200 and b"Annual meeting of members" in r.data and b"Dana Whitfield" in r.data
    with client.application.test_request_context():
        from app.agents import runtime
        n = runtime.calendar_reminders("1001")
        due = cal.due_now("1001")
        assert n == len(due) and n >= 1
        assert runtime.calendar_reminders("1001") == 0  # idempotent
        items = WorkItem.query.filter_by(kind="calendar", lane="board").all()
        treasurer_items = [w for w in items if (w.remote_ids or {}).get("owner") == "treasurer"]
        if treasurer_items:
            assert treasurer_items[0].proposal["action"] == "send_email" and treasurer_items[0].proposal["payload"]["to"] == "treasurer@willowcreek.example"
        hey_items = [w for w in items if (w.remote_ids or {}).get("owner") == "hey"]
        if hey_items:
            assert hey_items[0].proposal["action"] == "handoff"


def test_mark_done_from_page_and_roster_terms(client):
    client.post("/login/board")
    client.post("/board/calendar", data={"intent": "item", "title": "Backflow test", "kind": "maintenance", "repeats": "annual", "month": str(dt.date.today().month), "day": "28", "lead_days": "30", "owner": "board", "steps": "Call tester\nFile report"})
    it = CalendarItem.query.filter_by(title="Backflow test").first()
    assert it.steps == ["Call tester", "File report"]
    period = str(dt.date.today().year)
    client.post("/board/calendar", data={"intent": "done", "item_id": it.id, "period": period})
    r = client.get("/board/calendar")
    assert b"done" in r.data
    client.post("/board/calendar", data={"intent": "member", "name": "Old Member", "role": "director", "term_start": "2024-01-01", "term_years": "2"})
    assert cal.seats_ending("1001") and cal.seats_ending("1001")[0].days_left < 0
    r = client.get("/board/calendar")
    assert b"expired" in r.data
    client.post("/logout")
    client.post("/login/homeowner")
    assert b"Old Member" in client.get("/me/directory").data
