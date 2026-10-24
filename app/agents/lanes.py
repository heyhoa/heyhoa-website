"""The six agent lanes. Each has a prompt, a tool set and a demo planner."""
from __future__ import annotations

from flask import current_app, url_for

from .. import brand
from ..ai import assistant
from ..ai.prompts import HEY_SYSTEM
from ..integrations.registry import get_provider
from .base import RISK_READ, RISK_SEND, RISK_WRITE, Agent, Proposal
from .tools import pick

AUTO_SEND_CATEGORIES = {"balance", "payment", "autopay", "document", "rule_question", "status"}


class CSAgent(Agent):
    lane, name = "cs", "Customer service"
    description = "Owner, board and vendor communication on every channel. Answers what it can cite; hands money, disputes and emotion to people."
    system_prompt = HEY_SYSTEM + "\n\nYou are the customer-service lane. Use lookup_owner and get_ledger before answering account questions; who_fixes_what before answering who-repairs-what questions (cite its note); search_rules before answering rule questions; list_projects for when-is-X-getting-fixed questions. Reply with send_email or send_sms. Hand billing changes to the ar lane, invoices to ap, board decisions to board. Escalate disputes, waivers, threats and distress."
    tools = pick("lookup_owner", "get_ledger", "search_rules", "who_fixes_what", "list_projects", "list_decisions", "send_email", "send_sms", "post_note", "create_service_request", "handoff", "escalate")
    auto_execute_risks = {RISK_READ, RISK_SEND, RISK_WRITE}

    def plan(self, item):
        if item.kind == "board_approved":
            return Proposal(action="escalate", payload={"lane": "coordinator", "note": f"Board approved: {item.subject}. Carry it out and close the loop with the owner/vendor."}, preview=f"Board approved. Coordinator executes: {item.summary[:300]}", confidence=0.9, reason="board decision")
        if item.kind == "records_request":
            docs = get_provider().list_documents(item.community_id or "1001", board=True)
            inv = ", ".join(d.title for d in docs[:8])
            return Proposal(action="escalate", payload={"lane": "coordinator", "note": f"Statutory records request. On file: {inv}. Verify membership, produce or lawfully deny within the statutory clock."}, preview=f"Records request. Documents on file: {inv}. Coordinator verifies the requester is a member and produces within the statutory clock (SLA set).", confidence=0.9, sources=["document index", "records policy"], reason="statutory")
        t = assistant.triage_message(f"{item.subject}\n\n{item.summary}", known_owner=bool(item.unit_account_id))
        cat, route = t["category"], t["route"]
        item.category = cat
        if route in ("accountant", "board") or cat in ("dispute", "adjustment", "resale", "invoice", "violation"):
            lane = {"accountant": "ar", "board": "board"}.get(route, "ar")
            if cat == "invoice":
                lane = "ap"
            return Proposal(action="handoff", payload={"lane": lane, "note": f"{cat}: {t.get('summary', '')}"}, preview=f"Hand to {lane} lane ({cat}).", confidence=0.9, reason=cat)
        if cat == "maintenance" and item.unit_account_id:
            c = assistant.classify_request(item.summary or "")
            return Proposal(action="create_service_request", payload={"unit_account_id": item.unit_account_id, "category": c["category"], "summary": (item.summary or "")[:300]}, preview=f"File {c['category']} request for {item.unit_account_id} and confirm by email.", confidence=0.85, sources=["classifier"], reason="maintenance intake")
        if not item.unit_account_id:
            return Proposal(action="escalate", payload={"lane": "coordinator", "note": "sender not in roster"}, preview="Sender is not in the roster. A person should identify them.", confidence=0.6, reason="unknown sender")
        answer = assistant.ask(f"{item.subject}\n\n{item.summary}", role="homeowner", user={"community_id": item.community_id, "unit_account_id": item.unit_account_id})
        unsourced = answer.startswith("I am not finding")
        if unsourced or cat not in AUTO_SEND_CATEGORIES:
            return Proposal(action="send_email", payload={"to": item.counterpart_email, "subject": f"Re: {item.subject}", "body": answer}, preview=answer, confidence=0.5, reason="needs a person's eyes")
        return Proposal(action="send_email", payload={"to": item.counterpart_email, "subject": f"Re: {item.subject}", "body": answer}, preview=answer, confidence=0.9, sources=["ledger", "rules"], reason=f"sourced {cat} answer")


