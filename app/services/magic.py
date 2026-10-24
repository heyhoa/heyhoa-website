"""Magic links: log in from an email, act from an email. No passwords.

Two token kinds, both signed with the app secret and time-limited:
- login:  {m: member_id, c: community_id}            → session as that board member (7 days)
- action: {k: invoice|decision, i: id, a: action, m: member_id, c: community_id} → does the thing (14 days)
A link is for one person; the member id is inside it and the audit log records who clicked.
"""
from __future__ import annotations

from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ..extensions import db
from ..models import BoardMember

LOGIN_MAX_AGE = 7 * 24 * 3600
ACTION_MAX_AGE = 14 * 24 * 3600


def _s(salt: str):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=salt)


def login_token(member: BoardMember) -> str:
    return _s("magic-login").dumps({"m": member.id, "c": member.community_id})


def login_url(member: BoardMember) -> str:
    return url_for("auth.magic_login", token=login_token(member), _external=True)


def read_login(token: str) -> BoardMember | None:
    try:
        d = _s("magic-login").loads(token, max_age=LOGIN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    m = db.session.get(BoardMember, d.get("m"))
    return m if m and m.active else None


def action_token(kind: str, obj_id, action: str, member: BoardMember) -> str:
    return _s("magic-action").dumps({"k": kind, "i": str(obj_id), "a": action, "m": member.id, "c": member.community_id})


def action_url(kind: str, obj_id, action: str, member: BoardMember) -> str:
    return url_for("auth.magic_action", token=action_token(kind, obj_id, action, member), _external=True)


def read_action(token: str) -> tuple[dict | None, BoardMember | None, str | None]:
    """(payload, member, error)."""
    try:
        d = _s("magic-action").loads(token, max_age=ACTION_MAX_AGE)
    except SignatureExpired:
        return None, None, "This link has expired. Open the portal to act on it."
    except BadSignature:
        return None, None, "This link is not valid."
    m = db.session.get(BoardMember, d.get("m"))
    if not m or not m.active:
        return None, None, "This link belonged to a board member who is no longer on the roster."
    return d, m, None


def session_user(member: BoardMember) -> dict:
    return {"id": member.contact_id or f"member-{member.id}", "name": member.name, "email": member.email, "title": (member.role or "director").replace("_", " ").title(), "community_id": member.community_id, "role": "board"}
