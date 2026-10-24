"""hey hoa MCP server: the same capabilities as the portals, for the person's own agent.

Run:  python -m app.mcp_server                 (stdio; persona from HEY_MCP_DEFAULT_PERSONA)
      MCP_TRANSPORT=streamable-http python -m app.mcp_server   (HTTP on MCP_PORT, bearer tokens)

Tokens: HEY_MCP_TOKENS="tok1:homeowner:1001:ua-1012:Marcus Reed,tok2:board:1001:cc-7:Dana Whitfield"
Every write becomes a work item in hey ops and goes through the agent lanes
and the review policy, exactly as if the person had used the portal.
"""
from __future__ import annotations

import asyncio
import contextvars
import inspect
import os
from dataclasses import dataclass
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.mcpserver import MCPServer

from . import brand
from .ai import assistant

SCOPES = {"public": 0, "realtor": 1, "vendor": 1, "homeowner": 2, "board": 3}


@dataclass
class Persona:
    role: str = "public"
    community_id: str | None = None
    unit_account_id: str | None = None
    contact_id: str | None = None
    name: str = "anonymous"
    email: str = ""


_default_persona: contextvars.ContextVar[Persona] = contextvars.ContextVar("hey_persona", default=Persona())
_app = None


def set_default_persona(p: Persona) -> None:
    _default_persona.set(p)


def _tokens() -> dict[str, Persona]:
    out = {}
    for raw in os.environ.get("HEY_MCP_TOKENS", "").split(","):
        parts = raw.strip().split(":")
        if len(parts) >= 2:
            tok, role = parts[0], parts[1]
            out[tok] = Persona(role=role, community_id=parts[2] if len(parts) > 2 else None, unit_account_id=parts[3] if len(parts) > 3 and parts[3] else None, contact_id=parts[3] if len(parts) > 3 else None, name=parts[4] if len(parts) > 4 else role)
    return out


class StaticTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        p = _tokens().get(token)
        if not p:
            return None
        return AccessToken(token=token, client_id=p.name, scopes=[p.role], expires_at=None)


def current_persona() -> Persona:
    try:
        from mcp.server.auth.middleware.auth_context import get_access_token

        at = get_access_token()
        if at is not None:
            p = _tokens().get(at.token)
            if p:
                return p
    except Exception:  # noqa: BLE001
        pass
    return _default_persona.get()


def app():
    global _app
    if _app is None:
        from . import create_app

        _app = create_app()
    return _app


def require(*roles: str):
    """Tool decorator: run inside the Flask app context with a persona of the required role."""

    def deco(fn):
        sig = inspect.signature(fn)
        public_params = [prm for name, prm in sig.parameters.items() if name != "p"]

        def wrapper(*a, **kw):
            p = current_persona()
            allowed = not roles or p.role in roles or (p.role == "board" and "homeowner" in roles)
            if not allowed:
                raise PermissionError(f"This tool needs one of {roles}; your token is '{p.role}'.")
            with app().test_request_context():
                return fn(p, *a, **kw)

        wrapper.__name__, wrapper.__doc__, wrapper.__module__ = fn.__name__, fn.__doc__, fn.__module__
        wrapper.__signature__ = sig.replace(parameters=public_params)  # MCP sees only the caller's inputs
        wrapper.__annotations__ = {k: v for k, v in getattr(fn, "__annotations__", {}).items() if k != "p"}
        return wrapper

    return deco


server = MCPServer(
    name="hey hoa",
    instructions=(
        "hey hoa is the accounting and back office for self-managed HOAs and condos. Tools act for the person who issued your token (owner, board member, vendor or closing party). "
        "Reads are immediate. Writes create a reviewed work item and return its id and state; money actions always involve a person. Ask for the community slug when a public tool needs it."
    ),
)

# ---------------------------------------------------------------------------
# public (no token)
# ---------------------------------------------------------------------------
@server.tool(description="Public profile of a community served by hey: how to pay, how to file, documents, published financials, records policy.")
@require()
def community_profile(p, slug: str) -> dict:
    from .services.public_data import community_public

    return community_public(slug) or {"error": "unknown community"}


