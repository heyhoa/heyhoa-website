"""Help Scout integration: lead notification, contact delivery, webhook triage. No network."""
import base64
import hashlib
import hmac
import json

import pytest

from app import create_app
from app.config import TestConfig


class HSConfig(TestConfig):
    HELPSCOUT_APP_ID = "id"
    HELPSCOUT_APP_SECRET = "secret"
    HELPSCOUT_WEBHOOK_SECRET = "whsec"
    HELPSCOUT_MAILBOX_ID_SUPPORT = "11"
    HELPSCOUT_MAILBOX_ID_SALES = "22"
    HELPSCOUT_ASSIGNEE_COORDINATOR = "7"
    SLACK_WEBHOOK_URL = "https://hooks.slack.example/x"
    COMMUNITY_ALIASES = {"willowcreek@heyhoa.com": "1001"}


class FakeResp:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._body, self.headers, self.content = status, body or {}, headers or {}, b"x"
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


@pytest.fixture
def calls(monkeypatch):
    calls = []

    def fake_request(self, method, url, **kw):
        calls.append((method, url, kw.get("json")))
        if url.endswith("/oauth2/token"):
            return FakeResp(200, {"access_token": "tok", "expires_in": 100000})
        if method == "POST" and url.endswith("/conversations"):
            return FakeResp(201, {}, {"Resource-ID": "501"})
        return FakeResp(200, {})

    def fake_session_post(self, url, **kw):  # token endpoint uses Session.post
        calls.append(("POST", url, kw.get("json") or kw.get("data")))
        if url.endswith("/oauth2/token"):
            return FakeResp(200, {"access_token": "tok", "expires_in": 100000})
        return FakeResp(200, {})

    def fake_module_post(url, **kw):  # slack uses requests.post
        calls.append(("POST", url, kw.get("json")))
        return FakeResp(200, {})

    import requests

    monkeypatch.setattr(requests.Session, "request", fake_request)
    monkeypatch.setattr(requests.Session, "post", fake_session_post)
    monkeypatch.setattr(requests, "post", fake_module_post)
    return calls


@pytest.fixture
def client():
    app = create_app(HSConfig)
    with app.test_client() as c:
        yield c


def test_lead_creates_sales_conversation_and_slack(client, calls):
    r = client.post("/quote", data={"community_name": "Test HOA", "units": "48", "state": "tx", "current_setup": "self", "contact_name": "Dana W", "contact_role": "treasurer", "email": "dana@x.co", "plan": "books"})
    assert r.status_code == 302
    convo = next(c for c in calls if c[0] == "POST" and c[1].endswith("/conversations"))
    assert convo[2]["mailboxId"] == 22 and "Test HOA" in convo[2]["subject"] and "lead" in convo[2]["tags"] and convo[2]["imported"] is True
    assert any(c[1].startswith("https://hooks.slack.example") for c in calls)


def test_contact_message_lands_in_support_mailbox(client, calls):
    client.post("/contact", data={"name": "Owner", "email": "o@x.co", "topic": "owner", "message": "hi"})
    convo = next(c for c in calls if c[0] == "POST" and c[1].endswith("/conversations"))
    assert convo[2]["mailboxId"] == 11 and convo[2]["tags"] == ["website", "owner"]


def _signed(body: dict):
    raw = json.dumps(body).encode()
    sig = base64.b64encode(hmac.new(b"whsec", raw, hashlib.sha1).digest()).decode()
    return raw, sig


def test_webhook_rejects_bad_signature(client):
    r = client.post("/api/webhooks/helpscout", data=b"{}", headers={"X-HelpScout-Signature": "nope", "X-HelpScout-Event": "convo.created", "Content-Type": "application/json"})
    assert r.status_code == 401


def test_webhook_auto_replies_to_known_owner_balance_question(client, calls):
    body = {"id": 900, "subject": "What is my balance?", "primaryCustomer": {"email": "reed@example.com"},
            "_embedded": {"threads": [{"type": "customer", "to": ["willowcreek@heyhoa.com"], "body": "Hi, what do I owe right now?"}]}}
    raw, sig = _signed(body)
    r = client.post("/api/webhooks/helpscout", data=raw, headers={"X-HelpScout-Signature": sig, "X-HelpScout-Event": "convo.created", "Content-Type": "application/json"})
    j = r.get_json()
    assert r.status_code == 200 and j["owner_found"] and j["category"] == "balance" and j["route"] == "hey" and j["action"] == "replied"
    reply = next(c for c in calls if c[1].endswith("/conversations/900/reply"))
    assert "balance" in reply[2]["text"].lower()
    from app.models import PortalRequest
    assert PortalRequest.query.filter_by(remote_id="hs:900").first().status == "closed"


def test_webhook_drafts_and_assigns_dispute(client, calls):
    body = {"id": 901, "subject": "Late fee is wrong", "primaryCustomer": {"email": "reed@example.com"},
            "_embedded": {"threads": [{"type": "customer", "to": ["willowcreek@heyhoa.com"], "body": "I dispute this late fee, please waive it."}]}}
    raw, sig = _signed(body)
    j = client.post("/api/webhooks/helpscout", data=raw, headers={"X-HelpScout-Signature": sig, "X-HelpScout-Event": "convo.created", "Content-Type": "application/json"}).get_json()
    assert j["route"] == "accountant" and j["action"] == "drafted"
    assert any(c[1].endswith("/conversations/901/notes") for c in calls)
    assert not any(c[1].endswith("/conversations/901/reply") for c in calls)


def test_webhook_unknown_sender_goes_to_coordinator(client, calls):
    body = {"id": 902, "subject": "balance?", "primaryCustomer": {"email": "stranger@nowhere.com"}, "_embedded": {"threads": [{"type": "customer", "to": ["willowcreek@heyhoa.com"], "body": "what is my balance"}]}}
    raw, sig = _signed(body)
    j = client.post("/api/webhooks/helpscout", data=raw, headers={"X-HelpScout-Signature": sig, "X-HelpScout-Event": "convo.created", "Content-Type": "application/json"}).get_json()
    assert not j["owner_found"] and j["route"] == "coordinator" and j["action"] == "drafted"
    assign = next(c for c in calls if c[0] == "PATCH" and c[1].endswith("/conversations/902"))
    assert assign[2]["value"] == 7


def test_webhook_ignores_other_events(client):
    raw, sig = _signed({"id": 1})
    r = client.post("/api/webhooks/helpscout", data=raw, headers={"X-HelpScout-Signature": sig, "X-HelpScout-Event": "convo.tags", "Content-Type": "application/json"})
    assert r.status_code == 204
