"""The board calendar and the board roster.

A calendar item repeats (annual, quarterly, monthly) with a lead time and an owner. Occurrences are
computed for the next twelve months; completion is stored per period. hey's board lane opens a work
item when an occurrence enters its lead window so the right person gets the steps in their inbox.
"""
from __future__ import annotations

import calendar as cal
import datetime as dt

from ..extensions import db
from ..models import BoardMember, CalendarDone, CalendarItem

KINDS = [("governance", "Governance"), ("accounting", "Accounting & tax"), ("meeting", "Meetings"), ("insurance", "Insurance"), ("maintenance", "Maintenance"), ("custom", "Custom")]
REPEATS = [("annual", "Every year"), ("quarterly", "Every quarter"), ("monthly", "Every month"), ("once", "Once")]
OWNERS = [("board", "Board"), ("president", "President"), ("treasurer", "Treasurer"), ("secretary", "Secretary"), ("hey", "hey")]
ROLES = [("president", "President"), ("vice_president", "Vice president"), ("treasurer", "Treasurer"), ("secretary", "Secretary"), ("director", "Director")]

# The standard calendar for an Arizona association on a calendar fiscal year. Boards edit it.
# title, kind, repeats, month, day, lead_days, owner, source, steps
STANDARD = [
    ("Annual meeting of members", "meeting", "annual", 2, 15, 45, "secretary", "Bylaws; A.R.S. 33-1804 (notice 10-50 days)", ["Pick the date and place", "Send notice 10-50 days ahead (hey mails owners without email)", "Nominations and proxies or absentee ballots", "Agenda and the year in review", "Minutes within 30 days"]),
    ("Board election and officer appointments", "governance", "annual", 2, 15, 60, "president", "Bylaws", ["Check whose terms end this year", "Call for candidates 60 days out", "Ballots per the bylaws", "Record results and new terms on the roster", "Update bank signers at the partner bank"]),
    ("Budget for next year", "accounting", "annual", 10, 15, 60, "treasurer", "Bylaws; A.R.S. 33-1803", ["hey drafts from 12 months of actuals, contracts and the reserve plan", "Board reviews line by line", "Adopt at a board meeting", "Notice to owners with the new assessment", "Autopay amounts update on the effective date"]),
    ("Reserve plan review", "accounting", "annual", 9, 1, 30, "treasurer", "Reserve study; A.R.S. 33-1806 disclosure", ["Update the project list and years", "Compare the contribution to the study", "Decide the contribution for the budget"]),
    ("Year-end close", "accounting", "annual", 1, 15, 15, "hey", "Cash basis", ["December package", "Reconcile every account to the bank", "Fund balances rolled into the new year", "Prior-year package archived in Records"]),
    ("1099s to vendors", "accounting", "annual", 1, 31, 30, "hey", "IRS", ["Vendors over $600 without a W-9: chase", "Prepare and file 1099-NEC/MISC", "Copies to vendors by Jan 31"]),
    ("Association tax return (1120-H)", "accounting", "annual", 3, 15, 45, "treasurer", "IRS; CPA", ["hey sends the year-end package to the CPA", "Board signs the return", "Extension if needed"]),
    ("Annual corporate report", "governance", "annual", 6, 1, 30, "secretary", "Arizona Corporation Commission (due in the anniversary month)", ["File the annual report online", "Confirm statutory agent and officers", "Save the receipt in Records"]),
    ("Insurance renewal", "insurance", "annual", 2, 1, 60, "treasurer", "Policy expiry on the Insurance page", ["Agent sends renewal terms 45 days out", "Compare coverage to the bylaws and lender requirements", "Approve the premium on the decisions list", "New declarations pages to Records"]),
    ("Assessment notice to owners", "accounting", "annual", 11, 15, 10, "hey", "Adopted budget", ["Letter and email with the new amount and date", "Autopay updates", "Coupon or statement for check payers"]),
    ("Fidelity and D&O coverage check", "insurance", "annual", 7, 1, 15, "treasurer", "Bylaws; lender requirements", ["Limits still match the reserve balance and the bylaws", "Board members listed on the D&O policy"]),
    ("Backflow preventer test", "maintenance", "annual", 4, 1, 21, "board", "City of Mesa", ["Schedule the certified tester", "File the report with the city", "Invoice to approvals"]),
    ("Fire extinguisher and pool permit renewals", "maintenance", "annual", 5, 1, 30, "board", "County health; fire marshal", ["Pool permit renewal", "Extinguisher inspection tags", "Certificates to Records"]),
    ("Quarterly reserve transfer check", "accounting", "quarterly", 1, 10, 7, "treasurer", "Budget", ["Confirm the monthly contributions landed in the reserve account", "Any transfer needs a board decision; a person executes it at the bank"]),
    ("Financial package to the board", "accounting", "monthly", 1, 5, 0, "hey", "Agreement: by the 5th business day", ["Package delivered", "Board reads the monthly update first", "Questions to hey"]),
]