@server.tool(description="Fee schedule: what owners are charged for (collections, resale, lender docs) and what is inside the flat fee.")
@require()
def fee_schedule(p) -> dict:
    return {"owner_charged": brand.OWNER_FEES, "association_items": brand.ASSOCIATION_FEES, "tiers": brand.PRICING, "collection_ladder": brand.COLLECTION_STAGES, "lien_threshold": brand.LIEN_THRESHOLD}


@server.tool(description="File a statutory records request with a community. Creates a reviewed work item; the association responds within the statutory clock.")
@require()
def request_records(p, slug: str, name: str, email: str, relationship: str, records: str, unit: str = "") -> dict:
    from .agents import runtime
    from .services.public_data import community_public

    c = community_public(slug)
    if not c:
        return {"error": "unknown community"}
    item = runtime.inbound_portal(community_id=c["id"], unit_account_id=p.unit_account_id, kind="records_request", subject=f"Records request from {name}", body=f"Records requested: {records}\nRequester: {relationship} of {unit or 'unspecified unit'}", email=email, name=name, lane="cs")
    return {"work_item": item.id, "state": item.state, "statutory_clock": c.get("records_policy"), "respond_by": item.sla_due.isoformat()}


# ---------------------------------------------------------------------------
# homeowner
# ---------------------------------------------------------------------------
@server.tool(description="The owner's account: balance, next assessment, autopay status, unit and community.")
@require("homeowner")
def my_account(p) -> dict:
    from .integrations.registry import get_provider

    ua = get_provider().get_unit_account(p.unit_account_id)
    c = get_provider().get_community(ua.community_id)
    return {**ua.__dict__, "community": c.name, "dues_frequency": c.dues_frequency}


@server.tool(description="The owner's ledger lines (charges and payments) with running balance.")
@require("homeowner")
def my_ledger(p, limit: int = 24) -> dict:
    from .integrations.registry import get_provider

    return {"lines": [l.__dict__ for l in get_provider().get_ledger(p.unit_account_id)[:limit]]}


@server.tool(description="Who fixes what: is a building part (roof, window, patio gate, water line) the owner's or the association's responsibility, per the board's chart, with its source.")
@require("homeowner")
def who_fixes_what(p, item: str = "") -> dict:
    from .services import plans

    rows = plans.who_fixes(p.community_id, item) if item else plans.responsibilities(p.community_id)
    return {"items": [{"item": r.item, "who": r.party, "note": r.note or ""} for r in rows], "published": bool(plans.responsibilities(p.community_id))}


@server.tool(description="The community's project list: what is planned, in progress or done, with cost, year and status.")
@require("homeowner")
def community_projects(p) -> dict:
    from .services import plans

    return {"projects": [{"name": x.name, "status": x.status, "year": x.year, "cost": x.cost, "what": x.description or ""} for x in plans.projects(p.community_id)]}


@server.tool(description="Monthly statements available for the owner.")
@require("homeowner")
def my_statements(p) -> dict:
    from .integrations.registry import get_provider

    return {"statements": [s.__dict__ for s in get_provider().get_statements(p.unit_account_id)]}


@server.tool(description="The owner's open and recent maintenance requests, ARC applications and work items.")
@require("homeowner")
def my_requests(p) -> dict:
    from .integrations.registry import get_provider
    from .models import WorkItem

    prov = get_provider()
    items = WorkItem.query.filter_by(unit_account_id=p.unit_account_id).order_by(WorkItem.created_at.desc()).limit(20).all()
    return {"maintenance": [r.__dict__ for r in prov.list_service_requests(p.community_id, p.unit_account_id)], "arc": [a.__dict__ for a in prov.list_arc_requests(p.community_id, p.unit_account_id)],
            "work_items": [{"id": w.id, "kind": w.kind, "subject": w.subject, "state": w.state, "outcome": w.outcome, "created": w.created_at.isoformat()} for w in items]}


