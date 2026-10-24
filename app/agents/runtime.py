"""Runtime: create work items from inbound events, run agents, review, execute."""
from __future__ import annotations

import datetime as dt
import logging

from flask import current_app

from ..channels import email as email_channel
from ..extensions import db
from ..integrations.registry import get_provider
from ..models import AuditLog, Message, WorkItem
from .lanes import AGENTS

log = logging.getLogger(__name__)

SLA_HOURS = {"cs": 4, "ar": 24, "ap": 24, "board": 72, "close": 24, "onboarding": 48, "sales": 8}
KIND_SLA_HOURS = {"records_request": 10 * 24, "resale_order": 3 * 24}  # statutory / promised clocks, business days approximated


def _shadow(community_id: str | None) -> bool:
    live = set(current_app.config.get("LIVE_COMMUNITIES", []))
    return current_app.config.get("SHADOW_MODE", True) and str(community_id) not in live


def community_from_addresses(addresses: list[str]) -> str | None:
    aliases = current_app.config.get("COMMUNITY_ALIASES", {})
    for a in addresses:
        if a in aliases:
            return aliases[a]
    return None


def owner_from_email(community_id: str | None, email: str):
    if not community_id or not email:
        return None
    for ua in get_provider().list_unit_accounts(community_id):
        if (ua.email or "").lower() == email.lower():
            return ua
    return None


def create_item(*, kind: str, lane: str, subject: str, summary: str, community_id: str | None = None, unit_account_id: str | None = None,
                counterpart_email: str | None = None, counterpart_name: str | None = None, priority: str = "normal", remote_ids: dict | None = None, evidence: list | None = None) -> WorkItem:
    item = WorkItem(kind=kind, lane=lane, subject=subject[:300], summary=summary, community_id=community_id, unit_account_id=unit_account_id,
                    counterpart_email=counterpart_email, counterpart_name=counterpart_name, priority=priority, remote_ids=remote_ids or {}, evidence=evidence or [],
                    shadow=_shadow(community_id), sla_due=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=KIND_SLA_HOURS.get(kind, SLA_HOURS.get(lane, 24))))
    db.session.add(item)
    db.session.flush()
    return item


def run(item: WorkItem) -> WorkItem:
    """Run the owning agent; execute immediately when policy allows, else park as proposed."""
    for _ in range(3):  # follow hand-offs
        agent = AGENTS[item.lane]
        item.state = "working"
        proposal = agent.run(item)
        item.proposal = proposal.to_json()
        item.needs_review = proposal.needs_review
        if proposal.action == "handoff" and not proposal.needs_review:
            agent.execute(item, item.proposal)
            continue
        if proposal.action == "none":
            item.state, item.outcome = "done", proposal.preview
        elif proposal.needs_review:
            item.state = "proposed"
        else:
            _execute(item, agent)
        break
    db.session.add(AuditLog(actor="hey", action=f"agent.{item.lane}.{item.state}", target=f"wi:{item.id}", detail=(item.proposal or {}).get("action", "")))
    db.session.commit()
    return item


def _execute(item: WorkItem, agent=None) -> dict:
    agent = agent or AGENTS[item.lane]
    res = agent.execute(item, item.proposal or {})
    if res.get("ok"):
        if item.state != "escalated":
            item.state = "done"
        item.outcome = (item.proposal or {}).get("preview", "")[:2000]
    else:
        item.state = "failed"
        item.outcome = str(res.get("error"))
    return res


def approve(item: WorkItem, reviewer: str, edits: dict | None = None, note: str = "") -> dict:
    if edits:
        item.proposal = {**(item.proposal or {}), "payload": {**((item.proposal or {}).get("payload") or {}), **edits}}
        if "body" in edits:
            item.proposal["preview"] = edits["body"]
    item.reviewer, item.reviewed_at, item.review_note = reviewer, dt.datetime.now(dt.timezone.utc), note
    item.state = "approved"
    res = _execute(item)
    db.session.add(AuditLog(actor=reviewer, action="review.approve", target=f"wi:{item.id}", detail=(item.proposal or {}).get("action", "")))
    db.session.commit()
    return res


