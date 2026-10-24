"""Tools shared across lanes. Each returns a JSON-serialisable dict.

`item` is always passed (the WorkItem being worked) so tools can log and
attach messages; keyword arguments match the tool's input_schema.
"""
from __future__ import annotations

import datetime as dt

from flask import current_app

from .. import brand
from ..ai import assistant
from ..channels import email as email_channel
from ..channels import sms as sms_channel
from ..extensions import db
from ..integrations.registry import get_provider
from ..models import AuditLog, Message, WorkItem
from .base import RISK_MONEY, RISK_READ, RISK_SEND, RISK_WRITE, Tool


def _p():
    return get_provider()


def _log(item, action, detail=""):
    db.session.add(AuditLog(actor="hey", action=action, target=f"wi:{item.id}", detail=detail[:500]))


# ---- read tools -------------------------------------------------------------
def lookup_owner(item, email: str = "", unit_account_id: str = "") -> dict:
    cid = item.community_id or "1001"
    for ua in _p().list_unit_accounts(cid):
        if (unit_account_id and ua.id == unit_account_id) or (email and (ua.email or "").lower() == email.lower()):
            return ua.__dict__
    return {"found": False}


def get_ledger(item, unit_account_id: str) -> dict:
    return {"lines": [l.__dict__ for l in _p().get_ledger(unit_account_id)[:24]], "account": _p().get_unit_account(unit_account_id).__dict__}


def get_delinquencies(item) -> dict:
    return {"rows": [d.__dict__ for d in _p().list_delinquencies(item.community_id or "1001")]}


def search_rules(item, query: str) -> dict:
    """Community brain lookup. Phase 3 replaces this with document retrieval."""
    ctx = assistant._context_for("board", {"community_id": item.community_id or "1001"})
    hits = [line for line in ctx.split("\n") if any(w in line.lower() for w in query.lower().split()[:4])]
    return {"query": query, "hits": hits[:8] or [ctx[:1200]]}


def list_invoices(item, status: str = "pending_board") -> dict:
    return {"invoices": [i.__dict__ for i in _p().list_invoices(item.community_id or "1001", status=status or None)]}


def vendor_history(item, vendor: str) -> dict:
    inv = [i.__dict__ for i in _p().list_invoices(item.community_id or "1001") if vendor.lower() in i.vendor.lower()]
    return {"vendor": vendor, "invoices": inv, "count": len(inv), "avg": (sum(i["amount"] for i in inv) / len(inv)) if inv else 0}


def list_vendors(item) -> dict:
    return {"vendors": [v.__dict__ for v in _p().list_vendors(item.community_id or "1001")]}


def list_decisions(item) -> dict:
    cid = item.community_id or "1001"
    inv = [i.__dict__ for i in _p().list_invoices(cid, status="pending_board")]
    arcs = [a.__dict__ for a in _p().list_arc_requests(cid) if a.status in ("submitted", "under_review")]
    return {"invoices": inv, "arc": arcs}


def get_financials(item) -> dict:
    return _p().get_financial_snapshot(item.community_id or "1001").__dict__


# ---- write / send / money tools --------------------------------------------
def send_email(item, to: str, subject: str, body: str) -> dict:
    res = email_channel.send(to, subject, body, tag=f"lane-{item.lane}")
    db.session.add(Message(work_item_id=item.id, direction="out", channel="email", sender=current_app.config.get("POSTMARK_FROM") or brand.BRAND["email"], recipient=to, subject=subject, body=body, author="hey", delivered=bool(res.get("delivered")), meta=res))
    _log(item, "email.sent", f"to={to} subject={subject}")
    return {"ok": True, **res}


def send_sms(item, to: str, body: str) -> dict:
    res = sms_channel.send(to, body)
    db.session.add(Message(work_item_id=item.id, direction="out", channel="sms", sender=current_app.config.get("TWILIO_FROM") or "hey", recipient=to, body=body, author="hey", delivered=bool(res.get("delivered")), meta=res))
    _log(item, "sms.sent", f"to={to}")
    return {"ok": True, **res}


def post_note(item, unit_account_id: str, text: str) -> dict:
    db.session.add(Message(work_item_id=item.id, direction="out", channel="note", recipient=unit_account_id, body=text, author="hey", delivered=True))
    _log(item, "caliber.addnote", f"ua={unit_account_id}")
    return {"ok": True, "remote": "POST /api/v2/unitaccount/{id}/addnote (simulated in mock mode)"}


def handoff(item, lane: str, note: str = "") -> dict:
    item.lane = lane if lane in ("cs", "ar", "ap", "board", "close", "onboarding", "sales") else item.lane
    item.state = "new"
    item.summary = (item.summary or "") + f"\n\n[handoff] {note}"
    _log(item, "handoff", f"to={lane} {note}")
    return {"ok": True, "lane": item.lane}


