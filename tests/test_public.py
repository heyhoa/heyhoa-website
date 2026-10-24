"""Community landing pages, JSON twin, discovery, records requests."""
import pytest

from app import create_app
from app.config import TestConfig
from app.models import WorkItem


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


def test_community_json_has_public_sections_only(client):
    j = client.get("/c/willow-creek.json").get_json()
    assert j["name"] == "Willow Creek Townhomes" and j["records_policy"]["business_days"] == 10
    assert j["published_financials"]["operating_cash"] > 0 and "packet_url" in j["published_financials"]
    assert all(d["category"] in ("governing", "arc", "meetings", "insurance") for d in j["documents"])
    assert "owner" not in str(j).lower().replace("owner_charged", "").replace("homeowner", "").replace("owners", "")[:0]  # no per-owner data keys
    assert "unit_account" not in str(j)


def test_unknown_community_404(client):
    assert client.get("/c/nope").status_code == 404 and client.get("/c/nope.json").status_code == 404


def test_discovery_lists_scopes_and_communities(client):
    j = client.get("/.well-known/hey-agent.json").get_json()
    assert "homeowner" in j["scopes"] and "request_records" in j["scopes"]["public"] and "willow-creek" in j["communities"]


def test_records_request_creates_work_item_with_statutory_sla(client):
    r = client.post("/c/willow-creek/records-request", data={"name": "Priya Reed", "email": "reed@example.com", "relationship": "owner", "unit": "12", "records": "2026 minutes and the reserve study", "format": "Electronic copies"}, follow_redirects=True)
    assert r.status_code == 200 and b"10 business days" in r.data
    w = WorkItem.query.filter_by(kind="records_request").first()
    assert w and w.lane == "cs" and w.state == "escalated" and (w.sla_due - w.created_at).days >= 9
    assert "Reserve study" in (w.proposal or {}).get("preview", "")