class ARAgent(Agent):
    lane, name = "ar", "Accounts receivable"
    description = "Dues, autopay, payment plans, the collections ladder (Exhibit B), NSF and adjustments requests. Money actions always get a person."
    system_prompt = HEY_SYSTEM + "\n\nYou are the accounts-receivable lane. Follow the collection policy exactly: stages by days past due, fees to the owner ledger, no lien or attorney below $400 or 75 days. Draft notices with send_notice. Payment plans within policy with create_payment_plan. Never waive a fee: escalate waivers to the accountant."
    tools = pick("lookup_owner", "get_ledger", "get_delinquencies", "search_rules", "send_notice", "create_payment_plan", "post_fine", "send_email", "post_note", "escalate", "handoff")
    auto_execute_risks = {RISK_READ}

    def plan(self, item):
        if item.kind == "board_approved":
            return Proposal(action="escalate", payload={"lane": "accountant", "note": f"Board approved: {item.subject}. Post in Caliber."}, preview=f"Board approved. Accountant posts in Caliber: {item.summary[:300]}", confidence=0.9, reason="board decision")
        if item.kind == "delinquency" and item.unit_account_id:
            d = next((x for x in get_provider().list_delinquencies(item.community_id or "1001") if x.unit_account_id == item.unit_account_id), None)
            if not d:
                return Proposal(action="none", preview="Account is no longer delinquent.", confidence=0.95)
            stage = next((s for s in reversed(brand.COLLECTION_STAGES) if d.days_late >= s[1]), brand.COLLECTION_STAGES[0])
            key, days, label, fee = stage
            if key in ("lien", "attorney") and not (d.balance >= brand.LIEN_THRESHOLD["balance"] or d.days_late >= brand.LIEN_THRESHOLD["days"]):
                return Proposal(action="none", preview=f"{d.unit_label}: below the lien threshold; keep sending pre-lien notices.", confidence=0.9)
            if key == "attorney":
                return Proposal(action="queue_board_decision", payload={"title": f"Attorney referral: {d.unit_label} (${d.balance:,.2f}, {d.days_late} days)", "body": f"Policy requires a board vote before attorney referral. Lien recorded. Balance ${d.balance:,.2f}.", "decision_type": "collections"}, preview=f"Ask the board to vote on attorney referral for {d.unit_label}.", confidence=0.9, reason="policy")
            body = assistant.draft_delinquency_notice(d, get_provider().get_community(item.community_id or "1001"))
            return Proposal(action="send_notice", payload={"unit_account_id": d.unit_account_id, "stage": key, "body": body, "channel": "email", "fee": fee}, preview=f"{label} to {d.unit_label} ({d.days_late} days, ${d.balance:,.2f}); fee ${fee} to the ledger.\n\n{body}", confidence=0.85, sources=["Exhibit B", "ledger"], reason=f"{d.days_late} days past due")
        t = assistant.triage_message(item.summary or "", known_owner=bool(item.unit_account_id))
        if t["category"] in ("adjustment", "dispute"):
            return Proposal(action="escalate", payload={"lane": "accountant", "note": t.get("summary", "")}, preview="Waiver or dispute: accountant decides.", confidence=0.9, reason=t["category"])
        if "plan" in (item.summary or "").lower() and item.unit_account_id:
            ua = get_provider().get_unit_account(item.unit_account_id)
            months = 6 if ua.balance > 900 else 3
            return Proposal(action="create_payment_plan", payload={"unit_account_id": ua.id, "months": months, "monthly_amount": round(ua.balance / months, 2)}, preview=f"Payment plan for {ua.unit_label}: {months} × ${ua.balance / months:,.2f}, $75 setup fee, collection steps paused while current.", confidence=0.85, sources=["policy: payment plans"], reason="owner asked for a plan")
        return Proposal(action="escalate", payload={"lane": "accountant", "note": "AR question needs a person"}, preview="Needs an accountant.", confidence=0.5)


