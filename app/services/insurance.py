"""Insurance policies: the board's list, renewal dates, the agent, and the cyber nudge."""
from __future__ import annotations

import datetime as dt

from ..extensions import db
from ..models import InsurancePolicy

KINDS = [("property", "Property / master policy"), ("liability", "General liability"), ("do", "Directors & officers"), ("fidelity", "Fidelity / crime"), ("umbrella", "Umbrella"),
         ("workers_comp", "Workers' compensation"), ("cyber", "Cyber"), ("flood", "Flood"), ("other", "Other")]

RECOMMENDED = ["property", "liability", "do", "fidelity", "cyber"]


def policies(community_id: str) -> list[InsurancePolicy]:
    return InsurancePolicy.query.filter_by(community_id=community_id).order_by(InsurancePolicy.expires).all()


def gaps(community_id: str) -> list[str]:
    have = {p.kind for p in policies(community_id) if not p.expires or p.expires >= dt.date.today()}
    return [k for k in RECOMMENDED if k not in have]


def renewing(community_id: str, within_days: int = 60) -> list[InsurancePolicy]:
    return [p for p in policies(community_id) if p.days_to_expiry is not None and p.days_to_expiry <= within_days]


def _num(v):
    try:
        return float(str(v or "").replace(",", "").replace("$", "").strip() or 0) or None
    except ValueError:
        return None


def _date(v):
    try:
        return dt.date.fromisoformat(v) if v else None
    except ValueError:
        return None


def save(community_id: str, form, policy: InsurancePolicy | None = None) -> InsurancePolicy:
    p = policy or InsurancePolicy(community_id=community_id)
    p.kind = form.get("kind") or p.kind or "other"
    p.carrier = form.get("carrier", p.carrier)
    p.policy_number = form.get("policy_number", p.policy_number)
    p.coverage, p.deductible, p.premium = _num(form.get("coverage")), _num(form.get("deductible")), _num(form.get("premium"))
    p.begins, p.expires = _date(form.get("begins")), _date(form.get("expires"))
    p.agent_name, p.agent_phone, p.agent_email = form.get("agent_name"), form.get("agent_phone"), form.get("agent_email")
    p.notes = form.get("notes")
    if form.get("document_id"):
        p.document_id = int(form.get("document_id"))
    db.session.add(p)
    db.session.commit()
    return p


DEMO = [("property", "Farmers", "HO-2210934", 9_600_000, 10_000, 28_400, "2026-03-01", "2027-03-01", "Rosa Delgado", "(480) 555-0144"), ("liability", "Farmers", "GL-2210935", 2_000_000, 1_000, 3_900, "2026-03-01", "2027-03-01", "Rosa Delgado", "(480) 555-0144"),
        ("do", "Travelers", "DO-887120", 1_000_000, 2_500, 1_850, "2026-01-15", "2027-01-15", "Rosa Delgado", "(480) 555-0144"), ("fidelity", "Travelers", "CR-887121", 250_000, 1_000, 640, "2026-01-15", "2027-01-15", "Rosa Delgado", "(480) 555-0144")]


def seed_demo(community_id: str = "1001") -> int:
    n = 0
    for kind, carrier, num, cov, ded, prem, b, e, an, ap in DEMO:
        if not InsurancePolicy.query.filter_by(community_id=community_id, policy_number=num).first():
            db.session.add(InsurancePolicy(community_id=community_id, kind=kind, carrier=carrier, policy_number=num, coverage=cov, deductible=ded, premium=prem, begins=dt.date.fromisoformat(b), expires=dt.date.fromisoformat(e), agent_name=an, agent_phone=ap))
            n += 1
    db.session.commit()
    return n