def escalate(item, lane: str = "coordinator", note: str = "") -> dict:
    item.state = "escalated"
    item.priority = "high"
    item.review_note = note
    _log(item, "escalate", f"to={lane} {note}")
    return {"ok": True, "to": lane}


def post_fine(item, unit_account_id: str, amount: float, description: str) -> dict:
    _log(item, "caliber.postfine", f"ua={unit_account_id} amount={amount} {description}")
    return {"ok": True, "remote": "POST /api/v2/postfine (simulated in mock mode)", "amount": amount}


def create_payment_plan(item, unit_account_id: str, months: int, monthly_amount: float, start_date: str = "") -> dict:
    _log(item, "caliber.achpaymentplan", f"ua={unit_account_id} {months}x{monthly_amount}")
    return {"ok": True, "remote": "POST /api/v2/unitaccount/{id}/achpaymentplan (simulated in mock mode)", "setup_fee": 75}


def send_notice(item, unit_account_id: str, stage: str, body: str, channel: str = "email", fee: float = 0) -> dict:
    ua = _p().get_unit_account(unit_account_id)
    out = send_email(item, ua.email, f"{stage.replace('_', ' ').title()} — {ua.unit_label}", body) if channel == "email" else send_sms(item, ua.phone, body[:300])
    if fee:
        post_fine(item, unit_account_id, fee, f"Collection fee: {stage.replace('_', ' ')}")
    post_note(item, unit_account_id, f"{stage} sent via {channel}; fee ${fee:,.2f}")
    return {"ok": True, "sent": out, "fee": fee}


def post_invoice(item, vendor: str, number: str, amount: float, gl_account: str, description: str, due_date: str = "") -> dict:
    _log(item, "caliber.invoice.post", f"{vendor} {number} ${amount} {gl_account}")
    return {"ok": True, "remote": "POST /api/v2/invoice (simulated in mock mode)", "queued_for_board": True}


def request_vendor_document(item, vendor_email: str, document: str, vendor_name: str = "") -> dict:
    body = f"Hi {vendor_name or 'there'},\n\nTo keep payments moving for {item.community_id and _p().get_community(item.community_id).name}, we need a current {document} on file. Reply to this email with it attached and we will take it from there.\n\nThanks,\nhey hoa"
    return send_email(item, vendor_email, f"{document} needed — {_p().get_community(item.community_id or '1001').name}", body)


def create_service_request(item, unit_account_id: str, category: str, summary: str) -> dict:
    sr = _p().create_service_request(item.community_id or "1001", unit_account_id, category, summary)
    _log(item, "caliber.servicerequest", sr.id)
    return {"ok": True, "id": sr.id}


def queue_board_decision(item, title: str, body: str, decision_type: str = "other") -> dict:
    wi = WorkItem(community_id=item.community_id, kind="decision", lane="board", state="proposed", subject=title, summary=body, category=decision_type, needs_review=True, shadow=item.shadow, proposal={"action": "board_vote", "payload": {}, "preview": body, "needs_review": True})
    db.session.add(wi)
    _log(item, "board.decision.queued", title)
    return {"ok": True}


def send_board_digest(item, body: str, subject: str = "This week at your community") -> dict:
    # board contacts: demo sends to the treasurer persona
    from ..integrations.mock import DEMO_BOARD

    return send_email(item, DEMO_BOARD["email"], subject, body)


def snapshot_and_verify(item) -> dict:
    from ..services import financials

    cid = item.community_id or "1001"
    n = financials.snapshot_coa(cid, dt.date.today())
    snap = _p().get_financial_snapshot(cid)
    checks = {"accounts_snapshotted": n, "operating_cash_gl": snap.operating_cash, "reserve_cash_gl": snap.reserve_cash, "recon_status": snap.recon_status, "ap_pending": snap.ap_pending}
    _log(item, "close.snapshot", f"{n} accounts")
    return {"ok": True, **checks}


def request_documents(item, to: str, missing: list) -> dict:
    body = "Hi,\n\nTo finish onboarding we still need:\n" + "\n".join(f"• {m}" for m in missing) + "\n\nUpload them in the portal or reply with attachments.\n\nThanks,\nhey hoa"
    return send_email(item, to, "Onboarding: documents still needed", body)