def reject(item: WorkItem, reviewer: str, note: str = "") -> None:
    item.reviewer, item.reviewed_at, item.review_note = reviewer, dt.datetime.now(dt.timezone.utc), note
    item.state = "rejected"
    item.outcome = f"Rejected by {reviewer}: {note}"
    db.session.add(AuditLog(actor=reviewer, action="review.reject", target=f"wi:{item.id}", detail=note))
    db.session.commit()


def inbound_email(payload: dict) -> WorkItem:
    """Postmark inbound webhook → work item in the cs lane (agents hand off from there)."""
    m = email_channel.parse_inbound(payload)
    cid = community_from_addresses(m["to"])
    ua = owner_from_email(cid, m["from_email"])
    if not ua:
        reply = lead_reply(m)
        if reply is not None:
            return reply
    item = create_item(kind="email", lane="cs", subject=m["subject"], summary=m["text"], community_id=cid, unit_account_id=ua.id if ua else None,
                       counterpart_email=m["from_email"], counterpart_name=m["from_name"] or (ua.owner_name if ua else ""), remote_ids={"postmark_message_id": m["message_id"]},
                       evidence=([{"label": "owner", "ref": ua.id, "text": f"{ua.owner_name} · {ua.unit_label} · balance ${ua.balance:,.2f}"}] if ua else []) + [{"label": "attachments", "ref": "", "text": ", ".join(a["name"] or "" for a in m["attachments"]) or "none"}])
    db.session.add(Message(work_item_id=item.id, direction="in", channel="email", sender=m["from_email"], recipient=", ".join(m["to"]), subject=m["subject"], body=m["text"], author="owner" if ua else "unknown", delivered=True, meta={"message_id": m["message_id"]}))
    return run(item)


def lead_reply(m: dict) -> WorkItem | None:
    """A reply from someone we are selling to: mark the lead, stop sequence A, hand the thread to the sales lane."""
    from ..services import sales

    lead = sales.lead_for_email(m["from_email"])
    if not lead or lead.status in ("won",):
        return None
    kind = sales.mark_replied(lead, m["text"])
    item = create_item(kind="reply", lane="sales", subject=f"Reply ({kind}): {lead.community_name}", summary=m["text"][:4000], counterpart_email=m["from_email"], counterpart_name=m["from_name"] or lead.contact_name,
                       priority="high", remote_ids={"lead_id": lead.id, "reply_kind": kind, "postmark_message_id": m["message_id"]},
                       evidence=[{"label": "lead", "ref": str(lead.id), "text": f"{lead.community_name} · {lead.units} doors · status {lead.status}"}])
    db.session.add(Message(work_item_id=item.id, direction="in", channel="email", sender=m["from_email"], recipient=", ".join(m["to"]), subject=m["subject"], body=m["text"], author="lead", delivered=True, meta={"message_id": m["message_id"]}))
    return run(item)


def inbound_portal(*, community_id: str, unit_account_id: str | None, kind: str, subject: str, body: str, email: str | None, name: str | None, lane: str = "cs") -> WorkItem:
    item = create_item(kind=kind, lane=lane, subject=subject, summary=body, community_id=community_id, unit_account_id=unit_account_id, counterpart_email=email, counterpart_name=name)
    db.session.add(Message(work_item_id=item.id, direction="in", channel="portal", sender=email or "", subject=subject, body=body, author="owner", delivered=True))
    return run(item)


def new_lead(lead) -> WorkItem:
    """Quote request → sales lane: proposal email now, sequence A touches scheduled."""
    from ..services import sales

    item = create_item(kind="lead", lane="sales", subject=f"Quote: {lead.community_name} · {lead.units} doors · score {lead.score}", summary=f"{lead.contact_name} ({lead.contact_role}) · {lead.current_setup} · pains: {lead.pain_points or '-'} · plan asked: {lead.plan or '-'}",
                       counterpart_email=lead.email, counterpart_name=lead.contact_name, priority="high" if (lead.score or 0) >= 70 else "normal", remote_ids={"lead_id": lead.id}, evidence=[{"label": "quote", "ref": "", "text": f"${sales.quote(lead)['monthly']:,}/mo on {sales.quote(lead)['tier']['name']}"}])
    schedule_followups(lead, start_step=1)
    return run(item)