@server.tool(description="Governing documents, rules, meeting records and financial documents the owner may see.")
@require("homeowner")
def community_documents(p) -> dict:
    from .integrations.registry import get_provider

    return {"documents": [d.__dict__ for d in get_provider().list_documents(p.community_id, board=(p.role == "board"))]}


@server.tool(description="Ask a question about the community's rules, policies or the owner's account. Answers cite their source; unsourced questions are routed to a person.")
@require("homeowner")
def search_rules(p, question: str) -> dict:
    answer = assistant.ask(question, role=p.role, user={"community_id": p.community_id, "unit_account_id": p.unit_account_id, "name": p.name})
    return {"answer": answer, "note": "If the answer says it is routing to a person, a work item was created and a reply will come by email."}


@server.tool(description="Hosted payment page link for this owner's account (card or ACH). Nothing is charged until the owner completes it.")
@require("homeowner")
def payment_link(p, amount: float | None = None) -> dict:
    from .integrations.registry import get_provider

    res = get_provider().post_payment  # not called; hosted redirect in production
    ua = get_provider().get_unit_account(p.unit_account_id)
    with app().test_request_context():
        from flask import url_for

        url = url_for("homeowner.pay", _external=True)
    return {"url": url, "balance": ua.balance, "suggested_amount": amount or (ua.balance if ua.balance > 0 else ua.next_due_amount), "methods": ["ACH (free)", "card (2.9% + 30¢)"]}


def _write(p, kind: str, subject: str, body: str, lane: str = "cs") -> dict:
    from .agents import runtime

    item = runtime.inbound_portal(community_id=p.community_id, unit_account_id=p.unit_account_id, kind=kind, subject=subject, body=body, email=p.email, name=p.name, lane=lane)
    return {"work_item": item.id, "state": item.state, "lane": item.lane, "proposal": (item.proposal or {}).get("action"), "preview": (item.proposal or {}).get("preview", "")[:600], "note": "Executed" if item.state == "done" else "Waiting for a person to approve" if item.state == "proposed" else "Routed to a person"}


@server.tool(description="Turn autopay on or off for the owner's assessments (ACH). Creates a reviewed request.")
@require("homeowner")
def set_autopay(p, enabled: bool, day_of_month: int = 1) -> dict:
    return _write(p, "portal_form", f"Autopay {'on' if enabled else 'off'}", f"Owner requests autopay {'enabled' if enabled else 'disabled'} on day {day_of_month} of the month via their assistant.", lane="ar")


@server.tool(description="Request a payment plan within policy (up to 6 months, $75 setup fee).")
@require("homeowner")
def request_payment_plan(p, months: int) -> dict:
    return _write(p, "portal_form", "Payment plan request", f"Owner requests a payment plan over {months} months via their assistant.", lane="ar")


@server.tool(description="File a maintenance request for a common-area issue.")
@require("homeowner")
def file_service_request(p, summary: str, category: str = "") -> dict:
    return _write(p, "portal_form", f"Maintenance: {category or 'auto'}", summary, lane="cs")


@server.tool(description="Submit an architectural (ARC) application for an exterior change.")
@require("homeowner")
def submit_arc_request(p, request_type: str, description: str) -> dict:
    from .agents import runtime
    from .integrations.registry import get_provider

    arc = get_provider().create_arc_request(p.community_id, p.unit_account_id, request_type, description)
    item = runtime.inbound_portal(community_id=p.community_id, unit_account_id=p.unit_account_id, kind="arc", subject=f"ARC: {request_type}", body=f"Application {arc.id} submitted via assistant: {description}", email=p.email, name=p.name, lane="cs")
    return {"application": arc.id, "status": arc.status, "approvals_required": arc.approvals_required, "work_item": item.id}


@server.tool(description="Send a message to the board through hey (logged, routed, answered).")
@require("homeowner")
def message_board(p, subject: str, body: str) -> dict:
    return _write(p, "email", subject, body, lane="cs")