# ---- tool registry ------------------------------------------------------------
S = {"type": "string"}
N = {"type": "number"}
TOOLS: dict[str, Tool] = {t.name: t for t in [
    Tool("lookup_owner", "Find an owner by email or unit account id in this community's roster.", {"type": "object", "properties": {"email": S, "unit_account_id": S}}, lookup_owner, RISK_READ),
    Tool("get_ledger", "Owner ledger lines and current balance.", {"type": "object", "properties": {"unit_account_id": S}, "required": ["unit_account_id"]}, get_ledger, RISK_READ),
    Tool("get_delinquencies", "All delinquent accounts with stage and days.", {"type": "object", "properties": {}}, get_delinquencies, RISK_READ),
    Tool("search_rules", "Search the community's governing documents, policies and board notes.", {"type": "object", "properties": {"query": S}, "required": ["query"]}, search_rules, RISK_READ),
    Tool("list_invoices", "Vendor invoices by status (pending_board, approved, paid).", {"type": "object", "properties": {"status": S}}, list_invoices, RISK_READ),
    Tool("vendor_history", "Past invoices and average amount for a vendor.", {"type": "object", "properties": {"vendor": S}, "required": ["vendor"]}, vendor_history, RISK_READ),
    Tool("list_vendors", "Vendors with W-9 and COI status.", {"type": "object", "properties": {}}, list_vendors, RISK_READ),
    Tool("list_decisions", "Everything waiting on the board: invoices and ARC items.", {"type": "object", "properties": {}}, list_decisions, RISK_READ),
    Tool("get_financials", "Current financial snapshot.", {"type": "object", "properties": {}}, get_financials, RISK_READ),
    Tool("send_email", "Send an email to an owner, vendor or board member.", {"type": "object", "properties": {"to": S, "subject": S, "body": S}, "required": ["to", "subject", "body"]}, send_email, RISK_SEND),
    Tool("send_sms", "Send a text message.", {"type": "object", "properties": {"to": S, "body": S}, "required": ["to", "body"]}, send_sms, RISK_SEND),
    Tool("post_note", "Record a note on the owner's account in Caliber.", {"type": "object", "properties": {"unit_account_id": S, "text": S}, "required": ["unit_account_id", "text"]}, post_note, RISK_WRITE),
    Tool("handoff", "Hand this item to another lane (cs, ar, ap, board, close, onboarding).", {"type": "object", "properties": {"lane": S, "note": S}, "required": ["lane"]}, handoff, RISK_WRITE),
    Tool("escalate", "Escalate to a person (coordinator or accountant) with a note.", {"type": "object", "properties": {"lane": S, "note": S}}, escalate, RISK_WRITE),
    Tool("post_fine", "Post a fine or collection fee to an owner ledger.", {"type": "object", "properties": {"unit_account_id": S, "amount": N, "description": S}, "required": ["unit_account_id", "amount", "description"]}, post_fine, RISK_MONEY),
    Tool("create_payment_plan", "Set up an ACH payment plan within policy (max 6 months).", {"type": "object", "properties": {"unit_account_id": S, "months": {"type": "integer"}, "monthly_amount": N, "start_date": S}, "required": ["unit_account_id", "months", "monthly_amount"]}, create_payment_plan, RISK_MONEY),
    Tool("send_notice", "Send a collection notice for a stage, post the policy fee and a note.", {"type": "object", "properties": {"unit_account_id": S, "stage": S, "body": S, "channel": S, "fee": N}, "required": ["unit_account_id", "stage", "body"]}, send_notice, RISK_MONEY),
    Tool("post_invoice", "Post a coded vendor invoice to Caliber for board approval.", {"type": "object", "properties": {"vendor": S, "number": S, "amount": N, "gl_account": S, "description": S, "due_date": S}, "required": ["vendor", "number", "amount", "gl_account", "description"]}, post_invoice, RISK_WRITE),
    Tool("request_vendor_document", "Email a vendor for a W-9 or certificate of insurance.", {"type": "object", "properties": {"vendor_email": S, "document": S, "vendor_name": S}, "required": ["vendor_email", "document"]}, request_vendor_document, RISK_SEND),
    Tool("create_service_request", "File a maintenance request in Caliber.", {"type": "object", "properties": {"unit_account_id": S, "category": S, "summary": S}, "required": ["unit_account_id", "category", "summary"]}, create_service_request, RISK_WRITE),
    Tool("queue_board_decision", "Put a decision in front of the board.", {"type": "object", "properties": {"title": S, "body": S, "decision_type": S}, "required": ["title", "body"]}, queue_board_decision, RISK_WRITE),
    Tool("send_board_digest", "Email the board its weekly digest.", {"type": "object", "properties": {"subject": S, "body": S}, "required": ["body"]}, send_board_digest, RISK_SEND),
    Tool("snapshot_and_verify", "Snapshot the chart of accounts and verify cash and reconciliation status.", {"type": "object", "properties": {}}, snapshot_and_verify, RISK_READ),
    Tool("request_documents", "Email the board liaison for missing onboarding documents.", {"type": "object", "properties": {"to": S, "missing": {"type": "array", "items": S}}, "required": ["to", "missing"]}, request_documents, RISK_SEND),
]}


def pick(*names: str) -> list[Tool]:
    return [TOOLS[n] for n in names]
