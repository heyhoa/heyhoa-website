"""Meetings: notice, agenda from a template filled with this month's facts, minutes.

Agenda templates are lists of lines. "Build agenda" fills the template with what is actually
pending: decisions waiting on a vote, projects due, the financial package, open requests.
"""
from __future__ import annotations

import datetime as dt

from ..extensions import db
from ..models import Letter, Meeting
from . import decisions, plans

KINDS = [("board", "Board meeting"), ("annual", "Annual meeting of members"), ("budget", "Budget meeting"), ("special", "Special meeting"), ("executive", "Executive session")]

TEMPLATES: dict[str, list[str]] = {
    "board": ["Call to order, roll call, quorum", "Approve minutes of the last meeting", "Treasurer's report: {package}", "Decisions waiting on a vote: {decisions}", "Projects: {projects}", "Owner requests and correspondence: {requests}",
              "Old business", "New business", "Owner forum (3 minutes each)", "Next meeting date", "Adjourn"],
    "annual": ["Call to order, proof of notice, quorum of members", "Introduction of the board and hey hoa", "Approve minutes of the last annual meeting", "Year in review: financials, projects, reserves", "Treasurer's report: {package}",
               "Election of directors (nominations, ballots, count)", "Ratify the {year} budget", "Projects ahead: {projects}", "Owner forum", "Adjourn"],
    "budget": ["Call to order, quorum", "Current year to date vs budget", "Insurance renewal and the big lines", "Reserve plan: contribution and the next five years", "Proposed assessment for {year}", "Vote to adopt the budget", "Notice to owners (statutory days)", "Adjourn"],
    "special": ["Call to order, proof of notice, quorum", "Purpose of the meeting (one item)", "Discussion", "Vote", "Adjourn"],
    "executive": ["Call to order (closed session: legal, personnel, delinquencies, violations)", "Delinquent accounts: {delinquent}", "Pending violations", "Legal matters", "Return to open session, report actions taken", "Adjourn"],
}

NOTICE_DAYS = {"board": 10, "annual": 30, "budget": 10, "special": 10, "executive": 10}


def upcoming(community_id: str) -> list[Meeting]:
    return Meeting.query.filter_by(community_id=community_id).filter(Meeting.status == "scheduled").order_by(Meeting.date).all()


def past(community_id: str, limit: int = 24) -> list[Meeting]:
    return Meeting.query.filter_by(community_id=community_id).filter(Meeting.status != "scheduled").order_by(Meeting.date.desc()).limit(limit).all()


def facts(community_id: str, provider) -> dict:
    snap = provider.get_financial_snapshot(community_id)
    pend = decisions.pending(community_id)
    inv = provider.list_invoices(community_id, status="pending_board")
    projects = [p for p in plans.projects(community_id) if p.status in ("planned", "in_progress", "under_review") and p.year and p.year <= dt.date.today().year + 1]
    reqs = [r for r in provider.list_service_requests(community_id) if getattr(r, "status", "") not in ("closed", "completed")] if hasattr(provider, "list_service_requests") else []
    delinquent = provider.list_delinquencies(community_id)
    return {
        "package": f"{snap.last_packet_date or 'latest'} package: operating {snap.operating_cash:,.0f}, reserves {snap.reserve_cash:,.0f}, YTD net {snap.ytd_income - snap.ytd_expense:,.0f}",
        "decisions": "; ".join([d.subject for d in pend] + [f"invoice {i.vendor} ${i.amount:,.2f}" for i in inv]) or "none",
        "projects": "; ".join(f"{p.name} ({p.year}, ${p.cost:,.0f})" for p in projects) or "none due this year",
        "requests": f"{len(reqs)} open" if reqs else "none open",
        "delinquent": f"{len(delinquent)} accounts, ${sum(d.balance for d in delinquent):,.2f}",
        "year": dt.date.today().year + 1,
    }


def build_agenda(kind: str, community_id: str, provider) -> list[str]:
    f = facts(community_id, provider)
    out = []
    for line in TEMPLATES.get(kind, TEMPLATES["board"]):
        try:
            out.append(line.format(**f))
        except (KeyError, IndexError):
            out.append(line)
    return out


def create(community_id: str, *, kind: str, date: dt.date, time: str, where: str, agenda: list[str], created_by: str, notice_days: int | None = None) -> Meeting:
    m = Meeting(community_id=community_id, kind=kind, date=date, time=time, where=where, agenda=agenda, notice_days=notice_days or NOTICE_DAYS.get(kind, 10), created_by=created_by)
    db.session.add(m)
    db.session.commit()
    return m


def notice_text(m: Meeting, community_name: str) -> tuple[str, str]:
    label = dict(KINDS).get(m.kind, "Meeting")
    subject = f"Notice: {label} · {m.date.strftime('%A, %B %d, %Y')} at {m.time}"
    body = (f"To the owners of {community_name}:\n\nA {label.lower()} of the Board of Directors will be held on {m.date.strftime('%A, %B %d, %Y')} at {m.time}, {m.where}.\n\nAgenda\n" +
            "\n".join(f"{i}. {a}" for i, a in enumerate(m.agenda or [], 1)) +
            f"\n\nOwners are welcome. Owner forum is on the agenda. Minutes are posted in the portal within 30 days.\n\nThis notice is given {m.notice_days} days in advance per the bylaws and state statute.")
    return subject, body


def notice_deadline(m: Meeting) -> dt.date:
    return m.date - dt.timedelta(days=m.notice_days or 10)


def letters_for(m: Meeting) -> list[Letter]:
    return Letter.query.filter_by(meeting_id=m.id).all()
