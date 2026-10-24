"""MCP server: scopes, reads, writes become work items."""
import pytest

from app import mcp_server
from app.config import TestConfig
from app.mcp_server import Persona


@pytest.fixture(autouse=True)
def fresh_app(monkeypatch):
    from app import create_app

    mcp_server._app = create_app(TestConfig)
    yield
    mcp_server._app = None


def _ok(result):
    assert not getattr(result, "isError", False), result
    return result.structuredContent if getattr(result, "structuredContent", None) else result.content[0].text


def test_public_tools_need_no_token():
    mcp_server.set_default_persona(Persona())
    r = _ok(mcp_server.call("community_profile", slug="willow-creek"))
    assert "Willow Creek" in str(r) and "records_policy" in str(r)
    assert "owner_charged" in str(_ok(mcp_server.call("fee_schedule")))


def test_homeowner_scope_reads_and_writes():
    mcp_server.set_default_persona(Persona(role="homeowner", community_id="1001", unit_account_id="ua-1012", name="Marcus Reed", email="reed@example.com"))
    acct = _ok(mcp_server.call("my_account"))
    assert "ua-1012" in str(acct) and "Willow Creek" in str(acct)
    ans = _ok(mcp_server.call("search_rules", question="can I build a fence?"))
    assert "ARC" in str(ans)
    w = _ok(mcp_server.call("request_payment_plan", months=3))
    assert "work_item" in str(w) and ("proposed" in str(w) or "escalated" in str(w) or "done" in str(w))
    from app.models import WorkItem
    with mcp_server.app().app_context():
        item = WorkItem.query.filter_by(kind="portal_form").order_by(WorkItem.id.desc()).first()
        assert item.lane == "ar" and item.proposal["action"] == "create_payment_plan"


def test_homeowner_cannot_use_board_tools():
    mcp_server.set_default_persona(Persona(role="homeowner", community_id="1001", unit_account_id="ua-1012"))
    with pytest.raises(Exception) as e:
        mcp_server.call("financials")
    assert "needs one of" in str(e.value.__cause__ or e.value)


def test_board_scope_approves_invoice_and_sees_owner_tools():
    mcp_server.set_default_persona(Persona(role="board", community_id="1001", unit_account_id="ua-1021", contact_id="cc-7", name="Dana Whitfield"))
    pend = _ok(mcp_server.call("pending_approvals"))
    assert "inv-5103" in str(pend)
    r = _ok(mcp_server.call("approve_invoice", invoice_id="inv-5103", action="approve"))
    assert "2/2" in str(r) and "approved" in str(r)
    assert "ua-1021" in str(_ok(mcp_server.call("my_account")))


def test_records_request_via_mcp_sets_statutory_clock():
    mcp_server.set_default_persona(Persona())
    r = _ok(mcp_server.call("request_records", slug="willow-creek", name="A", email="a@b.co", relationship="owner", records="minutes"))
    assert "respond_by" in str(r) and "business_days" in str(r)


def test_tools_listed_match_discovery():
    import asyncio
    names = {t.name for t in asyncio.run(mcp_server.server.list_tools())}
    for n in ("community_profile", "my_account", "approve_invoice", "submit_invoice", "order_resale_package", "request_records"):
        assert n in names
