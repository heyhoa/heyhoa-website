"""Letters: templates, audiences, sending by mail API or by hand. One Letter row per recipient."""
from __future__ import annotations

import datetime as dt

from flask import current_app

from .. import brand
from ..channels import mail as mail_channel
from ..extensions import db
from ..models import Letter

TEMPLATES: dict[str, dict] = {
    "general": {"label": "General letter to owners", "subject": "A note from the {community} board", "body": "Dear owner,\n\n{message}\n\nQuestions: reply to this letter, call {phone}, or sign in to the owner portal.\n\n{community} Board of Directors\nc/o hey hoa"},
    "meeting_notice": {"label": "Meeting notice", "subject": "{subject}", "body": "{message}"},
    "budget": {"label": "Annual budget and assessment letter", "subject": "{year} budget and assessment for {community}", "body": "Dear owner,\n\nThe board adopted the {year} budget on {date}. Your assessment will be {dues} {frequency} starting {start}.\n\n{message}\n\nThe full budget and the reserve plan are in the owner portal. Autopay adjusts automatically.\n\n{community} Board of Directors\nc/o hey hoa · {phone}"},
    "collection": {"label": "Collection notice (per Exhibit B)", "subject": "Past due assessment · {unit}", "body": "Dear {owner},\n\nOur records show a balance of {balance} on {unit} as of {date}.\n\n{message}\n\nPay in the portal, by bank bill pay, or by check to the lockbox. If you believe this is in error, or want a payment plan, call {phone} or reply in the portal.\n\nhey hoa for {community}"},
    "violation": {"label": "Courtesy / violation notice", "subject": "Courtesy notice · {unit}", "body": "Dear {owner},\n\n{message}\n\nPlease correct this within 14 days or let us know if it is already done. The governing document section is cited above. The board thanks you.\n\n{community} Board of Directors\nc/o hey hoa · {phone}"},
    "welcome": {"label": "Welcome letter (new owner)", "subject": "Welcome to {community}", "body": "Dear {owner},\n\nWelcome. Your assessment is {dues} {frequency}; the portal has your account, autopay, documents and a place to ask questions.\n\n{message}\n\n{community} Board of Directors\nc/o hey hoa · {phone}"},
}

AUDIENCES = [("all", "All owners"), ("no_email", "Owners without an email on file"), ("unit", "One unit")]


def render(kind: str, ctx: dict) -> tuple[str, str]:
    t = TEMPLATES.get(kind, TEMPLATES["general"])
    base = {"phone": brand.BRAND["phone"], "date": dt.date.today().strftime("%B %d, %Y"), "year": dt.date.today().year + 1, "message": "", "subject": "", "owner": "owner", "unit": "", "balance": "", "dues": "", "frequency": "", "start": ""}
    base.update({k: v for k, v in ctx.items() if v is not None})
    try:
        return t["subject"].format(**base), t["body"].format(**base)
    except (KeyError, IndexError):
        return t["subject"], t["body"]


def recipients(provider, community_id: str, audience: str, unit_account_id: str | None = None) -> list:
    owners = provider.list_unit_accounts(community_id)
    if audience == "unit" and unit_account_id:
        return [u for u in owners if u.id == unit_account_id]
    if audience == "no_email":
        return [u for u in owners if not u.email]
    return owners


def send(provider, community_id: str, *, kind: str, subject: str, body: str, audience: str = "all", unit_account_id: str | None = None, requested_by: str = "", certified: bool = False, meeting_id: int | None = None, announcement_id: int | None = None) -> dict:
    """Create and send one letter per recipient. Returns counts and cost."""
    sent = []
    for u in recipients(provider, community_id, audience, unit_account_id):
        ctx = {"owner": u.owner_name, "unit": u.unit_label, "balance": f"${u.balance:,.2f}" if u.balance else "$0.00"}
        s, b = (subject, body)
        try:
            s, b = subject.format(**ctx), body.format(**ctx)
        except (KeyError, IndexError):
            pass
        letter = Letter(community_id=community_id, kind=kind, unit_account_id=u.id, to_name=u.owner_name, to_address=getattr(u, "mailing_address", None) or u.address, subject=s, body=b, certified=certified,
                        meeting_id=meeting_id, announcement_id=announcement_id, requested_by=requested_by)
        r = mail_channel.send_letter(to_name=letter.to_name, to_address=letter.to_address or "", subject=s, body=b, certified=certified, description=f"{kind} · {community_id}")
        letter.status, letter.provider, letter.provider_id, letter.cost = r["status"], r["provider"], r.get("provider_id"), r.get("cost")
        letter.sent_at = dt.datetime.now(dt.timezone.utc) if r["status"] in ("sent", "simulated") else None
        db.session.add(letter)
        sent.append(letter)
    db.session.commit()
    return {"count": len(sent), "cost": float(sum(float(l.cost or 0) for l in sent)), "status": (sent[0].status if sent else "none"), "letters": sent}


def recent(community_id: str, limit: int = 100) -> list[Letter]:
    return Letter.query.filter_by(community_id=community_id).order_by(Letter.created_at.desc()).limit(limit).all()


def configured() -> bool:
    return mail_channel.configured()


def per_letter() -> float:
    return float(current_app.config.get("LETTER_COST", 1.45))
