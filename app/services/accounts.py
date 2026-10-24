"""Board member accounts: password + emailed code, set-password links, trusted devices.

Login: email + password → a 6-digit code is emailed → code → session. A device that completed the
code stays trusted for MFA_TRUST_DAYS; after that, the code again. Five wrong passwords lock the
account for 15 minutes. Codes expire in 10 minutes, are hashed at rest, single use, 5 attempts.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import secrets

from flask import current_app, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from ..channels import email as email_channel
from ..extensions import db
from ..models import BoardMember, LoginCode

CODE_TTL = dt.timedelta(minutes=10)
LOCK_AFTER, LOCK_MINUTES = 5, 15
SETUP_MAX_AGE = 7 * 24 * 3600


def _now():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def find(email: str) -> BoardMember | None:
    e = (email or "").strip().lower()
    return BoardMember.query.filter(db.func.lower(BoardMember.email) == e, BoardMember.active.is_(True)).first() if e else None


def session_user(m: BoardMember) -> dict:
    return {"id": m.contact_id or f"member-{m.id}", "member_id": m.id, "name": m.name, "email": m.email, "title": (m.role or "director").replace("_", " ").title(), "community_id": m.community_id, "role": "board"}


# ---- passwords ---------------------------------------------------------------

def set_password(m: BoardMember, password: str) -> None:
    if len(password or "") < 10:
        raise ValueError("Use at least 10 characters.")
    m.password_hash = generate_password_hash(password)
    m.password_set_at = _now()
    m.failed_logins, m.locked_until = 0, None
    db.session.commit()


def check_password(m: BoardMember, password: str) -> tuple[bool, str | None]:
    if m.locked_until and m.locked_until > _now():
        return False, f"Too many tries. Try again in {max(1, int((m.locked_until - _now()).total_seconds() // 60))} minutes."
    if not m.password_hash:
        return False, "No password yet. Use the link we emailed you to set one, or ask for a new link below."
    if check_password_hash(m.password_hash, password or ""):
        m.failed_logins = 0
        db.session.commit()
        return True, None
    m.failed_logins = (m.failed_logins or 0) + 1
    if m.failed_logins >= LOCK_AFTER:
        m.locked_until = _now() + dt.timedelta(minutes=LOCK_MINUTES)
        m.failed_logins = 0
    db.session.commit()
    return False, "That password is not right."


# ---- set-password links (invite, forgot) ------------------------------------

def _s():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="set-password")


def setup_url(m: BoardMember) -> str:
    return url_for("auth.set_password", token=_s().dumps({"m": m.id, "h": (m.password_hash or "")[-12:]}), _external=True)


def read_setup(token: str) -> BoardMember | None:
    try:
        d = _s().loads(token, max_age=SETUP_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    m = db.session.get(BoardMember, d.get("m"))
    if not m or not m.active or d.get("h") != (m.password_hash or "")[-12:]:
        return None  # link already used (password changed since) or member gone
    return m


def send_setup(m: BoardMember, reason: str = "invite") -> dict:
    first = m.name.split(" ")[0]
    if reason == "invite":
        body = (f"Hi {first},\n\nYou are on the board roster for the hey hoa portal. Set your password here (the link works for 7 days):\n\n{setup_url(m)}\n\n"
                f"After that you sign in with your email and password, and we email you a 6-digit code the first time on each device. Bills and votes also reach you by email with one-click links that open once you are signed in.\n\n— hey")
        subject = "Set up your hey hoa board login"
    else:
        body = f"Hi {first},\n\nHere is a link to choose a new password (7 days, one use):\n\n{setup_url(m)}\n\nIf you did not ask for this, ignore it; your password has not changed.\n\n— hey"
        subject = "Reset your hey hoa password"
    return email_channel.send(m.email, subject, body, tag="account")


# ---- second factor -----------------------------------------------------------

def _hash(code: str) -> str:
    return hashlib.sha256((current_app.config["SECRET_KEY"] + code).encode()).hexdigest()


def send_code(m: BoardMember) -> LoginCode:
    LoginCode.query.filter_by(member_id=m.id, used_at=None).delete()
    code = f"{secrets.randbelow(10**6):06d}"
    lc = LoginCode(member_id=m.id, code_hash=_hash(code), expires_at=_now() + CODE_TTL)
    db.session.add(lc)
    db.session.commit()
    email_channel.send(m.email, f"{code} is your hey hoa code", f"Hi {m.name.split(' ')[0]},\n\nYour sign-in code is {code}. It works for 10 minutes.\n\nIf you did not just sign in, change your password.\n\n— hey", tag="login-code")
    return lc


def verify_code(m: BoardMember, code: str) -> tuple[bool, str | None]:
    lc = LoginCode.query.filter_by(member_id=m.id, used_at=None).order_by(LoginCode.created_at.desc()).first()
    if not lc or lc.expires_at < _now():
        return False, "That code has expired. We sent a new one." if lc else "No code is pending. Sign in again."
    if lc.attempts >= 5:
        return False, "Too many tries. Sign in again for a new code."
    if lc.code_hash != _hash((code or "").strip().replace(" ", "")):
        lc.attempts += 1
        db.session.commit()
        return False, "That code is not right."
    lc.used_at = _now()
    db.session.commit()
    return True, None


def device_trusted() -> bool:
    at = session.get("mfa_at")
    if not at:
        return False
    try:
        return (_now() - dt.datetime.fromisoformat(at)).days < current_app.config.get("MFA_TRUST_DAYS", 30)
    except ValueError:
        return False


def sign_in(m: BoardMember, *, mfa_done: bool) -> None:
    session.permanent = True
    session["role"] = "board"
    session["user"] = session_user(m)
    if mfa_done:
        session["mfa_at"] = _now().isoformat()
    m.last_login_at = _now()
    db.session.commit()