@server.tool(description="Update the owner's contact email or phone on file.")
@require("homeowner")
def update_contact(p, email: str = "", phone: str = "") -> dict:
    return _write(p, "portal_form", "Contact update", f"Owner asks to update contact info: email={email or '-'} phone={phone or '-'}", lane="cs")


# ---------------------------------------------------------------------------
# board
# ---------------------------------------------------------------------------
@server.tool(description="Financial snapshot for the board: cash, reserves, AR, AP pending, YTD vs budget, reconciliation status.")
@require("board")
def financials(p) -> dict:
    from .integrations.registry import get_provider

    return get_provider().get_financial_snapshot(p.community_id).__dict__


@server.tool(description="Everything waiting on the board: invoices to approve (with hey's notes) and ARC items.")
@require("board")
def pending_approvals(p) -> dict:
    from .integrations.registry import get_provider

    prov = get_provider()
    return {"invoices": [i.__dict__ for i in prov.list_invoices(p.community_id, status="pending_board")], "arc": [a.__dict__ for a in prov.list_arc_requests(p.community_id) if a.status in ("submitted", "under_review")]}


@server.tool(description="Delinquent accounts with stage, days and next action under the collection policy.")
@require("board")
def delinquencies(p) -> dict:
    from .integrations.registry import get_provider

    return {"rows": [d.__dict__ for d in get_provider().list_delinquencies(p.community_id)]}


@server.tool(description="Vendors with W-9 and insurance status and YTD paid.")
@require("board")
def vendors(p) -> dict:
    from .integrations.registry import get_provider

    return {"vendors": [v.__dict__ for v in get_provider().list_vendors(p.community_id)]}


@server.tool(description="Record this board member's decision on an invoice: approve, hold or reject. Two approvals release a payment; the accountant disburses.")
@require("board")
def approve_invoice(p, invoice_id: str, action: str, note: str = "") -> dict:
    from .extensions import db
    from .integrations.registry import get_provider
    from .models import AuditLog

    if action not in ("approve", "reject", "hold"):
        return {"error": "action must be approve, reject or hold"}
    inv = get_provider().act_on_invoice(invoice_id, p.contact_id or p.name, action, note)
    db.session.add(AuditLog(actor=f"{p.name} (via assistant)", action=f"invoice.{action}", target=invoice_id, detail=f"{inv.vendor} {inv.number} ${inv.amount:,.2f}"))
    db.session.commit()
    return {"invoice": inv.id, "status": inv.status, "approvals": f"{inv.approvals}/{inv.approvals_required}"}


@server.tool(description="Record this committee member's ARC decision: approve, deny or more_info, citing the rule.")
@require("board")
def decide_arc(p, arc_id: str, action: str, note: str = "") -> dict:
    from .extensions import db
    from .integrations.registry import get_provider
    from .models import AuditLog

    a = get_provider().act_on_arc(arc_id, p.contact_id or p.name, action, note)
    db.session.add(AuditLog(actor=f"{p.name} (via assistant)", action=f"arc.{action}", target=arc_id, detail=a.request_type))
    db.session.commit()
    return {"application": a.id, "status": a.status, "approvals": f"{a.approvals}/{a.approvals_required}"}


@server.tool(description="Decisions waiting on the board beyond invoices (transfers, bids, work orders, policies) with votes so far.")
@require("board")
def pending_decisions(p) -> dict:
    from .services import decisions

    return {"decisions": [{"id": d.id, "type": d.category, "label": decisions.spec(d.category, p.community_id)["label"], "title": d.subject, "details": d.summary, "approvals_needed": decisions.spec(d.category, p.community_id)["approvals"], "votes": (d.remote_ids or {}).get("votes", [])} for d in decisions.pending(p.community_id)]}