class APAgent(Agent):
    lane, name = "ap", "Accounts payable & vendors"
    description = "Invoice intake and coding, duplicate and contract checks, W-9 and COI chasing, bid requests. Board approves, accountant releases."
    system_prompt = HEY_SYSTEM + "\n\nYou are the accounts-payable lane. For each invoice: check vendor_history for duplicates and the 12-month average, code to the right GL account, then post_invoice. Block vendors without a W-9 (request_vendor_document). Never pay anything; the board approves and the accountant releases."
    tools = pick("list_invoices", "vendor_history", "list_vendors", "post_invoice", "request_vendor_document", "send_email", "queue_board_decision", "escalate", "handoff")
    auto_execute_risks = {RISK_READ, RISK_WRITE}

    def plan(self, item):
        if item.kind == "board_approved":
            return Proposal(action="escalate", payload={"lane": "accountant", "note": f"Board approved: {item.subject}. Set up the vendor/contract or release per the bid; accountant handles the bank side."}, preview=f"Board approved. Accountant executes: {item.summary[:300]}", confidence=0.9, reason="board decision")
        vendors = get_provider().list_vendors(item.community_id or "1001")
        missing = [v for v in vendors if not v.w9_on_file]
        if item.kind == "vendor_compliance" and missing:
            v = missing[0]
            return Proposal(action="request_vendor_document", payload={"vendor_email": v.email, "document": "W-9", "vendor_name": v.name}, preview=f"Ask {v.name} for a W-9 (payments blocked until received).", confidence=0.9, reason="no W-9 on file")
        if item.kind == "invoice":
            inv = next((i for i in get_provider().list_invoices(item.community_id or "1001", status="pending_board") if i.id == (item.remote_ids or {}).get("invoice_id")), None)
            if inv:
                hist = [i for i in get_provider().list_invoices(item.community_id or "1001") if i.vendor == inv.vendor and i.id != inv.id]
                avg = sum(i.amount for i in hist) / len(hist) if hist else inv.amount
                flag = "" if abs(inv.amount - avg) / max(avg, 1) < 0.15 else f" Amount is {((inv.amount - avg) / max(avg, 1)) * 100:+.0f}% vs the vendor average (${avg:,.2f})."
                return Proposal(action="queue_board_decision", payload={"title": f"Approve {inv.vendor} {inv.number} · ${inv.amount:,.2f}", "body": f"{inv.description} · {inv.gl_account}.{flag} {inv.ai_note or ''}", "decision_type": "invoice"}, preview=f"Coded to {inv.gl_account}; queue for board approval.{flag}", confidence=0.9 if not flag else 0.7, sources=["vendor history"], reason="invoice intake")
        return Proposal(action="escalate", payload={"lane": "accountant", "note": "AP item needs a person"}, preview="Needs an accountant.", confidence=0.5)


