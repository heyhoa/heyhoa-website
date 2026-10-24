"""Sales: quote → proposal email + sequence, web proposal, books review, outreach import."""
import datetime as dt
import io

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Lead, WorkItem
from app.services import sales


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


LEAD = {"community_name": "Cedar Park Villas", "community_type": "townhome", "units": "64", "state": "tx", "city": "Cedar Park", "current_setup": "self",
        "pain_points": ["late financials"], "contact_name": "Dana Whitfield", "contact_role": "treasurer", "email": "dana@cedarpark.example", "plan": ""}


def test_quote_math():
    class L:  # minimal lead stand-in
        plan, pain_points, units, current_setup = None, "late financials", 64, "self"
    q = sales.quote(L())
    assert q["slug"] == "back-office" and q["monthly"] == 349 + 34 * 9 and q["per_door"] == round(q["monthly"] / 64, 2)
    assert sales.monthly_price("books", 24) == 199 and sales.monthly_price("board-plus", 150) == 549 + 120 * 12


def test_quote_creates_sales_item_and_sequence(client):
    client.post("/quote", data=LEAD)
    lead = Lead.query.filter_by(community_name="Cedar Park Villas").first()
    item = WorkItem.query.filter_by(kind="lead").first()
    assert item.lane == "sales" and item.state == "proposed" and item.proposal["action"] == "send_email"
    body = item.proposal["payload"]["body"]
    assert "$655" in body and "/proposal/" in body and "/books-review" in body and item.proposal["payload"]["to"] == lead.email
    follow = WorkItem.query.filter_by(kind="followup").order_by(WorkItem.sla_due).all()
    assert len(follow) == 4 and all(f.state == "new" for f in follow)
    days = lambda w: round((w.sla_due - w.created_at).total_seconds() / 86400)  # noqa: E731
    assert days(follow[0]) == 4 and days(follow[-1]) == 14


def test_due_followup_runs_and_stops_when_lost(client):
    client.post("/quote", data=LEAD)
    lead = Lead.query.first()
    f = WorkItem.query.filter_by(kind="followup").order_by(WorkItem.sla_due).first()
    f.sla_due = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)
    from app.extensions import db
    db.session.commit()
    from app.agents import runtime
    assert runtime.run_due_followups() == 1
    f = db.session.get(WorkItem, f.id)
    assert f.state == "proposed" and "packet date" in f.proposal["payload"]["subject"]
    # lost → next due touch is a no-op
    lead.status = "lost"
    db.session.commit()
    g = WorkItem.query.filter_by(kind="followup", state="new").order_by(WorkItem.sla_due).first()
    g.sla_due = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)
    db.session.commit()
    runtime.run_due_followups()
    assert db.session.get(WorkItem, g.id).state == "done"


def test_web_proposal_renders_and_accepts(client):
    client.post("/quote", data=LEAD)
    lead = Lead.query.first()
    url = sales.proposal_url(lead).split("http://localhost")[-1]
    r = client.get(url)
    assert r.status_code == 200 and b"$655" in r.data and b"Back Office" in r.data and b"Week 3" in r.data
    r = client.post(url, follow_redirects=True)
    assert b"accepted" in r.data and db.session.get(Lead, lead.id).status == "accepted"
    assert WorkItem.query.filter_by(kind="lead_accepted").first().lane == "sales"
    assert client.get("/proposal/not-a-token").status_code == 404


def test_books_review_uploads_and_creates_items(client):
    data = {**LEAD, "files": [(io.BytesIO(b"%PDF-1.4 fake"), "sept.pdf"), (io.BytesIO(b"%PDF-1.4 fake"), "aug.pdf")]}
    r = client.post("/books-review", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert r.status_code == 200 and b"Got your statements" in r.data
    lead = Lead.query.first()
    assert lead.source == "books-review"
    w = WorkItem.query.filter_by(kind="books_review").first()
    assert w and w.lane == "sales" and w.state == "escalated" and "sept.pdf" in w.summary


def test_ops_leads_pipeline(client):
    client.post("/quote", data=LEAD)
    client.post("/login/ops")
    r = client.get("/ops/leads")
    assert b"Cedar Park Villas" in r.data and b"$655" in r.data
    lead = Lead.query.first()
    client.post(f"/ops/leads/{lead.id}/status", data={"status": "contacted"})
    assert db.session.get(Lead, lead.id).status == "contacted"


def test_home_has_no_fabricated_quotes(client):
    r = client.get("/")
    assert b"Why boards trust this" in r.data and b"Dana W., Treasurer" not in r.data
