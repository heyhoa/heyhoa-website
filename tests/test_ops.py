"""hey ops: inbound email → work item → proposal → review → execution. No network."""
import json

import pytest

from app import create_app
from app.agents import runtime
from app.config import TestConfig
from app.models import AgentRun, Message, WorkItem


class OpsConfig(TestConfig):
    POSTMARK_INBOUND_TOKEN = "tok"
    COMMUNITY_ALIASES = {"willowcreek@heyhoa.com": "1001"}
    SHADOW_MODE = True


class LiveConfig(OpsConfig):
    SHADOW_MODE = False


def _inbound(frm, subject, body, to="willowcreek@heyhoa.com"):
    return {"FromFull": {"Email": frm, "Name": "Marcus Reed"}, "ToFull": [{"Email": to}], "Subject": subject, "TextBody": body, "MessageID": "pm-1", "Attachments": []}


@pytest.fixture
def client():
    app = create_app(OpsConfig)
    with app.test_client() as c:
        yield c


@pytest.fixture
def live_client():
    app = create_app(LiveConfig)
    with app.test_client() as c:
        yield c


def test_webhook_requires_token(client):
    assert client.post("/api/webhooks/postmark", json=_inbound("reed@example.com", "balance", "what do I owe")).status_code == 401


def test_balance_question_from_known_owner_is_proposed_in_shadow(client):
    r = client.post("/api/webhooks/postmark?token=tok", json=_inbound("reed@example.com", "What is my balance?", "Hi, what do I owe right now?"))
    j = r.get_json()
    assert r.status_code == 200 and j["lane"] == "cs" and j["state"] == "proposed" and j["action"] == "send_email"
    w = WorkItem.query.get(j["work_item"])
    assert w.unit_account_id == "ua-1012" and w.category == "balance" and w.needs_review
    assert "balance" in w.proposal["payload"]["body"].lower()
    assert len(w.messages) == 1 and w.messages[0].direction == "in"
    assert AgentRun.query.filter_by(work_item_id=w.id).count() >= 1


def test_same_question_auto_executes_when_shadow_off(live_client):
    j = live_client.post("/api/webhooks/postmark?token=tok", json=_inbound("reed@example.com", "balance", "what do I owe right now?")).get_json()
    w = WorkItem.query.get(j["work_item"])
    assert w.state == "done" and w.reviewer is None
    out = [m for m in w.messages if m.direction == "out"]
    assert len(out) == 1 and out[0].channel == "email" and out[0].meta.get("simulated")


def test_dispute_hands_off_to_ar_and_escalates_to_accountant(client):
    j = client.post("/api/webhooks/postmark?token=tok", json=_inbound("reed@example.com", "Late fee is wrong", "I dispute this late fee, please waive it.")).get_json()
    w = WorkItem.query.get(j["work_item"])
    assert w.lane == "ar" and w.state in ("proposed", "escalated") and w.proposal["action"] == "escalate"


def test_unknown_sender_goes_to_person(client):
    j = client.post("/api/webhooks/postmark?token=tok", json=_inbound("stranger@nowhere.com", "balance?", "what is my balance")).get_json()
    w = WorkItem.query.get(j["work_item"])
    assert w.unit_account_id is None and w.proposal["action"] == "escalate"


def test_review_approve_executes_and_logs(client):
    j = client.post("/api/webhooks/postmark?token=tok", json=_inbound("reed@example.com", "pool", "when does the pool open?")).get_json()
    client.post("/login/ops")
    r = client.post(f"/ops/item/{j['work_item']}/approve", data={"body": "Edited answer: May 1.", "note": "ok"}, follow_redirects=True)
    assert r.status_code == 200
    w = WorkItem.query.get(j["work_item"])
    assert w.state == "done" and w.reviewer == "Jordan Alvarez"
    out = [m for m in w.messages if m.direction == "out"][0]
    assert out.body == "Edited answer: May 1." and out.recipient == "reed@example.com"


def test_review_reject_sends_nothing(client):
    j = client.post("/api/webhooks/postmark?token=tok", json=_inbound("reed@example.com", "pool", "when does the pool open?")).get_json()
    client.post("/login/ops")
    client.post(f"/ops/item/{j['work_item']}/reject", data={"note": "wrong tone"})
    w = WorkItem.query.get(j["work_item"])
    assert w.state == "rejected" and not [m for m in w.messages if m.direction == "out"]


def test_daily_agents_create_ar_ap_close_items(client):
    client.post("/login/ops")
    r = client.post("/ops/run-daily", follow_redirects=True)
    assert r.status_code == 200
    ar = WorkItem.query.filter_by(lane="ar", kind="delinquency").all()
    assert len(ar) == 4
    stages = {w.unit_account_id: w.proposal["action"] for w in ar}
    assert stages["ua-1003"] == "queue_board_decision"  # 94 days, lien recorded → attorney vote
    assert stages["ua-1031"] == "send_notice" and "rebill" in json.dumps(WorkItem.query.filter_by(unit_account_id="ua-1031").first().proposal)
    assert WorkItem.query.filter_by(lane="ap", kind="vendor_compliance").first().proposal["action"] == "request_vendor_document"
    close = WorkItem.query.filter_by(lane="close").first()
    assert close.state == "done" and "accounts_snapshotted" in json.dumps(close.outcome) or close.state == "done"
    from app.integrations.mock import MockProvider
    assert WorkItem.query.filter_by(kind="invoice").count() == len(MockProvider().list_invoices("1001", status="pending_board"))
    # idempotent: running again adds no duplicate AR items
    client.post("/ops/run-daily")
    assert WorkItem.query.filter_by(lane="ar", kind="delinquency").count() == 4


def test_manual_intake_logs_call(client):
    client.post("/login/ops")
    r = client.post("/ops/new", data={"community_id": "1001", "kind": "call", "name": "Marcus Reed", "email": "reed@example.com", "unit_account_id": "ua-1012", "lane": "cs", "subject": "Called about sprinkler", "body": "Sprinkler head broken at the corner, spraying the sidewalk"}, follow_redirects=True)
    assert r.status_code == 200
    w = WorkItem.query.filter_by(kind="call").first()
    assert w.proposal["action"] == "create_service_request" and w.proposal["payload"]["category"] == "Irrigation"


def test_contact_form_becomes_work_item(client):
    client.post("/contact", data={"name": "Owner", "email": "o@x.co", "topic": "owner", "message": "I need a copy of the bylaws"})
    w = WorkItem.query.filter(WorkItem.subject.like("[owner]%")).first()
    assert w is not None and w.lane == "cs"
