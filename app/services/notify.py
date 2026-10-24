"""Outbound notifications: new leads and contact messages to Help Scout and Slack.

Everything here is best-effort. A failure logs and returns False; it never
breaks the web request that triggered it.
"""
from __future__ import annotations

import logging

import requests
from flask import current_app

from ..integrations.helpscout import HelpScoutClient, HelpScoutError

log = logging.getLogger(__name__)


def _hs() -> HelpScoutClient | None:
    cfg = current_app.config
    if not (cfg.get("HELPSCOUT_APP_ID") and cfg.get("HELPSCOUT_APP_SECRET")):
        return None
    return HelpScoutClient(cfg["HELPSCOUT_APP_ID"], cfg["HELPSCOUT_APP_SECRET"])


def _slack(text: str, blocks: list | None = None) -> bool:
    url = current_app.config.get("SLACK_WEBHOOK_URL")
    if not url:
        return False
    try:
        r = requests.post(url, json={"text": text, **({"blocks": blocks} if blocks else {})}, timeout=10)
        return r.status_code < 300
    except requests.RequestException as e:  # noqa: BLE001
        log.warning("slack notify failed: %s", e)
        return False


def lead_summary(lead) -> str:
    tier = {"books": "Books", "back-office": "Back Office", "board-plus": "Board+"}.get(lead.plan or "", "no plan picked")
    pains = ", ".join(p for p in (lead.pain_points or "").split(",") if p) or "none listed"
    return (
        f"New quote request · score {lead.score}/100\n\n"
        f"Community: {lead.community_name} ({lead.community_type}, {lead.units} doors, {lead.city or '?'}, {lead.state or '?'})\n"
        f"Books today: {lead.current_setup} · software: {lead.accounting_system or '?'} · FYE: {lead.fiscal_year_end or '?'}\n"
        f"Pain: {pains}\n"
        f"Contact: {lead.contact_name} ({lead.contact_role}) · {lead.email} · {lead.phone or 'no phone'}\n"
        f"Plan: {tier}\nSource: {lead.source or 'direct'} · utm {lead.utm_source or '-'}/{lead.utm_medium or '-'}/{lead.utm_campaign or '-'}\n"
        f"Notes: {lead.notes or '-'}\n\n"
        f"Next: send the proposal within the business day (doc 06 sequence A, call script)."
    )


def notify_new_lead(lead) -> dict:
    """Create a Help Scout conversation in the sales mailbox and ping Slack."""
    result = {"helpscout": False, "slack": False}
    hs = _hs()
    mailbox = current_app.config.get("HELPSCOUT_MAILBOX_ID_SALES")
    if hs and mailbox:
        try:
            convo = hs.create_conversation(
                int(mailbox), subject=f"Quote request · {lead.community_name} · {lead.units} doors · score {lead.score}",
                customer_email=lead.email or current_app.config["LEAD_NOTIFY_EMAIL"], text=lead_summary(lead),
                first_name=(lead.contact_name or "").split(" ")[0], last_name=" ".join((lead.contact_name or "").split(" ")[1:]),
                tags=["lead", f"score-{(lead.score or 0) // 10 * 10}", lead.plan or "no-plan", (lead.state or "xx").lower()], imported=True,
            )
            result["helpscout"] = bool(convo)
        except HelpScoutError as e:
            log.warning("helpscout lead notify failed: %s", e)
    result["slack"] = _slack(f":house: New quote request: *{lead.community_name}* · {lead.units} doors · {lead.state} · score {lead.score} · {lead.contact_name} <{lead.email}>")
    return result


def deliver_contact_message(msg) -> dict:
    """Contact-form messages become real conversations in the support or sales mailbox."""
    result = {"helpscout": False, "slack": False}
    hs = _hs()
    cfg = current_app.config
    mailbox = cfg.get("HELPSCOUT_MAILBOX_ID_SALES") if msg.topic in ("sales", "closing-docs", "vendor") else cfg.get("HELPSCOUT_MAILBOX_ID_SUPPORT")
    if hs and mailbox:
        try:
            convo = hs.create_conversation(int(mailbox), subject=f"[{msg.topic}] from {msg.name}", customer_email=msg.email, text=msg.message, first_name=msg.name or "", tags=["website", msg.topic or "other"])
            result["helpscout"] = bool(convo)
        except HelpScoutError as e:
            log.warning("helpscout contact deliver failed: %s", e)
    if msg.topic in ("sales", "closing-docs"):
        result["slack"] = _slack(f":envelope: Website message ({msg.topic}) from {msg.name} <{msg.email}>: {msg.message[:200]}")
    return result
