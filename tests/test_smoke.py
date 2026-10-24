"""Every route renders. Run: pytest -q"""
import pytest

from app import create_app
from app.config import TestConfig

MARKETING = [
    "/", "/pricing", "/services", "/services/accounting", "/services/back-office", "/services/collections",
    "/how-it-works", "/self-managed", "/compare", "/reviews", "/about", "/faq", "/blog",
    "/blog/myth-of-full-service-management", "/homeowners", "/realtors", "/quote", "/contact", "/privacy", "/terms", "/brand", "/login",
    "/login/homeowner", "/login/board", "/api/health", "/api/provider/ping", "/sitemap.xml", "/robots.txt", "/quote?plan=back-office", "/sample-packet", "/c/willow-creek", "/c/willow-creek.json", "/c/willow-creek/records-request", "/.well-known/hey-agent.json",
]
HOMEOWNER = ["/me/dashboard", "/me/pay", "/me/ledger", "/me/requests", "/me/requests/new", "/me/arc", "/me/arc/new", "/me/documents", "/me/directory", "/me/profile", "/me/ask"]
OPS = ["/ops/dashboard", "/ops/review", "/ops/queue?state=open", "/ops/threads", "/ops/new", "/ops/agents", "/ops/activity", "/ops/settings"]
BOARD = ["/board/dashboard", "/board/financials", "/board/invoices", "/board/invoices?status=pending_board", "/board/delinquencies", "/board/delinquencies?draft=ua-1003",
         "/board/owners", "/board/requests", "/board/arc", "/board/violations", "/board/documents", "/board/vendors", "/board/announcements", "/board/meetings", "/board/budget", "/board/settings", "/board/ask", "/board/activity"]


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


@pytest.mark.parametrize("path", MARKETING)
def test_marketing_pages(client, path):
    assert client.get(path).status_code == 200


def test_portals_require_login(client):
    assert client.get("/me/dashboard").status_code == 302
    assert client.get("/board/dashboard").status_code == 302


@pytest.mark.parametrize("path", HOMEOWNER)
def test_homeowner_pages(client, path):
    client.post("/login/homeowner")
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", BOARD)
def test_board_pages(client, path):
    client.post("/login/board")
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", OPS)
def test_ops_pages(client, path):
    client.post("/login/ops")
    assert client.get(path).status_code == 200


def test_role_isolation(client):
    client.post("/login/homeowner")
    assert client.get("/board/dashboard").status_code == 403
    assert client.get("/ops/dashboard").status_code == 403


def test_quote_creates_lead(client):
    client.get("/?utm_source=reddit&utm_medium=post&utm_campaign=launch")
    r = client.post("/quote", data={"community_name": "Test HOA", "community_type": "hoa", "units": "48", "state": "az", "current_setup": "self",
                                    "pain_points": ["late financials"], "contact_name": "A", "contact_role": "treasurer", "email": "a@b.co", "plan": "back-office"})
    assert r.status_code == 302
    from app.models import Lead
    lead = Lead.query.filter_by(community_name="Test HOA").first()
    assert lead and lead.score >= 75 and lead.plan == "back-office" and lead.utm_source == "reddit" and lead.source == "reddit"


def test_quote_honeypot_drops_bots(client):
    from app.models import Lead
    client.get("/quote")
    before = Lead.query.count()
    r = client.post("/quote", data={"community_name": "Bot HOA", "website": "http://spam", "email": "x@y.z"})
    assert r.status_code == 302 and Lead.query.count() == before


def test_quote_rate_limit(client):
    from app.blueprints.marketing import routes
    routes._RATE.clear()
    for i in range(5):
        client.post("/quote", data={"community_name": f"HOA {i}", "email": "a@b.co"})
    r = client.post("/quote", data={"community_name": "HOA 6", "email": "a@b.co"}, follow_redirects=True)
    assert b"Too many submissions" in r.data
    routes._RATE.clear()


def test_sitemap_and_robots(client):
    s = client.get("/sitemap.xml")
    assert s.status_code == 200 and b"/pricing" in s.data and b"/blog/" in s.data
    r = client.get("/robots.txt")
    assert b"Disallow: /board/" in r.data and b"Sitemap:" in r.data


def test_invoice_approval_flow(client):
    client.post("/login/board")
    r = client.post("/board/invoices/inv-5102/approve", follow_redirects=True)
    assert b"1/2 approvals" in r.data
    r = client.post("/board/invoices/inv-5102/approve", follow_redirects=True)
    assert b"2/2 approvals" in r.data


def test_ask_demo_mode(client):
    client.post("/login/homeowner")
    r = client.post("/api/ask", json={"q": "can I build a fence?"})
    assert r.status_code == 200 and "ARC" in r.get_json()["answer"]
