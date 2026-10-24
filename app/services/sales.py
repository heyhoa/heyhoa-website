"""Sales: quote math, proposal links, recommended tier, follow-up sequence."""
from __future__ import annotations

import datetime as dt
import re

from flask import current_app, url_for
from itsdangerous import BadSignature, URLSafeSerializer

from .. import brand
from ..extensions import db

TIERS = {t["slug"]: t for t in brand.PRICING}
BASE_DOORS = 30


def monthly_price(slug: str, units: int) -> int:
    t = TIERS[slug]
    per_door = int(t["per_door"].split("$")[1].split("/")[0])
    return t["price"] + max(0, (units or 0) - BASE_DOORS) * per_door


def recommend_tier(lead) -> str:
    if lead.plan in TIERS:
        return lead.plan
    pains = (lead.pain_points or "").lower()
    units = lead.units or 0
    if units > 120 or ("vendor payments" in pains and "volunteer burnout" in pains):
        return "board-plus"
    if lead.current_setup == "accountant" and not pains:
        return "books"
    return "back-office"


def quote(lead) -> dict:
    slug = recommend_tier(lead)
    units = lead.units or BASE_DOORS
    return {
        "tier": TIERS[slug], "slug": slug, "units": units, "monthly": monthly_price(slug, units), "per_door": round(monthly_price(slug, units) / max(units, 1), 2),
        "alternatives": [{"slug": s, "name": TIERS[s]["name"], "monthly": monthly_price(s, units)} for s in TIERS if s != slug],
        "full_service_low": max(1000, units * 25), "full_service_high": max(1400, units * 40),
    }


def _serializer():
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="proposal")


def proposal_token(lead_id: int) -> str:
    return _serializer().dumps(lead_id)


def lead_id_from_token(token: str) -> int | None:
    try:
        return int(_serializer().loads(token))
    except (BadSignature, ValueError):
        return None


def proposal_url(lead) -> str:
    return url_for("marketing.proposal", token=proposal_token(lead.id), _external=True)


def onboarding_calendar(start: dt.date | None = None) -> list[dict]:
    start = start or (dt.date.today() + dt.timedelta(days=7))
    w = lambda n: start + dt.timedelta(days=7 * n)  # noqa: E731
    return [
        {"week": 1, "date": w(0), "what": "Documents and access: governing docs, 12 months of statements, vendor list, owner roster; accounts opened at the partner bank in the association's name"},
        {"week": 2, "date": w(1), "what": "Parallel rebuild: hey rebuilds the books from statements and invoices while your old process keeps running; duplicates and miscodes surface here"},
        {"week": 3, "date": w(2), "what": "Reconcile to your last statement to the penny; owners loaded; portals and autopay open; board walkthrough"},
        {"week": 4, "date": w(3), "what": "Live. First packet lands by the 5th of the following month"},
    ]


SEQUENCE_A = [
    (0, "your financial packet date", "Hi {first},\n\nI run hey hoa, an accounting and back office for self-managed communities like {community}. One question: what day of the month does your board get financials? Most treasurers tell us the 20th or later. We deliver by the 5th, in the agreement, or that month is free.\n\nPricing is public: {monthly}/month for {units} doors on {tier}. Full proposal here: {proposal_url}\n\nIf it is useful, I can look at your last three bank statements and tell you what we would find, no charge: {review_url}\n\nOr grab 15 minutes and I will walk you through the board portal: {booking_url}\n\n{founder}"),
    (4, "re: your financial packet date", "One more thing that might matter: owners can text a question and get an answer with the bylaw section in about a minute. The board group chat gets quiet.\n\nHere is the board portal with demo data, no signup: {demo_url}\n\n{founder}"),
    (7, "a thing we found", "We did a free books review for a 48-door community last month and found duplicate landscaping payments the old firm never caught. Not saying you have that. Saying it takes us two days to check: {review_url}\n\n{founder}"),
    (11, "resale certificates", "Different angle: if a closing has ever been delayed waiting on a resale certificate, that is also us. Three business days, paid by the seller, never a board task again.\n\nIf a quick call is easier than email: {booking_url}\n\n{founder}"),
    (14, "closing the loop", "I will stop here. If timing is wrong, reply \"later\" and I will check in before your next budget season. If you want the free review, it is at {review_url}. Thanks for reading.\n\n{founder}"),
]


def founder_signature() -> str:
    """Who the sales emails are from. Configured, never hard-coded in a lane."""
    c = current_app.config
    return f"{c.get('FOUNDER_FIRST', 'Austin')}\n{c.get('FOUNDER_TITLE', 'founder, hey hoa')} · {c.get('FOUNDER_EMAIL', '')} · {brand.BRAND['phone']}"


def booking_url() -> str:
    return current_app.config.get("BOOKING_URL") or url_for("marketing.quote", _external=True)


