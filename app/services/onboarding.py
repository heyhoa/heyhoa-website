"""Self-serve signup and onboarding.

A board member can sign up, sign the agreement and start without talking to anyone. The flow:
1. /start: community basics and who you are → a CommunityProfile (status signup) and a won lead.
2. /start/<token>/agreement: read the agreement, type your name, sign → status signed; agreement
   record keeps version, hash, signer, time, IP.
3. /start/<token>: the onboarding page. Intake (structured like the Caliber client), owner roster
   CSV, documents, board rules, bank. hey's onboarding lane chases what is missing.
4. Bank: accounts opened at the partner bank in the association's name; the board mails a start-up
   check (opening deposit) to the lockbox; after the parallel month, the final funds transfer from
   the old bank is also a check. Software never moves money.
5. Go-live: ops creates the Caliber client, sets provider_client_id, status live.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import pathlib
import re

from flask import current_app, url_for
from itsdangerous import BadSignature, URLSafeSerializer

from ..extensions import db
from ..models import ApprovalRule, CommunityProfile, Lead, OnboardingUnit
from . import sales

KINDS = [("hoa", "Single-family HOA"), ("townhome", "Townhomes"), ("condo", "Condominium"), ("mixed", "Mixed"), ("commercial", "Commercial")]
STRUCTURES = [("standalone", "Standalone association"), ("master", "Master association (has sub-associations)"), ("sub", "Sub-association (belongs to a master)")]
FREQUENCIES = [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("semiannual", "Twice a year"), ("annual", "Annual")]
PRIOR_SETUPS = [("self", "Self-managed, a volunteer keeps the books"), ("accountant", "An outside bookkeeper or CPA"), ("management_co", "A management company"), ("none", "Nobody, honestly")]

# What the Caliber client needs at go-live, in the order a treasurer can answer it.
INTAKE_FIELDS = [
    ("legal_name", "Legal name (as incorporated)", "Willow Creek Townhomes Association, Inc."),
    ("incorporation_state", "State of incorporation", "AZ"),
    ("ein_last4", "Last 4 of the EIN", "1234"),
    ("address1", "Mailing address", "1200 Willow Creek Dr"),
    ("city", "City", "Mesa"), ("state", "State", "AZ"), ("zip", "ZIP", "85201"), ("county", "County", "Maricopa"),
    ("fiscal_year_end", "Fiscal year end (MM/DD)", "12/31"),
    ("dues_amount", "Assessment amount per unit", "310"),
]

DEFAULT_RULES = {"invoice": 2, "transfer": 3, "investment": 3, "vendor_add": 2, "bid": 2, "arc": 2, "special_assessment": 3, "budget": 3, "collections": 2, "fee_waiver": 2}
RULE_LABELS = [("invoice", "Vendor invoices"), ("transfer", "Bank transfers"), ("investment", "CDs and investments"), ("vendor_add", "New vendors and contracts"), ("bid", "Bids and estimates"),
               ("arc", "Architectural requests"), ("special_assessment", "Special assessments"), ("budget", "Annual budget"), ("collections", "Liens and attorney referrals"), ("fee_waiver", "Fee waivers")]

DOCUMENTS = ["Recorded CC&Rs and amendments", "Bylaws", "Articles of incorporation", "Rules and policies", "Last 12 months of bank statements, every account", "Current budget", "Owner roster with mailing addresses",
             "Vendor list and contracts", "Insurance declarations pages", "Last reserve study", "Last tax return", "Minutes from the last 12 months"]


def _serializer():
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="onboard")


def token_for(profile) -> str:
    return _serializer().dumps({"p": profile.id})


def profile_from_token(token: str):
    try:
        pid = _serializer().loads(token)["p"]
    except (BadSignature, KeyError, TypeError):
        return None
    return db.session.get(CommunityProfile, pid)


def onboarding_url(profile) -> str:
    return url_for("marketing.onboard", token=token_for(profile), _external=True)


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")[:60] or "community"
    base, n = s, 2
    while CommunityProfile.query.filter_by(slug=s).first():
        s, n = f"{base}-{n}", n + 1
    return s


def agreement_text() -> str:
    p = pathlib.Path(current_app.root_path).parent / "legal" / "professional-services-agreement-template.md"
    return p.read_text() if p.exists() else "Professional Services Agreement (file missing)."


def agreement_hash() -> str:
    return hashlib.sha256((current_app.config.get("AGREEMENT_VERSION", "") + agreement_text()).encode()).hexdigest()


def _int(v):
    try:
        return int(str(v or "").replace(",", "").strip() or 0) or None
    except ValueError:
        return None


def start(form, *, source: str = "self-serve") -> CommunityProfile:
    """Step 1: community basics and the person. Creates the profile and a lead marked won."""
    units = _int(form.get("units"))
    plan = form.get("plan") or "back-office"
    lead = sales.lead_for_email(form.get("email")) or Lead(community_name=form.get("community_name"), community_type=form.get("kind"), units=units, state=(form.get("state") or "")[:2].upper() or None, city=form.get("city"),
                                                            current_setup=form.get("prior_setup"), contact_name=form.get("contact_name"), contact_role=form.get("contact_role"), email=form.get("email"), phone=form.get("phone"), source=source, plan=plan, score=95)
    lead.status = "accepted"
    db.session.add(lead)
    db.session.flush()
    profile = CommunityProfile(
        slug=slugify(form.get("community_name")), name=form.get("community_name"), kind=form.get("kind"), structure=form.get("structure") or "standalone", master_name=form.get("master_name") or None,
        units=units, unit_kind="lots" if form.get("kind") == "hoa" else "units", city=form.get("city"), state=(form.get("state") or "")[:2].upper() or None, dues_frequency=form.get("dues_frequency") or "monthly",
        plan=plan, monthly_price=sales.monthly_price(plan, units or 0), contact={"name": form.get("contact_name"), "title": form.get("contact_role"), "email": form.get("email"), "phone": form.get("phone")},
        board=[{"name": form.get("contact_name"), "title": form.get("contact_role"), "email": form.get("email"), "phone": form.get("phone"), "signer": True}],
        prior={"setup": form.get("prior_setup"), "manager": form.get("prior_manager") or "", "bank": form.get("prior_bank") or "", "software": form.get("prior_software") or ""},
        checklist={"intake": False, "roster": False, "documents": False, "rules": False, "bank": False}, bank={}, status="signup", lead_id=lead.id,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def sign(profile, *, signed_by: str, title: str, ip: str, user_agent: str) -> CommunityProfile:
    """Step 2: the e-signature record. Typed name + checkbox + time + IP + the agreement's hash."""
    profile.agreement = {"version": current_app.config.get("AGREEMENT_VERSION", ""), "sha256": agreement_hash(), "signed_by": signed_by, "title": title, "signed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                         "ip": ip, "user_agent": (user_agent or "")[:300], "plan": profile.plan, "monthly_price": profile.monthly_price, "term_months": 12, "notice_days": 30}
    profile.status = "signed"
    profile.go_live_on = profile.go_live_on or (dt.date.today() + dt.timedelta(days=28))
    for key, n in DEFAULT_RULES.items():
        if not ApprovalRule.query.filter_by(community_id=profile.community_id, decision_type=key).first():
            db.session.add(ApprovalRule(community_id=profile.community_id, decision_type=key, approvals=n))
    lead = db.session.get(Lead, profile.lead_id) if profile.lead_id else None
    if lead:
        lead.status = "won"
    db.session.commit()
    return profile


def save_intake(profile, form) -> CommunityProfile:
    for key, _, _ in INTAKE_FIELDS:
        v = (form.get(key) or "").strip()
        if key == "dues_amount":
            setattr(profile, key, float(v.replace(",", "").replace("$", "")) if v else None)
        elif key in ("state", "incorporation_state"):
            setattr(profile, key, v[:2].upper() or None)
        else:
            setattr(profile, key, v or None)
    for key in ("kind", "structure", "master_name", "dues_frequency"):
        if form.get(key):
            setattr(profile, key, form.get(key))
    if form.get("units"):
        profile.units = _int(form.get("units"))
    board = []
    for i in range(6):
        name = (form.get(f"b{i}_name") or "").strip()
        if name:
            board.append({"name": name, "title": form.get(f"b{i}_title") or "", "email": form.get(f"b{i}_email") or "", "phone": form.get(f"b{i}_phone") or "", "signer": bool(form.get(f"b{i}_signer"))})
    if board:
        profile.board = board
    cl = dict(profile.checklist or {})
    cl["intake"] = bool(profile.legal_name and profile.address1 and profile.fiscal_year_end and profile.dues_amount)
    profile.checklist = cl
    if profile.status == "signed":
        profile.status = "onboarding"
    db.session.commit()
    return profile


ROSTER_COLUMNS = {"unit": "unit_label", "unit_label": "unit_label", "lot": "unit_label", "address": "address", "property_address": "address", "owner": "owner_name", "owner_name": "owner_name", "name": "owner_name",
                  "email": "email", "phone": "phone", "mailing_address": "mailing_address", "mailing": "mailing_address", "balance": "balance", "notes": "notes"}


def import_roster(profile, data: bytes) -> int:
    """CSV with headers from ROSTER_COLUMNS (case-insensitive). Replaces the previous import."""
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    OnboardingUnit.query.filter_by(profile_id=profile.id).delete()
    n = 0
    for row in reader:
        rec = {}
        for k, v in row.items():
            col = ROSTER_COLUMNS.get((k or "").strip().lower().replace(" ", "_"))
            if col and v is not None:
                rec[col] = v.strip()
        if not rec.get("unit_label") and not rec.get("address"):
            continue
        bal = rec.pop("balance", "")
        try:
            rec["balance"] = float(bal.replace(",", "").replace("$", "")) if bal else None
        except ValueError:
            rec["balance"] = None
        db.session.add(OnboardingUnit(profile_id=profile.id, **rec))
        n += 1
    cl = dict(profile.checklist or {})
    cl["roster"] = n > 0
    profile.checklist = cl
    if n and not profile.units:
        profile.units = n
    db.session.commit()
    return n


def save_rules(profile, form) -> None:
    for key, _ in RULE_LABELS:
        n = _int(form.get(f"rule_{key}"))
        if n:
            r = ApprovalRule.query.filter_by(community_id=profile.community_id, decision_type=key).first() or ApprovalRule(community_id=profile.community_id, decision_type=key)
            r.approvals = max(1, min(n, 7))
            db.session.add(r)
    cl = dict(profile.checklist or {})
    cl["rules"] = True
    profile.checklist = cl
    db.session.commit()


def startup_amount(profile) -> float:
    """Opening deposit for the new operating account: one assessment cycle, with a floor."""
    per = float(profile.dues_amount or 0) * (profile.units or 0)
    cycle = {"monthly": 1, "quarterly": 1, "semiannual": 0.5, "annual": 0.25}.get(profile.dues_frequency or "monthly", 1)
    return max(float(current_app.config.get("STARTUP_CHECK_MIN", 2500)), round(per * cycle, 2))


def bank_step(profile, step: str, value=True, **extra) -> None:
    b = dict(profile.bank or {})
    b[step] = value
    b.update(extra)
    if step == "startup_check_mailed":
        b.setdefault("startup_amount", startup_amount(profile))
    profile.bank = b
    cl = dict(profile.checklist or {})
    cl["bank"] = bool(b.get("accounts_opened") and b.get("startup_check_received"))
    profile.checklist = cl
    if b.get("final_transfer_received") and profile.status in ("onboarding", "parallel"):
        profile.status = "parallel"
    db.session.commit()


def mark_documents(profile, done: bool) -> None:
    cl = dict(profile.checklist or {})
    cl["documents"] = done
    profile.checklist = cl
    db.session.commit()


def go_live(profile, provider_client_id: str) -> None:
    old = profile.community_id
    profile.provider_client_id = provider_client_id
    profile.status = "live"
    profile.go_live_on = dt.date.today()
    for r in ApprovalRule.query.filter_by(community_id=old).all():
        r.community_id = provider_client_id
    db.session.commit()


def progress(profile) -> dict:
    cl = profile.checklist or {}
    steps = [("signed", "Agreement signed", bool(profile.agreement)), ("intake", "Community details", cl.get("intake", False)), ("roster", "Owner roster imported", cl.get("roster", False)),
             ("documents", "Documents uploaded", cl.get("documents", False)), ("rules", "Board rules set", cl.get("rules", False)), ("bank", "Bank accounts open and funded", cl.get("bank", False))]
    done = sum(1 for _, _, ok in steps if ok)
    return {"steps": steps, "done": done, "total": len(steps), "pct": round(done / len(steps) * 100)}
