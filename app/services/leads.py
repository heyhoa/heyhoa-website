"""Lead capture, scoring and routing."""
import logging

from ..extensions import db
from ..models import Lead

log = logging.getLogger(__name__)

ICP_STATES = {"AZ", "TX", "CO", "NC", "GA", "UT", "NV", "WA", "TN"}


def score_lead(lead: Lead) -> int:
    """Simple ICP fit score 0-100. Tune as we learn who closes."""
    score = 0
    units = lead.units or 0
    if 15 <= units <= 150:
        score += 35
    elif 8 <= units < 15 or 150 < units <= 300:
        score += 15
    if lead.current_setup in ("self", "accountant"):
        score += 25
    elif lead.current_setup == "management_co":
        score += 15
    if lead.contact_role in ("treasurer", "president"):
        score += 15
    if (lead.state or "").upper() == "AZ":
        score += 15
    elif (lead.state or "").upper() in ICP_STATES:
        score += 10
    pains = (lead.pain_points or "").lower()
    for hot in ("late financials", "reconcil", "collections", "volunteer", "burnout", "quickbooks"):
        if hot in pains:
            score += 5
    return min(score, 100)


def create_lead(data: dict, source: str | None = None) -> Lead:
    lead = Lead(
        community_name=data.get("community_name"),
        community_type=data.get("community_type"),
        units=_int(data.get("units")),
        state=(data.get("state") or "")[:2].upper() or None,
        city=data.get("city"),
        current_setup=data.get("current_setup"),
        pain_points=",".join(data.getlist("pain_points")) if hasattr(data, "getlist") else data.get("pain_points"),
        accounting_system=data.get("accounting_system"),
        fiscal_year_end=data.get("fiscal_year_end"),
        contact_name=data.get("contact_name"),
        contact_role=data.get("contact_role"),
        email=data.get("email"),
        phone=data.get("phone"),
        notes=data.get("notes"),
        source=source,
        plan=data.get("plan"),
        utm_source=data.get("utm_source"),
        utm_medium=data.get("utm_medium"),
        utm_campaign=data.get("utm_campaign"),
        referrer=(data.get("referrer") or "")[:300] or None,
    )
    lead.score = score_lead(lead)
    db.session.add(lead)
    db.session.commit()
    log.info("new lead %s score=%s", lead.id, lead.score)
    return lead


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