def touch_context(lead) -> dict:
    q = quote(lead)
    return {
        "first": (lead.contact_name or "there").split(" ")[0], "community": lead.community_name or "your community", "units": q["units"], "tier": q["tier"]["name"],
        "monthly": f"${q['monthly']:,}", "proposal_url": proposal_url(lead), "review_url": url_for("marketing.books_review", _external=True),
        "demo_url": url_for("auth.login_role", role="board", demo=1, _external=True), "booking_url": booking_url(), "founder": founder_signature(),
    }


def render_touch(step: int, lead, founder: str | None = None) -> tuple[str, str]:
    day, subject, body = SEQUENCE_A[step]
    ctx = touch_context(lead)
    if founder:
        ctx["founder"] = founder
    return subject, body.format(**ctx)


# ---- replies -------------------------------------------------------------

def lead_for_email(email: str | None):
    """The most recent lead for this sender, if any. Replies to the founder land here."""
    from ..models import Lead

    if not email:
        return None
    return Lead.query.filter(db.func.lower(Lead.email) == email.strip().lower()).order_by(Lead.created_at.desc()).first()


def classify_reply(text: str) -> str:
    """later | stop | call | accept | question. Word-level, cheap, no model call; the founder reads the reply anyway."""
    t = (text or "").lower()
    first = t.strip().split("\n")[0][:200]
    if re.search(r"\b(unsubscribe|remove me|stop emailing|do not contact|not interested|no thanks)\b", t):
        return "stop"
    if re.search(r"\blater\b|next (year|quarter|budget)|budget season|not (right )?now|circle back", first):
        return "later"
    if re.search(r"\b(sign|accept|let's do it|lets do it|move forward|ready to start|send the agreement)\b", t):
        return "accept"
    if re.search(r"\b(call|phone|zoom|meet|meeting|walk ?through|demo|time (on|this|next))\b", t):
        return "call"
    return "question"


def stop_sequence(lead, reason: str) -> int:
    """Cancel every pending sequence touch for this lead. Returns the count stopped."""
    from ..models import WorkItem

    pending = WorkItem.query.filter_by(lane="sales", kind="followup", state="new").all()
    n = 0
    for wi in pending:
        if (wi.remote_ids or {}).get("lead_id") == lead.id:
            wi.state = "done"
            wi.proposal = {"action": "none", "preview": f"Sequence stopped: {reason}", "confidence": 1.0, "needs_review": False}
            n += 1
    db.session.commit()
    return n


def mark_replied(lead, text: str) -> str:
    """Record the first reply, stop the sequence, move the status. Returns the reply class."""
    kind = classify_reply(text)
    if not lead.replied_at:
        lead.replied_at = dt.datetime.now(dt.timezone.utc)
    if kind == "stop" and lead.status != "won":
        lead.status = "lost"
    elif kind == "accept" and lead.status not in ("won", "lost"):
        lead.status = "accepted"
    elif lead.status in ("new", "contacted", "proposal", "replied"):
        lead.status = "later" if kind == "later" else "replied"
    db.session.commit()
    stop_sequence(lead, f"{lead.contact_name or lead.email} replied ({kind})")
    return kind


def draft_reply(lead, kind: str, text: str) -> tuple[str, str]:
    """A short reply for the founder to edit and send. Never sent without a person in shadow mode."""
    ctx = touch_context(lead)
    first = ctx["first"]
    if kind == "call":
        body = f"Hi {first},\n\nHappy to. Pick any 15 minutes here and I will bring the portal with your numbers in it: {ctx['booking_url']}\n\nIf none of those work, send two times that do.\n\n{ctx['founder']}"
        return f"re: {lead.community_name} · a time to talk", body
    if kind == "accept":
        body = f"Hi {first},\n\nGreat. The agreement is in the proposal, one click to accept: {ctx['proposal_url']}\n\nAfter that you get the onboarding checklist (documents, statements, bank account) and we start the parallel rebuild the following Monday. Financials by the 5th business day from the first full month.\n\n{ctx['founder']}"
        return f"re: {lead.community_name} · next steps", body
    if kind == "later":
        body = f"Hi {first},\n\nUnderstood, I will check in before your next budget season and not before. If anything changes sooner, the proposal stays at {ctx['proposal_url']}.\n\n{ctx['founder']}"
        return f"re: {lead.community_name}", body
    if kind == "stop":
        return f"re: {lead.community_name}", f"Hi {first},\n\nDone, no more emails from me. Thanks for letting me know.\n\n{ctx['founder']}"
    body = f"Hi {first},\n\n[answer the question in two or three sentences; cite the proposal or the agreement where it applies]\n\nIf it is easier on a call: {ctx['booking_url']}\n\n{ctx['founder']}"
    return f"re: {lead.community_name}", body
