"""Outbound notifications for leads and website messages: Slack ping and an
email to the ops inbox. Website messages also become work items so hey ops
handles them like any other inbound. Best-effort; never raises."""
from __future__ import annotations

import logging

import requests
from flask import current_app

from ..channels import email as email_channel

log = logging.getLogger(__name__)


def _slack(text: str) -> bool:
    url = current_app.config.get("SLACK_WEBHOOK_URL")
    if not url:
        return False
    try:
        return requests.post(url, json={"text": text}, timeout=10).status_code < 300
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
    summary = lead_summary(lead)
    res = email_channel.send(current_app.config["LEAD_NOTIFY_EMAIL"], f"Quote request · {lead.community_name} · {lead.units} doors · score {lead.score}", summary, tag="lead")
    slack = _slack(f":house: New quote request: *{lead.community_name}* · {lead.units} doors · {lead.state} · score {lead.score} · {lead.contact_name} <{lead.email}>")
    return {"email": res, "slack": slack}


def deliver_contact_message(msg) -> dict:
    """Website message → work item (cs lane) + ops email + Slack for sales topics."""
    from ..agents import runtime

    try:
        item = runtime.inbound_portal(community_id=None, unit_account_id=None, kind="email", subject=f"[{msg.topic}] {msg.name}", body=msg.message, email=msg.email, name=msg.name, lane="cs")
        item_id = item.id
    except Exception as e:  # noqa: BLE001
        log.warning("work item for contact message failed: %s", e)
        item_id = None
    res = email_channel.send(current_app.config["LEAD_NOTIFY_EMAIL"], f"[{msg.topic}] website message from {msg.name}", f"{msg.message}\n\nFrom: {msg.name} <{msg.email}>\nWork item: #{item_id}", tag="website")
    slack = _slack(f":envelope: Website message ({msg.topic}) from {msg.name} <{msg.email}>: {msg.message[:200]}") if msg.topic in ("sales", "closing-docs") else False
    return {"email": res, "slack": slack, "work_item": item_id}
