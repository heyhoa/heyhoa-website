"""Board: decisions and votes, owner inbox replies, documents, reserves, confidential invoices, voice intake."""
import io

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import InvoiceFlag, Message, ReserveComponent, StoredDocument, WorkItem


class Cfg(TestConfig):
    POSTMARK_INBOUND_TOKEN = "tok"
    COMMUNITY_ALIASES = {"willowcreek@heyhoa.com": "1001"}


@pytest.fixture
def client():
    app = create_app(Cfg)
    with app.test_client() as c:
        yield c


def test_transfer_decision_needs_two_votes_then_executes(client):
    client.post("/login/board")
    client.post("/board/decisions/new", data={"decision_type": "transfer", "title": "Move $12,000 to reserves", "amount": "12000", "body": "Q4 contribution catch-up"})
    d = WorkItem.query.filter_by(kind="decision").first()
    assert d.state == "proposed" and d.category == "transfer"
    client.post(f"/board/decisions/{d.id}/vote", data={"vote": "approve", "note": "ok"})
    assert db.session.get(WorkItem, d.id).state == "proposed"  # 1 of 2
    # second member votes via the decisions service (different member id)
    from app.services import decisions
    decisions.vote(db.session.get(WorkItem, d.id), "cc-8", "Luis Castillo", "approve")
    d = db.session.get(WorkItem, d.id)
    assert d.state == "done" and "Approved 2/2" in d.outcome
    ex = WorkItem.query.filter_by(kind="board_approved").first()
    assert ex.lane == "close" and ex.state == "escalated" and "bank" in ex.proposal["payload"]["note"].lower()


def test_deny_rejects(client):
    client.post("/login/board")
    client.post("/board/decisions/new", data={"decision_type": "work_order", "title": "Fix gate", "body": "x"})
    d = WorkItem.query.filter_by(kind="decision").first()
    client.post(f"/board/decisions/{d.id}/vote", data={"vote": "deny", "note": "get a second bid"})
    assert db.session.get(WorkItem, d.id).state == "rejected"


def test_service_request_to_work_order_decision(client):
    client.post("/login/board")
    r = client.post("/board/requests/sr-302/work-order", data={"vendor": "Bright Light Electric", "nte": "350"}, follow_redirects=True)
    assert r.status_code == 200
    d = WorkItem.query.filter_by(kind="decision", category="work_order").first()
    assert d and "Bright Light" in d.summary and d.proposal["payload"]["amount"] == 350.0


def test_board_inbox_shows_owner_traffic_and_reply_goes_out(client):
    client.post("/api/webhooks/postmark?token=tok", json={"FromFull": {"Email": "reed@example.com", "Name": "Marcus Reed"}, "ToFull": [{"Email": "willowcreek@heyhoa.com"}], "Subject": "Pool hours?", "TextBody": "When does the pool close for the season?", "MessageID": "m1"})
    client.post("/login/board")
    r = client.get("/board/inbox")
    assert b"Pool hours?" in r.data
    w = WorkItem.query.filter_by(kind="email").first()
    r = client.post(f"/board/inbox/{w.id}/reply", data={"body": "Oct 31 this year. Thanks for asking.", "resolve": "1"}, follow_redirects=True)
    assert r.status_code == 200
    out = Message.query.filter_by(work_item_id=w.id, direction="out", author="board").first()
    assert out and out.recipient == "reed@example.com" and db.session.get(WorkItem, w.id).state == "done"


def test_board_cannot_open_other_community_item(client):
    client.post("/login/board")
    other = WorkItem(community_id="1002", kind="email", lane="cs", subject="x", summary="y")
    db.session.add(other)
    db.session.commit()
    assert client.get(f"/board/inbox/{other.id}").status_code == 404


def test_document_upload_with_expiry_and_owner_visibility(client):
    client.post("/login/board")
    r = client.post("/board/documents/upload", data={"file": (io.BytesIO(b"contract"), "greenscape.pdf"), "title": "GreenScape contract", "category": "contract", "visibility": "board", "vendor": "GreenScape Lawn Co", "expires_on": "2026-12-15", "notes": "$1,850/mo"}, content_type="multipart/form-data", follow_redirects=True)
    assert r.status_code == 200 and b"Expiring within 90 days" in r.data
    d = StoredDocument.query.first()
    assert d.vendor == "GreenScape Lawn Co" and d.size == 8
    client.post("/board/documents/upload", data={"title": "Pool rules 2026", "category": "rules", "visibility": "owners"}, follow_redirects=True)
    client.get("/logout")
    client.post("/login/homeowner")
    r = client.get("/me/documents")
    assert b"Pool rules 2026" in r.data and b"GreenScape contract" not in r.data


def test_reserve_study_upload_creates_extraction_item_and_plan_math(client):
    client.post("/login/board")
    client.post("/board/documents/upload", data={"file": (io.BytesIO(b"study"), "study.pdf"), "title": "2026 Level II study", "category": "reserve_study"}, follow_redirects=True)
    assert WorkItem.query.filter_by(kind="reserve_study", lane="onboarding").first()
    client.post("/board/reserves", data={"intent": "seed_demo"})
    assert ReserveComponent.query.count() == 5
    r = client.get("/board/reserves")
    assert r.status_code == 200 and b"Percent funded" in r.data and b"2027" in r.data
    roof = ReserveComponent.query.filter_by(name="Roofs (12 buildings)").first()
    assert round(roof.accrued) == round(412000 * 16 / 25)


def test_confidential_invoice_hidden_from_owners(client):
    client.post("/login/board")
    client.post("/board/invoices/inv-5106/confidential", data={"confidential": "1", "reason": "legal"})
    assert InvoiceFlag.query.filter_by(invoice_id="inv-5106").first().confidential
    client.get("/logout")
    client.post("/login/homeowner")
    r = client.get("/me/spending")
    assert b"GreenScape" in r.data and b"Bright Light" not in r.data and b"shown only to the board" in r.data
    assert client.get("/board/delinquencies").status_code == 403  # owners never see delinquencies


def test_voice_intake_creates_call_item(client):
    r = client.post("/api/webhooks/twilio/voice?token=tok&step=0&community=1001", data={"From": "+14805550112"})
    assert r.status_code == 200 and b"<Gather" in r.data and b"What is your name" in r.data
    r = client.post("/api/webhooks/twilio/voice?token=tok&step=1&community=1001", data={"From": "+14805550112", "SpeechResult": "Marcus Reed unit 12"})
    assert b"what can we help with" in r.data
    r = client.post("/api/webhooks/twilio/voice?token=tok&step=2&community=1001&name=Marcus%20Reed%20unit%2012", data={"From": "+14805550112", "SpeechResult": "The gate code stopped working"})
    assert b"passed this to the board" in r.data and b"<Hangup/>" in r.data
    w = WorkItem.query.filter_by(kind="call").first()
    assert w and w.community_id == "1001" and "gate code" in w.summary and "0112" in w.summary
    assert client.post("/api/webhooks/twilio/voice?step=0").status_code == 401
