"""Meetings from templates, notices by email and letter, letters page, insurance page."""
import datetime as dt

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Announcement, InsurancePolicy, Letter, Meeting
from app.services import letters, meetings


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


def test_agenda_builds_from_what_is_pending(client):
    client.post("/login/board")
    client.post("/board/decisions/new", data={"decision_type": "bid", "title": "Award asphalt bid to Desert Paving", "amount": "18500", "body": "three bids"})
    with client.application.test_request_context():
        from app.integrations.registry import get_provider
        agenda = meetings.build_agenda("board", "1001", get_provider())
    assert any("Award asphalt bid" in a for a in agenda) and agenda[0].startswith("Call to order") and agenda[-1] == "Adjourn"
    assert any("Treasurer" in a and "operating" in a for a in agenda)


def test_schedule_notice_minutes_and_letters(client):
    client.post("/login/board")
    date = (dt.date.today() + dt.timedelta(days=21)).isoformat()
    r = client.post("/board/meetings", data={"kind": "annual", "date": date, "time": "6:30 pm", "where": "Clubhouse", "agenda": "", "notice_days": "30"}, follow_redirects=False)
    m = Meeting.query.first()
    assert m.kind == "annual" and m.notice_days == 30 and len(m.agenda) >= 8 and r.headers["Location"].endswith(f"/board/meetings/{m.id}")
    r = client.get(f"/board/meetings/{m.id}")
    assert r.status_code == 200 and b"late" in r.data  # 30-day notice, 21 days out
    client.post(f"/board/meetings/{m.id}", data={"intent": "notice", "channels": ["email", "portal", "mail"], "audience": "all"})
    m = db.session.get(Meeting, m.id)
    assert m.notice_sent_at and "mail" in m.notice_channels
    assert Announcement.query.filter(Announcement.title.like("Notice:%")).first()
    ls = Letter.query.filter_by(meeting_id=m.id).all()
    assert ls and all(l.status == "simulated" and l.provider == "manual" for l in ls) and "Agenda" in ls[0].body
    client.post(f"/board/meetings/{m.id}", data={"intent": "minutes", "minutes": "Called to order 6:31 pm. Quorum present. Budget ratified 3-0.", "status": "held"})
    assert db.session.get(Meeting, m.id).status == "held"
    r = client.get(f"/board/meetings/{m.id}?print=1")
    assert b"Budget ratified" in r.data and b"Annual meeting" in r.data
    assert b"Minutes" in client.get("/board/meetings").data


def test_letters_page_preview_and_send_one_unit(client):
    client.post("/login/board")
    r = client.post("/board/letters", data={"intent": "preview", "kind": "collection", "audience": "unit", "unit_account_id": "ua-1003", "message": "Per the policy, a lien may be recorded after 75 days."})
    assert r.status_code == 200 and b"Past due assessment" in r.data and b"1 letter(s)" in r.data
    r = client.post("/board/letters", data={"intent": "send", "kind": "collection", "audience": "unit", "unit_account_id": "ua-1003", "certified": "1", "final_subject": "Past due assessment · {unit}", "final_body": "Dear {owner}, balance {balance}."}, follow_redirects=True)
    l = Letter.query.filter_by(kind="collection").first()
    assert l and l.certified and l.to_name.startswith("Okafor") and "$1,240.00" in l.body and "Unit 3" in l.subject and float(l.cost) > 6
    r = client.get("/board/letters")
    assert b"certified" in r.data and b"mailed by hey" in r.data


def test_announcement_mail_channel_sends_letters_to_owners_without_email(client):
    client.post("/login/board")
    client.post("/board/announcements", data={"intent": "send", "title": "Pool closes Oct 31", "body": "Gate codes reset Nov 1.", "channel": "mail"}, follow_redirects=True)
    assert Announcement.query.filter_by(title="Pool closes Oct 31").first()
    assert Letter.query.filter_by(kind="general").count() == 0  # every demo owner has an email
    client.post("/board/announcements", data={"intent": "send", "title": "Annual meeting Dec 10", "body": "Clubhouse, 7 pm.", "channel": "mail_all"}, follow_redirects=True)
    with client.application.app_context():
        from app.integrations.registry import get_provider
        n = len(get_provider().list_unit_accounts("1001"))
    assert n > 10 and Letter.query.filter_by(kind="general").count() == n


def test_insurance_page_gaps_and_renewals(client):
    client.post("/login/board")
    r = client.get("/board/insurance")
    assert r.status_code == 200 and b"Get a cyber quote" in r.data and b"Not on file" in r.data
    soon = (dt.date.today() + dt.timedelta(days=30)).isoformat()
    client.post("/board/insurance", data={"kind": "do", "carrier": "Travelers", "policy_number": "DO-1", "coverage": "1,000,000", "deductible": "2,500", "premium": "1,850", "expires": soon, "agent_name": "Rosa Delgado"})
    p = InsurancePolicy.query.first()
    assert p.coverage == 1_000_000 and p.days_to_expiry == 30
    r = client.get("/board/insurance")
    assert b"Renewing within 60 days" in r.data and b"Directors &amp; officers" in r.data
    client.post("/board/insurance", data={"intent": "seed_demo"})
    assert InsurancePolicy.query.count() == 5
