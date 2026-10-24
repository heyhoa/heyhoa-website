"""Inbound ticket triage: Help Scout conversation → community + owner → hey.

Flow (doc 13 §2–3):
  1. identify the community from the alias the mail was sent to (or the mailbox)
  2. identify the owner from the sender's email against the roster
  3. classify the message and decide: hey replies / hey drafts for a person / board
  4. act in Help Scout (reply, or note + tags + assign) and mirror a PortalRequest
"""
from __future__ import annotations

import logging

from flask import current_app

from ..ai.assistant import ask, triage_message
from ..extensions import db
from ..integrations import helpscout as hs
from ..integrations.registry import get_provider
from ..models import AuditLog, PortalRequest

log = logging.getLogger(__name__)

# Categories hey may answer on its own when the answer is sourced and the owner is identified.
AUTO_SEND = {"balance", "payment", "autopay", "document", "rule_question", "status"}


def community_for(addresses: list[str]) -> tuple[str | None, dict | None]:
    """Map an alias like willowcreek@heyhoa.com to a community id via config ALIASES."""
    aliases = current_app.config.get("COMMUNITY_ALIASES", {})  # {"willowcreek@heyhoa.com": "1001"}
    for a in addresses:
        if a in aliases:
            cid = aliases[a]
            try:
                return cid, get_provider().get_community(cid).__dict__
            except Exception:  # noqa: BLE001
                return cid, None
    return None, None


def owner_for(community_id: str | None, email: str) -> dict | None:
    if not community_id or not email:
        return None
    for ua in get_provider().list_unit_accounts(community_id):
        if (ua.email or "").lower() == email:
            return ua.__dict__
    return None


def triage_conversation(conversation: dict, client: hs.HelpScoutClient | None) -> dict:
    convo_id = conversation.get("id")
    email = hs.extract_customer_email(conversation)
    text = hs.extract_latest_customer_text(conversation)
    subject = conversation.get("subject") or ""
    community_id, community = community_for(hs.extract_to_addresses(conversation))
    owner = owner_for(community_id, email)

    t = triage_message(f"{subject}\n\n{text}", known_owner=bool(owner))
    category, route = t["category"], t["route"]
    user = {"community_id": community_id or "1001", "unit_account_id": owner["id"] if owner else None, "name": (owner or {}).get("owner_name", "")}
    role = "homeowner" if owner else "visitor"
    draft = ask(f"{subject}\n\n{text}", role=role, user=user) if route in ("hey", "coordinator") else ""

    auto = route == "hey" and category in AUTO_SEND and owner is not None and not t.get("unsourced")
    action = "replied" if auto else "drafted"
    tags = [f"cat:{category}", f"route:{route}", f"hey:{action}"] + ([f"community:{community_id}"] if community_id else ["community:unknown"])

    if client and convo_id:
        try:
            if auto:
                client.reply(convo_id, email, draft, status="closed" if category in ("balance", "document", "status") else "active")
            else:
                note = f"hey triage · {category} · route {route}" + (f"\n\nOwner: {owner['owner_name']} · {owner['unit_label']} · balance ${owner['balance']:,.2f}" if owner else "\n\nSender not found in roster.") + (f"\n\nDraft reply:\n{draft}" if draft else "")
                client.note(convo_id, note)
            client.set_tags(convo_id, tags)
            assignee = current_app.config.get("HELPSCOUT_ASSIGNEE_" + route.upper())
            if not auto and assignee:
                client.assign(convo_id, int(assignee))
        except hs.HelpScoutError as e:
            log.warning("helpscout triage action failed: %s", e)
            action = "error"

    pr = PortalRequest(community_id=community_id, unit_account_id=owner["id"] if owner else None, kind="ticket", title=subject[:200], body=text, status="closed" if auto else "open", remote_id=f"hs:{convo_id}", ai_category=category, ai_summary=t.get("summary"))
    db.session.add(pr)
    db.session.add(AuditLog(actor="hey", action=f"ticket.{action}", target=f"hs:{convo_id}", detail=f"{category} → {route}; owner={'yes' if owner else 'no'}"))
    db.session.commit()
    return {"conversation_id": convo_id, "community_id": community_id, "owner_found": owner is not None, "category": category, "route": route, "action": action}