@server.tool(description="Record this board member's vote on a decision: approve, deny or abstain, with an optional note.")
@require("board")
def vote_decision(p, decision_id: int, vote: str, note: str = "") -> dict:
    from .extensions import db
    from .models import WorkItem
    from .services import decisions

    item = db.session.get(WorkItem, decision_id)
    if not item or item.community_id != p.community_id or item.kind != "decision":
        return {"error": "unknown decision"}
    if vote not in ("approve", "deny", "abstain"):
        return {"error": "vote must be approve, deny or abstain"}
    decisions.vote(item, p.contact_id or p.name, p.name, vote, note)
    return {"decision": item.id, "state": item.state, "outcome": item.outcome, "votes": item.remote_ids.get("votes", [])}


@server.tool(description="Have hey draft an owner announcement from a brief; it is queued for a board member to send.")
@require("board")
def draft_announcement(p, brief: str) -> dict:
    from .integrations.registry import get_provider

    d = assistant.draft_announcement(brief, get_provider().get_community(p.community_id))
    res = _write(p, "decision", f"Announcement draft: {d['title']}", d["body"], lane="board")
    return {**d, **res}


# ---------------------------------------------------------------------------
# vendor
# ---------------------------------------------------------------------------
@server.tool(description="Submit an invoice to a community for coding and board approval.")
@require("vendor")
def submit_invoice(p, community_slug: str, number: str, amount: float, description: str, due_date: str = "") -> dict:
    from .services.public_data import SLUGS

    cid = SLUGS.get(community_slug)
    if not cid:
        return {"error": "unknown community"}
    pp = Persona(role="vendor", community_id=cid, name=p.name, email=p.email)
    return _write(pp, "invoice", f"Invoice {p.name} {number} · ${amount:,.2f}", f"{description}\nAmount ${amount:,.2f} · due {due_date or 'net 30'}", lane="ap")


@server.tool(description="Payment status of this vendor's invoices across communities served by hey.")
@require("vendor")
def payment_status(p) -> dict:
    from .integrations.registry import get_provider

    rows = [i.__dict__ for i in get_provider().list_invoices("1001") if p.name.lower() in i.vendor.lower()]
    return {"invoices": rows}


# ---------------------------------------------------------------------------
# realtor / lender / title
# ---------------------------------------------------------------------------
@server.tool(description="Order a resale / disclosure package for a closing. Fee paid by the requester; delivered in 3 business days.")
@require("realtor")
def order_resale_package(p, community_slug: str, unit: str, closing_date: str, requester_email: str, rush: bool = False) -> dict:
    from .services.public_data import SLUGS

    cid = SLUGS.get(community_slug)
    if not cid:
        return {"error": "unknown community"}
    pp = Persona(role="realtor", community_id=cid, name=p.name, email=requester_email)
    res = _write(pp, "resale_order", f"Resale package: {unit} closing {closing_date}", f"Resale/disclosure package ordered via assistant for {unit}, closing {closing_date}. Rush: {rush}.", lane="cs")
    return {**res, "fee": "$275" + (" + $100 rush" if rush else ""), "turnaround": "1 business day" if rush else "3 business days"}


def call(tool_name: str, /, **arguments):
    """In-process helper for tests and scripts (positional tool name so it never collides with tool args)."""
    return asyncio.run(server.call_tool(tool_name, arguments))


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    raw = os.environ.get("HEY_MCP_DEFAULT_PERSONA", "")
    if raw:
        parts = raw.split(":")
        set_default_persona(Persona(role=parts[0], community_id=parts[1] if len(parts) > 1 else None, unit_account_id=parts[2] if len(parts) > 2 else None, contact_id=parts[2] if len(parts) > 2 else None, name=parts[3] if len(parts) > 3 else parts[0]))
    if transport == "streamable-http":
        import uvicorn

        server_app = server.streamable_http_app(host="0.0.0.0")
        uvicorn.run(server_app, host="0.0.0.0", port=int(os.environ.get("MCP_PORT", "8765")))
    else:
        server.run("stdio")


if __name__ == "__main__":
    main()
