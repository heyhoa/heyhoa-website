"""Sales: quote math, proposal links, recommended tier, follow-up sequence."""
from __future__ import annotations

import datetime as dt

from flask import current_app, url_for
from itsdangerous import BadSignature, URLSafeSerializer

from .. import brand

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
    (0, "your financial packet date", "Hi {first},\n\nI run hey hoa, an accounting and back office for self-managed communities like {community}. One question: what day of the month does your board get financials? Most treasurers tell us the 20th or later. We deliver by the 5th, in the agreement, or that month is free.\n\nPricing is public: {monthly}/month for {units} doors on {tier}. Full proposal here: {proposal_url}\n\nIf it is useful, I can look at your last three bank statements and tell you what we would find, no charge: {review_url}\n\n{founder}"),
    (4, "re: your financial packet date", "One more thing that might matter: owners can text a question and get an answer with the bylaw section in about a minute. The board group chat gets quiet.\n\nHere is the board portal with demo data, no signup: {demo_url}\n\n{founder}"),
    (7, "a thing we found", "We did a free books review for a 48-door community last month and found duplicate landscaping payments the old firm never caught. Not saying you have that. Saying it takes us two days to check: {review_url}\n\n{founder}"),
    (11, "resale certificates", "Different angle: if a closing has ever been delayed waiting on a resale certificate, that is also us. Three business days, paid by the seller, never a board task again.\n\n{founder}"),
    (14, "closing the loop", "I will stop here. If timing is wrong, reply \"later\" and I will check in before your next budget season. If you want the free review, it is at {review_url}. Thanks for reading.\n\n{founder}"),
]


def render_touch(step: int, lead, founder: str = "Austin, hey hoa") -> tuple[str, str]:
    day, subject, body = SEQUENCE_A[step]
    q = quote(lead)
    ctx = {
        "first": (lead.contact_name or "there").split(" ")[0], "community": lead.community_name or "your community", "units": q["units"], "tier": q["tier"]["name"],
        "monthly": f"${q['monthly']:,}", "proposal_url": proposal_url(lead), "review_url": url_for("marketing.books_review", _external=True),
        "demo_url": url_for("auth.login_role", role="board", demo=1, _external=True), "founder": founder,
    }
    return subject, body.format(**ctx)