class BoardAgent(Agent):
    lane, name = "board", "Board"
    description = "Keeps the board's decision list current, drafts digests, agendas, minutes and announcements. Never decides; surfaces."
    system_prompt = HEY_SYSTEM + "\n\nYou are the board lane. Keep the decision queue current, draft the Friday digest, agendas from the month's activity, and announcements from briefs. Boards decide; you surface and draft."
    tools = pick("list_decisions", "get_financials", "get_delinquencies", "send_board_digest", "send_email", "queue_board_decision", "escalate")
    auto_execute_risks = {RISK_READ, RISK_SEND}

    def plan(self, item):
        if item.kind == "digest":
            p = get_provider()
            cid = item.community_id or "1001"
            snap, inv, dq = p.get_financial_snapshot(cid), p.list_invoices(cid, status="pending_board"), p.list_delinquencies(cid)
            body = (f"Hi board,\n\nThis week at {p.get_community(cid).name}:\n\n• Decisions waiting: {len(inv)} invoices (${sum(i.amount for i in inv):,.2f}) in the approval queue\n"
                    f"• Cash: operating ${snap.operating_cash:,.0f}, reserves ${snap.reserve_cash:,.0f}\n• Delinquent: {len(dq)} accounts, ${sum(d.balance for d in dq):,.2f}; {sum(1 for d in dq if d.days_late >= 60)} past 60 days\n"
                    f"• Packet: {snap.recon_status}\n\nOpen the board portal to approve or ask hey.\n\n— hey")
            return Proposal(action="send_board_digest", payload={"body": body}, preview=body, confidence=0.9, sources=["snapshot", "AP", "AR"], reason="weekly digest")
        return Proposal(action="none", preview="Decision is on the board's list; nothing for hey to do until they vote.", confidence=0.9)


class CloseAgent(Agent):
    lane, name = "close", "Monthly close"
    description = "Nightly snapshots, cash and reconciliation checks, packet draft and board summary by the 5th."
    system_prompt = HEY_SYSTEM + "\n\nYou are the close lane. Snapshot, verify cash against the bank, flag variances over 10% or $500, draft the packet summary. The accountant signs off."
    tools = pick("snapshot_and_verify", "get_financials", "list_invoices", "get_delinquencies", "send_email", "escalate")
    auto_execute_risks = {RISK_READ}

    def plan(self, item):
        if item.kind == "board_approved":
            amt = (item.remote_ids or {}).get("amount")
            return Proposal(action="escalate", payload={"lane": "accountant", "note": f"Board approved money movement: {item.subject}{f' · ${amt:,.2f}' if amt else ''}. A person executes it in {current_app.config.get('BANK_NAME', 'the bank')} {current_app.config.get('BANK_PORTAL_NAME', 'Client Connect')} with the board's signers, records it in Caliber and attaches the confirmation to the decision. Software never moves money."}, preview=f"Board approved. Accountant executes in {current_app.config.get('BANK_PORTAL_NAME', 'Client Connect')} and records in Caliber: {item.summary[:300]}", confidence=0.95, reason="board decision")
        return Proposal(action="snapshot_and_verify", payload={}, preview="Snapshot the chart of accounts and verify cash and reconciliation status.", confidence=0.95, reason="nightly")


class OnboardingAgent(Agent):
    lane, name = "onboarding", "Onboarding"
    description = "Document inventory, interview capture, community brain entries, go-live checklist."
    system_prompt = HEY_SYSTEM + "\n\nYou are the onboarding lane. Track the PSA §4.1 document list, chase what is missing, turn the board interview into community-brain entries with sources."
    tools = pick("search_rules", "request_documents", "send_email", "escalate")
    auto_execute_risks = {RISK_READ, RISK_SEND}

    def plan(self, item):
        missing = (item.remote_ids or {}).get("missing") or ["Recorded CC&Rs", "Bylaws", "Last 12 bank statements", "Owner roster", "Vendor list with W-9s"]
        return Proposal(action="request_documents", payload={"to": item.counterpart_email or "board@example.com", "missing": missing}, preview="Email the liaison for: " + ", ".join(missing), confidence=0.9, reason="documents outstanding")


