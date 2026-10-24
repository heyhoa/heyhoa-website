"""Email transport: Postmark outbound + inbound webhook parsing.

Without POSTMARK_SERVER_TOKEN, sends are simulated (stored, delivered=False)
so the whole pipeline runs in demo mode.
"""
from __future__ import annotations

import logging

import requests
from flask import current_app

log = logging.getLogger(__name__)

POSTMARK_API = "https://api.postmarkapp.com/email"


def send(to: str, subject: str, body: str, *, from_addr: str | None = None, reply_to: str | None = None, tag: str | None = None, stream: str = "outbound") -> dict:
    """Send a plain-text email through Postmark. Returns {"delivered": bool, "id": ..., "simulated": bool}."""
    cfg = current_app.config
    token = cfg.get("POSTMARK_SERVER_TOKEN")
    sender = from_addr or cfg.get("POSTMARK_FROM") or cfg.get("LEAD_NOTIFY_EMAIL")
    if not token:
        log.info("[simulated email] to=%s subject=%s", to, subject)
        return {"delivered": False, "simulated": True, "id": None}
    payload = {"From": sender, "To": to, "Subject": subject, "TextBody": body, "MessageStream": stream}
    if reply_to:
        payload["ReplyTo"] = reply_to
    if tag:
        payload["Tag"] = tag
    try:
        r = requests.post(POSTMARK_API, json=payload, headers={"X-Postmark-Server-Token": token, "Accept": "application/json"}, timeout=15)
        ok = r.status_code < 300
        if not ok:
            log.warning("postmark send failed %s %s", r.status_code, r.text[:200])
        return {"delivered": ok, "simulated": False, "id": (r.json().get("MessageID") if ok else None)}
    except requests.RequestException as e:  # noqa: BLE001
        log.warning("postmark send error: %s", e)
        return {"delivered": False, "simulated": False, "id": None}


def parse_inbound(payload: dict) -> dict:
    """Normalise a Postmark inbound webhook JSON body."""
    from_full = payload.get("FromFull") or {}
    to_full = payload.get("ToFull") or []
    cc_full = payload.get("CcFull") or []
    to_addrs = [str(t.get("Email", "")).lower() for t in to_full] + [str(t.get("Email", "")).lower() for t in cc_full]
    if not to_addrs and payload.get("To"):
        to_addrs = [a.strip().lower() for a in str(payload["To"]).split(",")]
    attachments = [{"name": a.get("Name"), "content_type": a.get("ContentType"), "size": a.get("ContentLength"), "content": a.get("Content")} for a in payload.get("Attachments") or []]
    return {
        "from_email": str(from_full.get("Email") or payload.get("From") or "").lower(),
        "from_name": from_full.get("Name") or "",
        "to": to_addrs,
        "subject": payload.get("Subject") or "(no subject)",
        "text": payload.get("StrippedTextReply") or payload.get("TextBody") or "",
        "message_id": payload.get("MessageID"),
        "attachments": attachments,
    }
