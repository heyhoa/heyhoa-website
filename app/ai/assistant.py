"""hey's AI layer.

Two modes:
  * live  - ANTHROPIC_API_KEY set: calls the Claude API (Opus 5.5 by default) with
            server-side refusal fallbacks enabled.
  * demo  - no key: deterministic, rule-based answers so the portals work offline.

Every public function returns plain text (or a dict for classify_request) and
never raises on API failure; callers always get something renderable.
"""
from __future__ import annotations

import json
import logging
import re

from flask import current_app

from ..integrations import mock
from .prompts import CLASSIFY_SYSTEM, HEY_SYSTEM

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Live client
# --------------------------------------------------------------------------
def _client():
    key = current_app.config.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:  # pragma: no cover
        log.warning("anthropic SDK not installed; running in demo mode")
        return None
    return anthropic.Anthropic(api_key=key)


def _complete(system: str, user: str, max_tokens: int = 2000) -> str | None:
    client = _client()
    if client is None:
        return None
    try:
        resp = client.beta.messages.create(
            model=current_app.config.get("HEY_AI_MODEL", "claude-opus-5-5"),
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium"},
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        if resp.stop_reason == "refusal":
            return "I can't help with that one. I've passed it to a person who will follow up by email."
        return "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception as e:  # noqa: BLE001 - never break a portal page on AI failure
        log.exception("claude call failed: %s", e)
        return None


# --------------------------------------------------------------------------
# Context assembly (what hey is allowed to know for this question)
# --------------------------------------------------------------------------
def _context_for(role: str, user: dict) -> str:
    parts = []
    cid = user.get("community_id", "1001")
    community = mock.COMMUNITIES.get(cid)
    if community:
        parts.append(f"Community: {community.name}, {community.units} units, {community.city} {community.state}, dues {community.dues_frequency}.")
    parts.append("Governing docs on file: CC&Rs (2004), Bylaws (2019), Rules & Regulations (2024). Relevant sections: §7.2 ARC 30-day review; Rules §4 exterior modifications; Rules §6 parking (no trailers overnight on streets); Rules §9 rentals (min 30 days, register tenant). Pool season: May 1 – Oct 31, heated to 82°F.")
    parts.append("Collections policy (2025): reminder day 1, late notice day 30 ($25 fee), demand day 60, lien warning day 120, attorney by board vote. Payment plans up to 6 months without board vote.")
    if role == "homeowner" and user.get("unit_account_id"):
        ua = mock.UNIT_ACCOUNTS.get(user["unit_account_id"])
        if ua:
            parts.append(f"Owner: {ua.owner_name}, {ua.unit_label}, balance ${ua.balance:,.2f}, autopay {'on' if ua.autopay else 'off'}, next due {ua.next_due_date} ${ua.next_due_amount:,.2f}.")
            lines = mock.LEDGER.get(ua.id, [])
            parts.append("Ledger: " + "; ".join(f"{l.date} {l.description} {'+' + format(l.charge, '.2f') if l.charge else '-' + format(l.payment, '.2f')}" for l in lines[-10:]))
    if role == "board":
        snap = mock.MockProvider().get_financial_snapshot(cid)
        parts.append(f"Financial snapshot as of {snap.as_of}: operating cash ${snap.operating_cash:,.2f}, reserves ${snap.reserve_cash:,.2f} (82% funded), AR ${snap.ar_total:,.2f} (${snap.ar_over_60:,.2f} over 60d), AP pending ${snap.ap_pending:,.2f}.")
        parts.append("YTD expenses vs budget: " + "; ".join(f"{n} ${a:,.0f} vs ${b:,.0f}" for n, a, b in snap.expense_lines))
        parts.append("Prior year landscaping: $17,200. Vendors missing W-9: Fence Masters.")
        parts.append("Pending invoices: " + "; ".join(f"{i.vendor} {i.number} ${i.amount:,.2f} ({i.ai_note})" for i in mock.INVOICES.values() if i.status == "pending_board"))
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def ask(question: str, role: str = "visitor", context: str = "", user: dict | None = None) -> str:
    user = user or {}
    ctx = _context_for(role, user)
    live = _complete(HEY_SYSTEM, f"Role of the person asking: {role}.\n\nContext:\n{ctx}\n\nQuestion: {question}")
    if live:
        return live
    return _demo_answer(question, role, user)


def classify_request(text: str) -> dict:
    live = _complete(CLASSIFY_SYSTEM, text, max_tokens=300)
    if live:
        try:
            m = re.search(r"\{.*\}", live, re.S)
            if m:
                return json.loads(m.group(0))
        except ValueError:
            pass
    t = text.lower()
    rules = [
        ("Irrigation", ("sprinkler", "irrigation", "spray")), ("Lighting", ("light", "lamp", "bulb")),
        ("Fence", ("fence", "gate panel")), ("Roof", ("roof", "gutter", "shingle")), ("Plumbing", ("leak", "pipe", "water main")),
        ("Pool", ("pool", "spa")), ("Gate / access", ("gate", "code", "fob")), ("Pest", ("ant", "wasp", "rodent", "pest")),
        ("Landscaping", ("tree", "lawn", "mow", "bush", "mulch")),
    ]
    cat = next((c for c, kws in rules if any(k in t for k in kws)), "Other")
    urgent = any(k in t for k in ("flood", "gas", "sewage", "sparking", "fire"))
    return {"category": cat, "responsibility": "association" if cat in ("Irrigation", "Lighting", "Pool", "Gate / access", "Landscaping") else "unclear", "urgency": "urgent" if urgent else "normal", "summary": text[:60]}


def draft_delinquency_notice(d, community) -> str:
    stage_text = {
        "reminder": "friendly reminder", "late_notice": "late notice", "demand": "demand for payment", "lien_warning": "notice of intent to lien", "attorney": "attorney referral notice",
    }.get(d.stage, "notice")
    live = _complete(HEY_SYSTEM, f"Draft a {stage_text} letter from the {community.name} board to the owner of {d.unit_label}, {d.owner_name}, balance ${d.balance:,.2f}, {d.days_late} days past due. Offer a payment plan (up to 6 months). Under 180 words. Label it DRAFT.")
    if live:
        return live
    return (
        f"DRAFT — {stage_text.title()}\n\n"
        f"{d.owner_name}\n{d.unit_label}, {community.name}\n\n"
        f"Hi,\n\nYour account shows a balance of ${d.balance:,.2f}, now {d.days_late} days past due. "
        f"Under the association's collections policy this is the {stage_text} stage"
        f"{'; the next step is a lien warning' if d.stage == 'demand' else ''}.\n\n"
        f"You can pay online at any time, or set up a payment plan of up to six months in the portal with no board vote required. "
        f"If you believe this is in error, reply to this letter and we will review the ledger with you.\n\n"
        f"Thank you,\n{community.name} Board of Directors\n(sent on the board's behalf by hey hoa)"
    )


def draft_announcement(brief: str, community) -> dict:
    live = _complete(HEY_SYSTEM, f"Write a short owner announcement for {community.name} from this brief: '{brief}'. Return a first line that is the title, then a blank line, then the body (under 120 words).")
    if live and "\n" in live:
        title, _, body = live.partition("\n")
        return {"title": title.strip("# ").strip(), "body": body.strip()}
    items = [s.strip() for s in re.split(r"[,;]\s*|\s+and\s+", brief) if s.strip()]
    title = items[0].capitalize() if items else "Community update"
    body = "A few dates for your calendar:\n\n" + "\n".join(f"• {i[0].upper() + i[1:]}" for i in items) + "\n\nQuestions? Reply to this email or ask hey in the portal.\n\n— The Board"
    return {"title": title, "body": body}


# --------------------------------------------------------------------------
# Demo answers (no API key). Rule-based so the mock-ups are self-explanatory.
# --------------------------------------------------------------------------
def _demo_answer(q: str, role: str, user: dict) -> str:
    t = q.lower()
    if role == "homeowner":
        ua = mock.UNIT_ACCOUNTS.get(user.get("unit_account_id", ""), None)
        if any(k in t for k in ("balance", "owe", "paid", "assessment", "2025")):
            if ua:
                return f"Your balance is ${ua.balance:,.2f}. Your next assessment of ${ua.next_due_amount:,.2f} is due {ua.next_due_date}, and autopay is {'on' if ua.autopay else 'off'}. In 2025 you paid $3,720.00 in assessments across 12 payments (ledger). Want a PDF statement for your taxes?"
        if "pool" in t:
            return "The pool is open May 1 through Oct 31 and heated to 82°F (Rules & Regulations §8). Gate codes reset May 1 and go out by text the morning of."
        if "fence" in t:
            return "Yes, with an ARC application. Fences can be up to 6 ft, cedar or approved composite, and must stay inside your lot line (Rules §4.3). The committee has 30 days (CC&Rs §7.2); most decisions come back in under 10. Want me to start the application?"
        if "rent" in t or "airbnb" in t or "short-term" in t:
            return "Rentals must be 30 days or longer and the tenant must be registered with the association (Rules §9). Short-term rentals under 30 days are not permitted. I can send you the tenant registration form."
        if "trailer" in t or "park" in t:
            return "Trailers and RVs cannot be parked on the street overnight (Rules §6.2). Inside a closed garage is fine. For a one-night exception, message the board here and they usually say yes."
        if "payment plan" in t or "plan" in t:
            return "You can set up a plan of up to six months with no board vote needed (Collections policy §3). Pick the number of months on the Pay page and the first installment is due in 7 days. Late fees pause while the plan is current."
        if "gate" in t:
            return "For a stuck gate call Gate Pros, 24 hours, (512) 555-0133. For a code or fob, reply here with your unit and I will reissue it today."
        return "I am not finding that in the documents or your ledger, so I will not guess. I have sent it to a person on the hey team; you will get an email reply, usually within one business day."
    if role == "board":
        if "landscap" in t:
            return "Landscaping YTD is $18,500.00 (GL 6210), exactly on budget. Last year's comparable period was $17,200, so you are up 7.6%, which is the contract rate increase from March. All 10 GreenScape invoices this year matched the contract."
        if "w-9" in t or "w9" in t or "vendor" in t:
            return "One vendor is missing a W-9: Fence Masters. I have not released any payment to them and there is none pending. Their COI also expires Oct 30; I requested a renewal on Oct 1 and again on Oct 15."
        if "reserve" in t:
            return "Reserves are $162,480.00 (GL 1020), 82% funded against the 2026 Level II study. Contribution is $3,000/month (GL 9010), on schedule YTD at $36,000. Asphalt seal and stripe ($18,500) is due in 2027; the draft 2027 budget raises the contribution to $3,250."
        if "pool" in t and ("draft" in t or "notice" in t or "closing" in t):
            return "DRAFT — Pool closing\n\nThe pool closes for the season on Friday, Oct 31 at 8 pm. Gate codes will stop working at that time and the furniture will be stored the following week. Thank you for a great season.\n\n— The Board"
        if "rental" in t or "declaration" in t:
            return "The Declaration (CC&Rs §11.4) allows leasing of whole units only, for a minimum of 30 days, with the lease subject to the governing documents. Rules & Regulations §9 adds tenant registration within 10 days. There is no rental cap."
        if "invoice" in t or "pool" in t:
            return "Austin Pool Service #AP-889 is $640.00, 28% above the 12-month average of $498. The difference is a $142 chlorine shock treatment line. It sits in the AP queue with 0 of 2 approvals and the PDF attached."
        return "I can give you numbers from the GL, owner ledgers, invoices and the governing documents. I did not find that one, so I have not guessed. Rephrase, or I can route it to your coordinator."
    return "hey answers questions for owners and boards of communities it serves. Log in to ask about your community, or request a quote if you are a board looking to switch."