def _clamp(year: int, month: int, day: int) -> dt.date:
    return dt.date(year, month, min(day or 1, cal.monthrange(year, month)[1]))


def occurrences(item: CalendarItem, start: dt.date, months: int = 12) -> list[tuple[dt.date, str]]:
    """(due date, period key) for every occurrence within the window."""
    end = _clamp(start.year + (start.month - 1 + months) // 12, (start.month - 1 + months) % 12 + 1, start.day)
    out = []
    if item.repeats == "once":
        if item.year and item.month:
            d = _clamp(item.year, item.month, item.day or 1)
            if start - dt.timedelta(days=365) <= d <= end:
                out.append((d, str(item.year)))
        return out
    if item.repeats == "annual":
        for y in (start.year - 1, start.year, start.year + 1, start.year + 2):
            d = _clamp(y, item.month or 1, item.day or 1)
            if start - dt.timedelta(days=item.lead_days or 0) - dt.timedelta(days=90) <= d <= end:
                out.append((d, str(y)))
    elif item.repeats == "quarterly":
        m0 = ((item.month or 1) - 1) % 3
        for y in (start.year - 1, start.year, start.year + 1):
            for q in range(4):
                m = m0 + q * 3 + 1
                d = _clamp(y, m, item.day or 1)
                if start - dt.timedelta(days=45) <= d <= end:
                    out.append((d, f"{y}-Q{(m - 1) // 3 + 1}"))
    elif item.repeats == "monthly":
        y, m = start.year, start.month
        for _ in range(months + 1):
            d = _clamp(y, m, item.day or 1)
            if start - dt.timedelta(days=31) <= d <= end:
                out.append((d, f"{y}-{m:02d}"))
            m += 1
            if m > 12:
                y, m = y + 1, 1
    return sorted(out)


def items(community_id: str) -> list[CalendarItem]:
    return CalendarItem.query.filter_by(community_id=community_id, active=True).order_by(CalendarItem.month, CalendarItem.day).all()


def upcoming(community_id: str, today: dt.date | None = None, months: int = 12) -> list[dict]:
    """Every occurrence in the window with its status: done, overdue, due (inside the lead window), upcoming."""
    today = today or dt.date.today()
    rows = []
    done = {(d.item_id, d.period): d for d in CalendarDone.query.join(CalendarItem, CalendarItem.id == CalendarDone.item_id).filter(CalendarItem.community_id == community_id).all()}
    for it in items(community_id):
        for due, period in occurrences(it, today, months):
            d = done.get((it.id, period))
            if d:
                status = "done"
            elif due < today:
                status = "overdue"
            elif (due - today).days <= (it.lead_days or 0):
                status = "due"
            else:
                status = "upcoming"
            if status == "done" and due < today - dt.timedelta(days=60):
                continue  # old and finished: off the list
            if status == "overdue" and due < today - dt.timedelta(days=120):
                continue  # too old to nag about; the next occurrence carries it
            rows.append({"item": it, "due": due, "period": period, "status": status, "done": d, "starts": due - dt.timedelta(days=it.lead_days or 0)})
    rows.sort(key=lambda r: r["due"])
    return rows


def due_now(community_id: str, today: dt.date | None = None) -> list[dict]:
    return [r for r in upcoming(community_id, today, months=3) if r["status"] in ("due", "overdue")]


def mark_done(item_id: int, period: str, by: str, note: str = "") -> CalendarDone:
    d = CalendarDone.query.filter_by(item_id=item_id, period=period).first() or CalendarDone(item_id=item_id, period=period)
    d.done_by, d.note, d.done_at = by, note, dt.datetime.now(dt.timezone.utc)
    db.session.add(d)
    db.session.commit()
    return d


def unmark(item_id: int, period: str) -> None:
    CalendarDone.query.filter_by(item_id=item_id, period=period).delete()
    db.session.commit()


def _int(v, default=None):
    try:
        return int(str(v).strip()) if str(v).strip() else default
    except (TypeError, ValueError):
        return default


def save_item(community_id: str, form, item: CalendarItem | None = None) -> CalendarItem:
    it = item or CalendarItem(community_id=community_id)
    it.title = (form.get("title") or it.title or "").strip()
    it.kind = form.get("kind") or it.kind or "custom"
    it.repeats = form.get("repeats") or it.repeats or "annual"
    it.month = _int(form.get("month"), it.month or 1)
    it.day = _int(form.get("day"), it.day or 1)
    it.year = _int(form.get("year"), it.year)
    it.lead_days = _int(form.get("lead_days"), it.lead_days if it.lead_days is not None else 30)
    it.owner = form.get("owner") or it.owner or "board"
    it.source = form.get("source", it.source)
    it.notes = form.get("notes", it.notes)
    steps = [s.strip() for s in (form.get("steps") or "").splitlines() if s.strip()]
    if steps or form.get("steps") is not None:
        it.steps = steps
    db.session.add(it)
    db.session.commit()
    return it


def seed_standard(community_id: str, fiscal_year_end: str = "12/31") -> int:
    n = 0
    for title, kind, repeats, month, day, lead, owner, source, steps in STANDARD:
        if not CalendarItem.query.filter_by(community_id=community_id, title=title).first():
            db.session.add(CalendarItem(community_id=community_id, title=title, kind=kind, repeats=repeats, month=month, day=day, lead_days=lead, owner=owner, source=source, steps=steps))
            n += 1
    db.session.commit()
    return n


# ---- roster ----------------------------------------------------------------

def roster(community_id: str) -> list[BoardMember]:
    order = {k: i for i, (k, _) in enumerate(ROLES)}
    return sorted(BoardMember.query.filter_by(community_id=community_id, active=True).all(), key=lambda m: (order.get(m.role, 9), m.name or ""))


def member_for(community_id: str, owner: str) -> BoardMember | None:
    if owner in ("board", "hey"):
        return next((m for m in roster(community_id) if m.role == "president"), None)
    return next((m for m in roster(community_id) if m.role == owner), None)


def save_member(community_id: str, form, member: BoardMember | None = None) -> BoardMember:
    m = member or BoardMember(community_id=community_id)
    m.name = (form.get("name") or m.name or "").strip()
    m.role = form.get("role") or m.role or "director"
    m.email, m.phone, m.unit_label = form.get("email", m.email), form.get("phone", m.phone), form.get("unit_label", m.unit_label)
    m.signer = bool(form.get("signer")) if "signer" in form or member is None else m.signer
    ts = form.get("term_start")
    m.term_start = dt.date.fromisoformat(ts) if ts else m.term_start
    m.term_years = _int(form.get("term_years"), m.term_years or 2)
    te = form.get("term_end")
    if te:
        m.term_end = dt.date.fromisoformat(te)
    elif m.term_start and m.term_years:
        m.term_end = dt.date(m.term_start.year + m.term_years, m.term_start.month, min(m.term_start.day, 28))
    is_new = member is None
    db.session.add(m)
    db.session.commit()
    if is_new and m.email:
        try:
            from . import accounts

            accounts.send_setup(m, reason="invite")
        except Exception:  # noqa: BLE001 - an email failure must not block the roster
            pass
    return m


def seats_ending(community_id: str, within_days: int = 180) -> list[BoardMember]:
    return [m for m in roster(community_id) if m.days_left is not None and m.days_left <= within_days]


DEMO_ROSTER = [("Luis Castillo", "president", "luis@willowcreek.example", "Unit 18", "2025-02-15", 2, True), ("Dana Whitfield", "treasurer", "treasurer@willowcreek.example", "Unit 21", "2026-02-15", 2, True), ("Grace Thompson", "secretary", "grace@willowcreek.example", "Unit 27", "2025-02-15", 2, False)]


def seed_demo(community_id: str = "1001") -> int:
    n = seed_standard(community_id)
    for name, role, email, unit, start, years, signer in DEMO_ROSTER:
        if not BoardMember.query.filter_by(community_id=community_id, name=name).first():
            s = dt.date.fromisoformat(start)
            db.session.add(BoardMember(community_id=community_id, name=name, role=role, email=email, unit_label=unit, term_start=s, term_years=years, term_end=dt.date(s.year + years, s.month, s.day), signer=signer))
            n += 1
    db.session.commit()
    return n
