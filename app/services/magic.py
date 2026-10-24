"""Signed one-click action links for emails: approve or reject a bill, approve or deny a vote.

The token names the member; the link only acts once that member is signed in on the device (password
and code, or a device trusted within MFA_TRUST_DAYS). Otherwise it parks the action and sends them to
sign in, then finishes. 14-day expiry, idempotent, audited under their name.
"""
from __future__ import annotations

from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ..extensions import db
from ..models import BoardMember

ACTION_MAX_AGE = 14 * 24 * 3600


def _s():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="magic-action")


def action_token(kind: str, obj_id, action: str, member: BoardMember) -> str:
    return _s().dumps({"k": kind, "i": str(obj_id), "a": action, "m": member.id, "c": member.community_id})


def action_url(kind: str, obj_id, action: str, member: BoardMember) -> str:
    return url_for("auth.magic_action", token=action_token(kind, obj_id, action, member), _external=True)


def read_action(token: str) -> tuple[dict | None, BoardMember | None, str | None]:
    try:
        d = _s().loads(token, max_age=ACTION_MAX_AGE)
    except SignatureExpired:
        return None, None, "This link has expired. Sign in to the portal to act on it."
    except BadSignature:
        return None, None, "This link is not valid."
    m = db.session.get(BoardMember, d.get("m"))
    if not m or not m.active:
        return None, None, "This link belonged to a board member who is no longer on the roster."
    return d, m, None