def schedule_followups(lead, start_step: int = 1) -> int:
    from ..services import sales

    n = 0
    for step in range(start_step, len(sales.SEQUENCE_A)):
        day = sales.SEQUENCE_A[step][0]
        wi = WorkItem(kind="followup", lane="sales", state="new", subject=f"Follow-up {step + 1}: {lead.community_name}", summary=f"Sequence A touch {step + 1} (day {day}).", counterpart_email=lead.email, counterpart_name=lead.contact_name,
                      remote_ids={"lead_id": lead.id, "step": step}, shadow=True, priority="low", sla_due=dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=day))
        db.session.add(wi)
        n += 1
    db.session.commit()
    return n


def run_due_followups() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    due = WorkItem.query.filter_by(lane="sales", kind="followup", state="new").filter(WorkItem.sla_due <= now).all()
    for w in due:
        run(w)
    return len(due)


def calendar_reminders(community_id: str) -> int:
    """Each calendar occurrence entering its lead window becomes one board-lane item with the steps."""
    from ..services import calendar as board_calendar

    n = 0
    for r in board_calendar.due_now(community_id):
        key = f"{r['item'].id}:{r['period']}"
        if WorkItem.query.filter_by(community_id=community_id, kind="calendar").filter(WorkItem.remote_ids["calendar_key"].as_string() == key).first():
            continue
        it = r["item"]
        run(create_item(kind="calendar", lane="board", subject=f"{it.title} · due {r['due']:%b %d}", summary="\n".join(f"- {s}" for s in (it.steps or [])) or (it.notes or ""), community_id=community_id,
                        priority="high" if r["status"] == "overdue" else "normal", remote_ids={"calendar_key": key, "calendar_item_id": it.id, "period": r["period"], "owner": it.owner},
                        evidence=[{"label": "source", "ref": "", "text": it.source or ""}, {"label": "due", "ref": "", "text": f"{r['due']} ({r['status']})"}]))
        n += 1
    return n


def daily(community_id: str | None = None) -> dict:
    """Scheduled work: AR ladder, vendor compliance, close snapshot, Friday digest."""
    p = get_provider()
    counts = {"ar": 0, "ap": 0, "close": 0, "board": 0, "sales": run_due_followups()}
    for c in p.list_communities():
        if community_id and c.id != str(community_id):
            continue
        for d in p.list_delinquencies(c.id):
            if WorkItem.query.filter_by(community_id=c.id, unit_account_id=d.unit_account_id, kind="delinquency").filter(WorkItem.state.in_(["new", "working", "proposed", "approved"])).first():
                continue
            run(create_item(kind="delinquency", lane="ar", subject=f"Collections: {d.unit_label} · {d.days_late} days · ${d.balance:,.2f}", summary=f"{d.owner_name} is {d.days_late} days past due with ${d.balance:,.2f}. Stage {d.stage}. Last: {d.last_action}.", community_id=c.id, unit_account_id=d.unit_account_id, counterpart_email=None, priority="high" if d.days_late >= 60 else "normal"))
            counts["ar"] += 1
        if any(not v.w9_on_file for v in p.list_vendors(c.id)) and not WorkItem.query.filter_by(community_id=c.id, kind="vendor_compliance").filter(WorkItem.state.in_(["new", "working", "proposed"])).first():
            run(create_item(kind="vendor_compliance", lane="ap", subject="Vendor missing W-9", summary="A vendor on the list has no W-9; payments are blocked until received.", community_id=c.id))
            counts["ap"] += 1
        for inv in p.list_invoices(c.id, status="pending_board"):
            if not WorkItem.query.filter_by(community_id=c.id, kind="invoice").filter(WorkItem.remote_ids["invoice_id"].as_string() == inv.id).first():
                run(create_item(kind="invoice", lane="ap", subject=f"Invoice {inv.vendor} {inv.number} · ${inv.amount:,.2f}", summary=inv.description, community_id=c.id, remote_ids={"invoice_id": inv.id}))
                counts["ap"] += 1
        run(create_item(kind="close", lane="close", subject=f"Nightly close check · {dt.date.today():%b %d}", summary="Snapshot chart of accounts, verify cash and reconciliation status.", community_id=c.id))
        counts["close"] += 1
        if dt.date.today().weekday() == 4:
            run(create_item(kind="digest", lane="board", subject="Friday board digest", summary="Weekly digest for the board.", community_id=c.id))
            counts["board"] += 1
        counts["board"] += calendar_reminders(c.id)
    db.session.commit()
    return counts
