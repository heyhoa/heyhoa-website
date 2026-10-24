"""Board decisions beyond invoices: what needs a vote, how many, and what happens after.

A decision is a WorkItem with kind="decision" in the board lane. Votes are
recorded on the item; when approvals reach the type's quorum the item is
approved and an execution work item is created for the accountant or the
coordinator. Invoices keep their own flow (two approvals in Caliber).
"""
from __future__ import annotations

import datetime as dt

from ..extensions import db
from ..models import AuditLog, WorkItem

DECISION_TYPES = {
    "transfer": {"label": "Bank transfer (operating ↔ reserve)", "approvals": 2, "execute_lane": "close", "money": True},
    "investment": {"label": "Buy or redeem a CD / yield vehicle", "approvals": 2, "execute_lane": "close", "money": True},
    "bid": {"label": "Vendor estimate / bid", "approvals": 2, "execute_lane": "ap", "money": True},
    "work_order": {"label": "Service request → open a work order", "approvals": 1, "execute_lane": "cs", "money": False},
    "arc": {"label": "Architectural request (if assigned to the board)", "approvals": 2, "execute_lane": "cs", "money": False},
    "special_assessment": {"label": "Special assessment", "approvals": 3, "execute_lane": "ar", "money": True},
    "budget": {"label": "Annual budget adoption", "approvals": 3, "execute_lane": "close", "money": True},
    "policy": {"label": "Policy or rule adoption", "approvals": 3, "execute_lane": "cs", "money": False},
    "collections": {"label": "Attorney referral / lien / foreclosure step", "approvals": 2, "execute_lane": "ar", "money": True},
    "fee_waiver": {"label": "Fee or fine waiver", "approvals": 2, "execute_lane": "ar", "money": True},
    "vendor_add": {"label": "New vendor / contract", "approvals": 2, "execute_lane": "ap", "money": True},
    "insurance": {"label": "Insurance renewal / claim", "approvals": 2, "execute_lane": "ap", "money": True},
    "meeting": {"label": "Meeting notice / election", "approvals": 1, "execute_lane": "cs", "money": False},
    "announcement": {"label": "Owner announcement", "approvals": 1, "execute_lane": "cs", "money": False},
    "invoice": {"label": "Vendor invoice", "approvals": 2, "execute_lane": "ap", "money": True},
    "other": {"label": "Other", "approvals": 2, "execute_lane": "cs", "money": False},
}


def spec(decision_type: str) -> dict:
    return DECISION_TYPES.get(decision_type or "other", DECISION_TYPES["other"])


def pending(community_id: str) -> list[WorkItem]:
    return WorkItem.query.filter_by(community_id=str(community_id), kind="decision").filter(WorkItem.state.in_(["proposed", "approved"])).order_by(WorkItem.created_at).all()


def history(community_id: str, limit: int = 50) -> list[WorkItem]:
    return WorkItem.query.filter_by(community_id=str(community_id), kind="decision").filter(WorkItem.state.in_(["done", "rejected"])).order_by(WorkItem.updated_at.desc()).limit(limit).all()


def create(community_id: str, decision_type: str, title: str, body: str, *, amount: float | None = None, requested_by: str = "hey", attachments: list | None = None, shadow: bool = True) -> WorkItem:
    item = WorkItem(community_id=str(community_id), kind="decision", lane="board", state="proposed", subject=title[:300], summary=body, category=decision_type, needs_review=True, shadow=shadow,
                    proposal={"action": "board_vote", "payload": {"amount": amount, "attachments": attachments or []}, "preview": body, "needs_review": True, "confidence": 1.0, "reason": requested_by},
                    remote_ids={"votes": [], "requested_by": requested_by})
    db.session.add(item)
    db.session.commit()
    return item


def vote(item: WorkItem, member_id: str, member_name: str, choice: str, note: str = "") -> WorkItem:
    votes = [v for v in (item.remote_ids or {}).get("votes", []) if v.get("member_id") != member_id]
    votes.append({"member_id": member_id, "member": member_name, "vote": choice, "note": note, "at": dt.datetime.now(dt.timezone.utc).isoformat()})
    item.remote_ids = {**(item.remote_ids or {}), "votes": votes}
    s = spec(item.category)
    approvals = sum(1 for v in votes if v["vote"] == "approve")
    denials = sum(1 for v in votes if v["vote"] == "deny")
    db.session.add(AuditLog(actor=member_name, action=f"decision.{choice}", target=f"wi:{item.id}", detail=f"{item.category}: {item.subject} ({approvals}/{s['approvals']})"))
    if choice == "deny" and denials >= 1 and s["approvals"] <= 1 or denials >= s["approvals"]:
        item.state, item.outcome = "rejected", f"Denied ({denials} deny). {note}".strip()
    elif approvals >= s["approvals"]:
        item.state, item.outcome = "done", f"Approved {approvals}/{s['approvals']}."
        _execute(item, s)
    db.session.commit()
    return item


def _execute(item: WorkItem, s: dict) -> WorkItem:
    """Approved → an execution work item for the lane that carries it out (accountant/coordinator)."""
    ex = WorkItem(community_id=item.community_id, kind="board_approved", lane=s["execute_lane"], state="new", subject=f"Execute: {item.subject}", summary=f"Board approved ({item.category}). {item.summary}", category=item.category, needs_review=True, shadow=item.shadow,
                  remote_ids={"decision_id": item.id, "amount": ((item.proposal or {}).get("payload") or {}).get("amount")}, priority="high" if s["money"] else "normal")
    db.session.add(ex)
    db.session.flush()
    from ..agents import runtime

    runtime.run(ex)
    return ex
