"""Physical mail. Lob when configured; otherwise the letter is recorded and a person prints and mails it.

Either way the Letter row is the record: who, where, what, when, cost.
"""
from __future__ import annotations

import datetime as dt
import logging

import requests
from flask import current_app

log = logging.getLogger("hey.mail")


def configured() -> bool:
    return bool(current_app.config.get("LOB_API_KEY"))


def send_letter(*, to_name: str, to_address: str, subject: str, body: str, certified: bool = False, description: str = "") -> dict:
    """Returns {"status": sent|simulated|failed, "provider", "provider_id", "cost"}."""
    cost = float(current_app.config.get("LETTER_COST", 1.45)) + (6.50 if certified else 0.0)
    if not configured():
        log.info("mail (simulated) to %s: %s", to_name, subject)
        return {"status": "simulated", "provider": "manual", "provider_id": None, "cost": cost}
    parts = [p.strip() for p in to_address.replace("\n", ",").split(",") if p.strip()]
    line1 = parts[0] if parts else ""
    city_state_zip = parts[-1] if len(parts) > 1 else ""
    try:
        r = requests.post(
            "https://api.lob.com/v1/letters",
            auth=(current_app.config["LOB_API_KEY"], ""),
            data={
                "description": description or subject,
                "to[name]": to_name, "to[address_line1]": line1, "to[address_city]": city_state_zip.rsplit(" ", 2)[0] if city_state_zip else "",
                "to[address_state]": city_state_zip.rsplit(" ", 2)[-2] if city_state_zip.count(" ") >= 2 else "", "to[address_zip]": city_state_zip.rsplit(" ", 1)[-1] if city_state_zip else "",
                "from": current_app.config.get("LOB_FROM_ADDRESS", ""),
                "file": f"<html><body style='font-family:Helvetica;font-size:12pt;padding:1in'><h2>{subject}</h2><pre style='font-family:Helvetica;white-space:pre-wrap'>{body}</pre></body></html>",
                "color": "false", "extra_service": "certified" if certified else "",
            },
            timeout=20,
        )
        r.raise_for_status()
        j = r.json()
        return {"status": "sent", "provider": "lob", "provider_id": j.get("id"), "cost": cost, "expected_delivery": j.get("expected_delivery_date")}
    except Exception as e:  # noqa: BLE001
        log.warning("mail failed: %s", e)
        return {"status": "failed", "provider": "lob", "provider_id": None, "cost": 0.0, "error": str(e)}
