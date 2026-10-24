"""Sign-in and the inbox: password + emailed code, trusted device, set-password links, one-click actions after sign-in."""
import re

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import AuditLog, BoardMember, WorkItem
from app.services import accounts, board_mail, decisions, magic


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


@pytest.fixture
def outbox(monkeypatch):
    sent = []
    import app.services.accounts as acc

    monkeypatch.setattr(acc.email_channel, "send", lambda to, subject, body, **kw: sent.append({"to": to, "subject": subject, "body": body}) or {"delivered": False, "simulated": True})
    return sent


def _member(client, name="Dana Whitfield", role="treasurer", email="treasurer@willowcreek.example", signer=True, password="correct horse battery"):
    with client.application.app_context():
        m = BoardMember(community_id="1001", name=name, role=role, email=email, signer=signer)
        db.session.add(m)
        db.session.commit()
        if password:
            accounts.set_password(m, password)
        return m.id


def _code(outbox):
    return re.search(r"(\d{6}) is your", outbox[-1]["subject"]).group(1)


def _sign_in(client, outbox, email="treasurer@willowcreek.example", password="correct horse battery"):
    r = client.post("/login", data={"email": email, "password": password})
    assert r.headers["Location"].endswith("/login/code")
    return client.post("/login/code", data={"code": _code(outbox)})


def test_password_then_code_then_trusted_device(client, outbox):
    _member(client)
    r = client.post("/login", data={"email": "treasurer@willowcreek.example", "password": "wrong"}, follow_redirects=True)
    assert b"not right" in r.data
    r = _sign_in(client, outbox)
    assert r.status_code == 302 and r.headers["Location"].endswith("/board/dashboard")
    with client.session_transaction() as s:
        assert s["role"] == "board" and s["user"]["name"] == "Dana Whitfield" and s["mfa_at"]
    assert b"Hey, Dana." in client.get("/board/").data and b"Your first month" not in client.get("/board/").data
    assert AuditLog.query.filter_by(action="login", actor="Dana Whitfield").count() == 1
    # trusted device: sign in again, no code this time
    n = len(outbox)
    r = client.post("/login", data={"email": "treasurer@willowcreek.example", "password": "correct horse battery"})
    assert r.headers["Location"].endswith("/board/dashboard") and len(outbox) == n


def test_wrong_code_and_lockout(client, outbox):
    _member(client)
    client.post("/login", data={"email": "treasurer@willowcreek.example", "password": "correct horse battery"})
    r = client.post("/login/code", data={"code": "000000"}, follow_redirects=True)
    assert b"not right" in r.data
    with client.session_transaction() as s:
        assert "role" not in s
    for _ in range(5):
        client.post("/login", data={"email": "treasurer@willowcreek.example", "password": "nope"})
    r = client.post("/login", data={"email": "treasurer@willowcreek.example", "password": "correct horse battery"}, follow_redirects=True)
    assert b"Too many tries" in r.data


def test_invite_sets_password_and_reset_is_quiet(client, outbox):
    client.post("/login/board")  # demo board adds a colleague to the roster → invite email
    client.post("/board/calendar", data={"intent": "member", "name": "Grace Thompson", "role": "secretary", "email": "grace@willowcreek.example"})
    assert outbox and "Set up your hey hoa board login" in outbox[-1]["subject"]
    url = re.search(r"https?://\S+/set-password/\S+", outbox[-1]["body"]).group(0)
    path = "/set-password/" + url.split("/set-password/")[1]
    client.get("/logout")
    r = client.post(path, data={"password": "short", "again": "short"}, follow_redirects=True)
    assert b"at least 10" in r.data
    r = client.post(path, data={"password": "a long enough sentence", "again": "a long enough sentence"}, follow_redirects=True)
    assert b"Password set" in r.data
    assert client.get(path).status_code == 302  # link is one use
    r = _sign_in(client, outbox, email="grace@willowcreek.example", password="a long enough sentence")
    assert r.status_code == 302
    n = len(outbox)
    client.post("/login/forgot", data={"email": "nobody@example.com"})
    assert len(outbox) == n
    r = client.post("/login/forgot", data={"email": "grace@willowcreek.example"}, follow_redirects=True)
    assert len(outbox) == n + 1 and b"reset link is on its way" in r.data


def test_one_click_needs_sign_in_then_finishes_and_is_idempotent(client, outbox):
    mid = _member(client)
    with client.application.test_request_context():
        m = db.session.get(BoardMember, mid)
        path = "/go/" + magic.action_url("invoice", "inv-5101", "approve", m).split("/go/")[1]
    r = client.get(path)
    assert r.status_code == 302 and r.headers["Location"].endswith("/login")  # parked
    r = _sign_in(client, outbox)
    assert "/go/" in r.headers["Location"]  # finishes the parked action
    r = client.get(r.headers["Location"])
    assert r.status_code == 200 and b"Approved" in r.data and b"of 2 approvals" in r.data
    assert AuditLog.query.filter_by(actor="Dana Whitfield", action="invoice.approve", target="inv-5101").count() == 1
    r = client.get(path)
    assert b"already" in r.data and AuditLog.query.filter_by(actor="Dana Whitfield", action="invoice.approve").count() == 1


def test_one_click_vote_only_for_the_named_member(client, outbox):
    mid = _member(client)
    _member(client, name="Luis Castillo", role="president", email="luis@willowcreek.example")
    client.post("/login/board")
    client.post("/board/decisions/new", data={"decision_type": "transfer", "title": "Move $5,000", "amount": "5000", "body": "x"})
    d = WorkItem.query.filter_by(kind="decision").first()
    with client.application.test_request_context():
        m = db.session.get(BoardMember, mid)
        path = "/go/" + magic.action_url("decision", d.id, "approve", m).split("/go/")[1]
    client.get("/logout")
    _sign_in(client, outbox, email="luis@willowcreek.example")  # the wrong member is signed in
    r = client.get(path)
    assert r.status_code == 302  # parked again, asks for Dana
    client.get("/logout")  # clears the parked action too
    _sign_in(client, outbox)
    r = client.get(path)
    assert b"you voted approve" in r.data
    votes = db.session.get(WorkItem, d.id).remote_ids["votes"]
    assert len(votes) == 1 and votes[0]["member"] == "Dana Whitfield"
    assert client.get("/go/not-a-token").status_code == 400


def test_home_is_the_inbox_in_plain_words(client):
    client.post("/login/board")
    client.post("/board/decisions/new", data={"decision_type": "bid", "title": "Award asphalt bid", "amount": "18500", "body": "three bids"})
    r = client.get("/board/")
    assert r.status_code == 200 and b"Needs you" in r.data and b"Award asphalt bid" in r.data and b'id="dec-' in r.data
    assert b"Bills</a>" in r.data and b"Votes</a>" in r.data and b"Owners behind</a>" in r.data
    assert b"GL account" not in r.data and b"(memo)" not in r.data and b'id="ask-drawer"' in r.data


def test_emails_carry_the_portal_link_not_a_login_link(client):
    _member(client, password=None)
    with client.application.test_request_context():
        item = decisions.create("1001", "bid", "Award fence bid", "two bids", amount=9000, requested_by="Dana")
        assert board_mail.notify_decision(item, "Vendor estimate / bid", 2, "Willow Creek") == 1
