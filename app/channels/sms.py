"""SMS transport: Twilio outbound. Simulated without credentials."""
from __future__ import annotations

import logging

import requests
from flask import current_app

log = logging.getLogger(__name__)


def send(to: str, body: str, from_number: str | None = None) -> dict:
    cfg = current_app.config
    sid, token = cfg.get("TWILIO_ACCOUNT_SID"), cfg.get("TWILIO_AUTH_TOKEN")
    sender = from_number or cfg.get("TWILIO_FROM")
    if not (sid and token and sender):
        log.info("[simulated sms] to=%s body=%s", to, body[:80])
        return {"delivered": False, "simulated": True, "id": None}
    try:
        r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", data={"To": to, "From": sender, "Body": body}, auth=(sid, token), timeout=15)
        ok = r.status_code < 300
        return {"delivered": ok, "simulated": False, "id": (r.json().get("sid") if ok else None)}
    except requests.RequestException as e:  # noqa: BLE001
        log.warning("twilio send error: %s", e)
        return {"delivered": False, "simulated": False, "id": None}