class SalesAgent(Agent):
    lane, name = "sales", "Sales"
    description = "Quote requests, proposals, outbound sequence A, free books reviews, follow-ups until a board says yes or later. The founder sends; hey drafts and keeps the calendar."
    system_prompt = HEY_SYSTEM + "\n\nYou are the sales lane. Treasurers are tired volunteers: be short, specific and honest. Quote the exact monthly number for their door count, link the written proposal, offer the free books review, never discount, never pressure. Schedule the next touch from sequence A unless they replied."
    tools = pick("send_email", "escalate")
    auto_execute_risks = {RISK_READ}

    def plan(self, item):
        from ..extensions import db
        from ..models import Lead
        from ..services import sales

        lead = db.session.get(Lead, (item.remote_ids or {}).get("lead_id") or 0)
        if not lead:
            return Proposal(action="escalate", payload={"lane": "coordinator", "note": "lead not found"}, preview="Lead record missing.", confidence=0.5)
        if item.kind == "lead":
            q = sales.quote(lead)
            subject = f"Your hey hoa proposal: ${q['monthly']:,}/month for {lead.community_name}"
            body = (f"Hi {(lead.contact_name or 'there').split(' ')[0]},\n\nThanks for the details on {lead.community_name}. For {q['units']} doors on {q['tier']['name']} the price is ${q['monthly']:,} a month (${q['per_door']:.2f} per door). "
                    f"Onboarding is free and takes three weeks. Financials land by the 5th business day every month or that month's fee is waived.\n\n"
                    f"The written proposal, with what is included, the onboarding calendar and the agreement in plain words: {sales.proposal_url(lead)}\n\n"
                    f"Two ways to go from here:\n1. Send three recent bank statements for a free books review and we tell you what we find within two business days: {url_for('marketing.books_review', _external=True)}\n"
                    f"2. Book 15 minutes and I will walk your board through the portal: {sales.booking_url()}\n\n{sales.founder_signature()}")
            return Proposal(action="send_email", payload={"to": lead.email, "subject": subject, "body": body}, preview=body, confidence=0.9, sources=["pricing", "lead"], reason=f"score {lead.score}, {q['tier']['name']} recommended")
        if item.kind == "followup":
            step = int((item.remote_ids or {}).get("step", 1))
            if lead.status in ("won", "lost") or (lead.status == "contacted" and step > 0 and (item.remote_ids or {}).get("replied")):
                return Proposal(action="none", preview=f"Lead is {lead.status}; sequence stopped.", confidence=0.95)
            subject, body = sales.render_touch(step, lead)
            return Proposal(action="send_email", payload={"to": lead.email, "subject": subject, "body": body}, preview=body, confidence=0.85, sources=["sequence A"], reason=f"touch {step + 1} of {len(sales.SEQUENCE_A)}")
        if item.kind == "reply":
            kind = (item.remote_ids or {}).get("reply_kind") or sales.classify_reply(item.summary or "")
            subject, body = sales.draft_reply(lead, kind, item.summary or "")
            if kind == "stop":
                return Proposal(action="none", preview=f"{lead.contact_name or lead.email} asked to stop. Lead marked lost, sequence stopped, nothing sent.", confidence=0.95, reason="opt-out")
            if kind == "later":
                return Proposal(action="send_email", payload={"to": lead.email, "subject": subject, "body": body}, preview=body, confidence=0.7, sources=["reply"], reason="asked for later; sequence stopped, status later. Founder confirms the note before it goes.")
            return Proposal(action="send_email", payload={"to": lead.email, "subject": subject, "body": body}, preview=body, confidence=0.6 if kind == "question" else 0.75, sources=["reply", "proposal"], reason=f"{kind} reply; founder edits and sends. Sequence stopped.")
        if item.kind == "books_review":
            return Proposal(action="escalate", payload={"lane": "accountant", "note": "Free books review: statements attached. Deliver the one-page findings memo within 2 business days."}, preview="Statements received for a free books review. Accountant delivers the findings memo in 2 business days; sales follows up with the proposal.", confidence=0.9, reason="offer")
        return Proposal(action="escalate", payload={"lane": "coordinator", "note": item.summary or ""}, preview="Sales item needs a person.", confidence=0.5)


AGENTS: dict[str, Agent] = {a.lane: a for a in (CSAgent(), ARAgent(), APAgent(), BoardAgent(), CloseAgent(), OnboardingAgent(), SalesAgent())}
