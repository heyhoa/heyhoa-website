"""Emails to board members that carry the decision and one-click links, so nobody has to log in."""
from __future__ import annotations

from ..channels import email as email_channel
from . import calendar as board_calendar
from . import magic


def _members(community_id: str, signers_only: bool = False):
    return [m for m in board_calendar.roster(community_id) if m.email and (m.signer or not signers_only)]


def notify_invoice(community_id: str, inv, checks: list[tuple[str, str]] | None = None, community_name: str = "") -> int:
    """One email per signer: what, why, what hey checked, approve / reject links."""
    n = 0
    for m in _members(community_id, signers_only=True):
        lines = "\n".join(f"  {'✓' if lvl == 'ok' else '!' if lvl == 'warn' else '✗'} {txt}" for lvl, txt in (checks or []))
        body = (f"Hi {m.name.split(' ')[0]},\n\nA bill is waiting on you{(' at ' + community_name) if community_name else ''}:\n\n"
                f"  {inv.vendor} · #{inv.number} · ${inv.amount:,.2f}\n  {inv.description}\n  Due {inv.due_date} · {inv.approvals} of {inv.approvals_required} approvals so far\n\n"
                f"hey checked:\n{lines or '  (no checks recorded)'}\n{('hey: ' + inv.ai_note) if inv.ai_note else ''}\n\n"
                f"Approve: {magic.action_url('invoice', inv.id, 'approve', m)}\nReject: {magic.action_url('invoice', inv.id, 'reject', m)}\n\n"
                f"Or open it in the portal: {magic.login_url(m)}\n\nNothing moves until {inv.approvals_required} approvals are in; the accountant then releases payment. — hey")
        email_channel.send(m.email, f"Approve? {inv.vendor} ${inv.amount:,.2f}", body, tag="board-invoice")
        n += 1
    return n


def notify_decision(item, label: str, approvals_needed: int, community_name: str = "") -> int:
    """One email per board member: the question, the details, approve / deny links."""
    n = 0
    amount = ((item.proposal or {}).get("payload") or {}).get("amount")
    for m in _members(item.community_id):
        body = (f"Hi {m.name.split(' ')[0]},\n\nYour vote is needed{(' at ' + community_name) if community_name else ''}:\n\n  {item.subject}{(' · $' + format(amount, ',.2f')) if amount else ''}\n  {label} · {approvals_needed} approvals needed\n\n{item.summary}\n\n"
                f"Approve: {magic.action_url('decision', item.id, 'approve', m)}\nDeny: {magic.action_url('decision', item.id, 'deny', m)}\n\n"
                f"Or open it in the portal: {magic.login_url(m)}\n\nIf it is a money decision, a person executes it at the bank after the vote. — hey")
        email_channel.send(m.email, f"Vote: {item.subject[:60]}", body, tag="board-decision")
        n += 1
    return n


def send_login_link(member) -> dict:
    body = f"Hi {member.name.split(' ')[0]},\n\nHere is your link to the board portal. It works for 7 days and only for you:\n\n{magic.login_url(member)}\n\n— hey"
    return email_channel.send(member.email, "Your hey hoa link", body, tag="magic-login")
