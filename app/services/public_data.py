"""What a community publishes: the landing page, its JSON twin, and agent discovery.

Boards choose what is public. Defaults: governing documents, fee schedule,
meeting notices, records policy. Financial summary and packet are opt-in.
Nothing per-owner is ever public.
"""
from __future__ import annotations

from flask import current_app, url_for

from .. import brand
from ..integrations.registry import get_provider

SLUGS = {"willow-creek": "1001", "apache-wells": "1002"}
PUBLISH_DEFAULTS = {"documents": True, "fees": True, "meetings": True, "records_policy": True, "financial_summary": True, "packet": False, "board_names": False}

RECORDS_POLICY = {
    "AZ": {"statute": "A.R.S. § 33-1258 (condominium) / § 33-1805 (planned community)", "business_days": 10, "copy_fee_per_page": 0.15, "who": "members and their agents", "exclusions": "privileged communications, pending litigation, personal owner records, job applications"},
    "TX": {"statute": "Tex. Prop. Code § 209.005", "business_days": 10, "copy_fee_per_page": 0.10, "who": "owners and their agents", "exclusions": "per the association's records production and copying policy"},
}


def slug_for(community_id: str) -> str | None:
    return next((s for s, c in SLUGS.items() if c == str(community_id)), None)


def _plans():
    from . import plans

    return plans


def community_public(slug: str) -> dict | None:
    cid = SLUGS.get(slug)
    if not cid:
        return None
    p = get_provider()
    c = p.get_community(cid)
    pub = dict(PUBLISH_DEFAULTS)
    docs = [{"id": d.id, "title": d.title, "category": d.category, "date": d.date} for d in p.list_documents(cid) if not d.board_only and d.category in ("governing", "arc", "meetings", "insurance")] if pub["documents"] else []
    snap = p.get_financial_snapshot(cid) if pub["financial_summary"] else None
    return {
        "slug": slug, "id": cid, "name": c.name, "type": c.kind, "units": c.units, "city": c.city, "state": c.state, "fiscal_year_end": c.fiscal_year_end, "dues_frequency": c.dues_frequency,
        "managed_by": {"name": brand.BRAND["name"], "email": brand.BRAND["email"], "phone": brand.BRAND["phone"], "role": "accounting and back office; the board governs"},
        "how_to_pay": {"portal": url_for("auth.login_role", role="homeowner", _external=True), "methods": ["ACH autopay (free)", "card (2.9% + 30¢)", "bank bill pay to lockbox", "check to lockbox"]},
        "how_to_file": {"service_request": url_for("auth.login_role", role="homeowner", _external=True), "arc_request": url_for("auth.login_role", role="homeowner", _external=True), "records_request": url_for("marketing.records_request", slug=slug, _external=True), "contact_board": url_for("marketing.contact", _external=True)},
        "fees": {"owner_charged": brand.OWNER_FEES, "association_items": brand.ASSOCIATION_FEES} if pub["fees"] else None,
        "collection_policy": {"stages": [{"key": k, "days": d, "label": l, "fee": f} for k, d, l, f in brand.COLLECTION_STAGES], "lien_threshold": brand.LIEN_THRESHOLD} if pub["fees"] else None,
        "documents": docs,
        "who_fixes_what": [{"item": r.item, "who": r.party, "note": r.note or ""} for r in _plans().responsibilities(cid)],
        "projects": [{"name": x.name, "status": x.status, "year": x.year, "cost": x.cost} for x in _plans().projects(cid) if x.status != "completed"],
        "published_financials": ({"as_of": snap.as_of, "operating_cash": snap.operating_cash, "reserve_cash": snap.reserve_cash, "reserve_funded_pct": 82, "ytd_income": snap.ytd_income, "ytd_expense": snap.ytd_expense, "last_packet_date": snap.last_packet_date, "packet_url": None} if snap else None),
        "records_policy": RECORDS_POLICY.get(c.state) if pub["records_policy"] else None,
        "meetings": [{"date": "2026-11-12", "time": "19:00", "where": "Clubhouse + Zoom", "kind": "board", "notice_sent": "2026-10-28"}] if pub["meetings"] else [],
        "agent": {"discovery": url_for("marketing.agent_discovery", _external=True), "mcp": current_app.config.get("MCP_PUBLIC_URL", "https://mcp.heyhoa.com/mcp"), "scopes": ["public", "homeowner", "board", "vendor", "realtor"]},
    }


def discovery() -> dict:
    return {
        "name": brand.BRAND["name"], "description": brand.BRAND["one_liner"], "version": "0.1",
        "mcp": {"url": current_app.config.get("MCP_PUBLIC_URL", "https://mcp.heyhoa.com/mcp"), "transport": "streamable-http", "auth": "bearer token issued in the portal (Settings → Connect your assistant); public tools need no token"},
        "scopes": {
            "public": ["community_profile", "fee_schedule", "request_records"],
            "homeowner": ["my_account", "my_ledger", "my_statements", "my_requests", "community_documents", "search_rules", "payment_link", "set_autopay", "request_payment_plan", "file_service_request", "submit_arc_request", "request_records", "message_board", "update_contact"],
            "board": ["financials", "pending_approvals", "pending_decisions", "vote_decision", "delinquencies", "vendors", "approve_invoice", "decide_arc", "draft_announcement", "plus every homeowner tool"],
            "vendor": ["payment_status", "submit_invoice"],
            "realtor": ["community_profile", "fee_schedule", "order_resale_package"],
        },
        "communities": {s: url_for("marketing.community_json", slug=s, _external=True) for s in SLUGS},
        "policy": "Every write becomes a reviewed work item. Money actions always involve a person. Agents are treated exactly like the person they act for.",
    }
