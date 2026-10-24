"""Nothing to learn: the inbox home, one-click email actions, magic-link login, plain labels, ask on every page."""
import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import AuditLog, BoardMember, WorkItem
from app.services import board_mail, decisions, magic


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


def _member(client, name="Dana Whitfield", role="treasurer", email="treasurer@willowcreek.example", signer=True):
    with client.application.app_context():
        m = BoardMember(community_id="1001", name=name, role=role, email=email, signer=signer)
        db.session.add(m)
        db.session.commit()
        return m.id


def test_home_is_the_inbox(client):
    client.post("/login/board")
    client.post("/board/decisions/new", data={"decision_type": "bid", "title": "Award asphalt bid", "amount": "18500", "body": "three bids"})
    r = client.get("/board/")
    assert r.status_code == 200
    assert b"Needs you" in r.data and b"Award asphalt bid" in r.data and b"Your first month" in r.data
    assert b'id="dec-' in r.data  # the vote's drawer is inline on the home page
    assert b"Bills</a>" in r.data and b"Votes</a>" in r.data and b"Owners behind</a>" in r.data
    assert b"GL account" not in r.data and b"(memo)" not in r.data
    assert b'id="ask-drawer"' in r.data and b"Page: " in r.data
    client.post("/board/hide-firsts")
    assert b"Your first month" not in client.get("/board/").data


def test_one_click_approve_from_email_is_idempotent(client):
    mid = _member(client)
    with client.application.test_request_context():
        m = db.session.get(BoardMember, mid)
        url = magic.action_url("invoice", "inv-5101", "approve", m)
        login = magic.login_url(m)
    path = url.split("http://localhost", 1)[1]
    r = client.get(path)
    assert r.status_code == 200 and b"Approved" in r.data and b"of 2 approvals" in r.data
    assert AuditLog.query.filter_by(actor="Dana Whitfield", action="invoice.approve", target="inv-5101").count() == 1
    r = client.get(path)
    assert b"already" in r.data and AuditLog.query.filter_by(actor="Dana Whitfield", action="invoice.approve").count() == 1
    # the login link signs in as that member, no password
    r = client.get(login.split("http://localhost", 1)[1])
    assert r.status_code == 302 and r.headers["Location"].endswith("/board/dashboard")
    with client.session_transaction() as s:
        assert s["role"] == "board" and s["user"]["name"] == "Dana Whitfield"
    assert b"Hey, Dana." in client.get("/board/").data


def test_one_click_vote_and_bad_links(client):
    mid = _member(client)
    client.post("/login/board")
    client.post("/board/decisions/new", data={"decision_type": "transfer", "title": "Move $5,000", "amount": "5000", "body": "x"})
    d = WorkItem.query.filter_by(kind="decision").first()
    with client.application.test_request_context():
        m = db.session.get(BoardMember, mid)
        url = magic.action_url("decision", d.id, "approve", m)
    client.get("/logout")
    r = client.get(url.split("http://localhost", 1)[1])
    assert r.status_code == 200 and b"you voted approve" in r.data
    votes = db.session.get(WorkItem, d.id).remote_ids["votes"]
    assert len(votes) == 1 and votes[0]["member"] == "Dana Whitfield"
    assert client.get("/go/not-a-token").status_code == 400
    assert client.get("/login/magic/not-a-token").status_code == 302


def test_emails_go_out_when_a_decision_or_bill_appears(client):
    _member(client)
    _member(client, name="Luis Castillo", role="president", email="luis@willowcreek.example")
    with client.application.test_request_context():
        item = decisions.create("1001", "bid", "Award fence bid", "two bids", amount=9000, requested_by="Dana")
        assert board_mail.notify_decision(item, "Vendor estimate / bid", 2, "Willow Creek") == 2
        from app.integrations.registry import get_provider
        inv = get_provider().list_invoices("1001", status="pending_board")[0]
        assert board_mail.notify_invoice("1001", inv, [("ok", "Coded")], "Willow Creek") == 2


def test_email_me_a_link_is_quiet_about_unknown_addresses(client):
    _member(client)
    r = client.post("/login/email", data={"email": "treasurer@willowcreek.example"}, follow_redirects=True)
    assert b"a link is on its way" in r.data
    r = client.post("/login/email", data={"email": "nobody@example.com"}, follow_redirects=True)
    assert b"a link is on its way" in r.data
