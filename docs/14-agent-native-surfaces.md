# 14 · Agent-native surfaces: when the homeowner has an agent too

The thesis: within a couple of years most owners, board members, vendors, realtors and lenders will have a personal agent that reads email, fills forms and calls tools for them. A back office that only has a website and a phone number will be hard for those agents to use, and the agents will route around it. hey should be the easiest HOA back office for *any* agent to work with, because we are one.

So every capability has three faces, built from the same code:
1. **A page** for a person (portals, community landing page).
2. **A tool** for an agent, over MCP, with the same auth scopes as the person.
3. **Structured, published data** with no login: what a community makes public, in JSON and in plain HTML, with a discovery file so an agent can find the tools.

Every write from any face becomes a work item in hey ops and goes through the same agent lanes and review policy. An owner's agent filing an ARC request is handled exactly like an owner typing it into the portal.

## The MCP server (`app/mcp_server.py`)
One server, scoped by token. A token belongs to a persona (owner of unit X, board member of community Y, vendor Z, a title company) and every tool checks the scope. Tokens are issued from the portals ("Connect your assistant") and revocable there.

| Scope | Tools (read) | Tools (write → work item) |
|---|---|---|
| homeowner | `my_account`, `my_ledger`, `my_statements`, `my_requests`, `community_documents`, `search_rules`, `community_profile`, `payment_link` | `set_autopay`, `request_payment_plan`, `file_service_request`, `submit_arc_request`, `request_records`, `message_board`, `update_contact` |
| board | all homeowner reads for the community + `financials`, `pending_approvals`, `delinquencies`, `vendors`, `budget_vs_actual` | `approve_invoice`, `decide_arc`, `draft_announcement`, `schedule_meeting`, `request_bids` |
| vendor | `my_invoices`, `payment_status` | `submit_invoice`, `provide_w9`, `provide_coi` |
| realtor / lender / title | `community_profile`, `fee_schedule` | `order_resale_package`, `order_lender_questionnaire`, `escrow_docs_alert` |
| public (no token) | `community_profile`, `published_financials`, `fee_schedule`, `public_documents`, `records_request_policy` | `request_records` (statutory records requests may come from members only; the tool asks for identity and creates a work item that verifies it) |

Discovery: `/.well-known/hey-agent.json` lists the MCP endpoint, scopes, how to get a token, and the public JSON per community. Each community landing page links it.

## Community landing pages (`/c/<slug>`)
A public page per community, no login: name, type, dues schedule, fee schedule, how to pay, how to file requests, board contact through hey, public documents (governing docs, rules, meeting notices and minutes where the board publishes them), published financials summary (if the board turns it on: cash, reserve funding %, last packet date, budget), the records-request process with the statutory timeline, and the agent discovery link. The same page in JSON at `/c/<slug>.json`. Boards choose what is public in Settings; the default is governing docs, fee schedule, meeting notices and the records policy.

## Records requests
Statutory in every state (AZ: A.R.S. § 33-1258 condo / § 33-1805 planned community, 10 business days, ≤ $0.15/page; TX: Tex. Prop. Code § 209.005, 10 business days, with a records production and copying policy). A request from a person or their agent creates a work item (kind `records_request`, CS lane, SLA = the statutory clock in business days). hey inventories what exists, drafts the production (or the lawful denial with the reason), the coordinator reviews, and delivery is logged with the date for the statute.

## Published financials
Boards can publish a monthly summary (cash, reserves, funding %, dues, budget headline, packet date) and optionally the full packet PDF. Agents and owners read it at `/c/<slug>.json`; nothing per-owner is ever public.

## Payment and AP approval processes, as tools
- Owner pay: `payment_link` returns the hosted processor URL for the owner's account; autopay and plans are proposals that the AR lane executes via the Caliber ACH endpoints.
- Board AP: `pending_approvals` lists what hey has coded; `approve_invoice` records the board member's approval through `invoice/{id}/{clientContactId}/action`; two approvals release; the accountant disburses in Caliber. A board member's agent can approve on their behalf only if the board enabled "agent approvals" and the invoice matches a contract exactly; otherwise the tool returns "needs the person" with the evidence.
- 1099s: vendors' agents can supply W-9s through `provide_w9`; January filing stays with the accountant; `my_invoices`/`payment_status` give vendors their YTD.

## Context: company and community
Two layers hey reads on every turn:
- **Company context** (one document, versioned): who we are, what we do and do not do, tone, escalation rules, fee schedule, SLAs, the promise, legal boundaries. Lives in `app/brand.py` and `docs/04`; moves to the DB in Phase 3.
- **Community context** (the community brain, doc 13 §4): profile, governing documents with section ids, policies as data, decision rights, vendors and contract rates, board notes with sources, escalation list, what is public.

## What I need from you to be confident we are building the right agents
Ranked by how much each changes the build.
1. **Three months of real inbound.** Every email, voicemail transcript and text the Heywood team received from owners, boards and vendors, with what was done about it. That is the eval set: it tells us the real category mix, what hey can answer from documents, and which escalations matter. Nothing else moves accuracy as much.
2. **One real community end to end.** Governing documents, the current ledger export, the last three packets, the vendor list with contracts, the board interview (doc 13 §4). That makes the community brain real and lets me check the Caliber field mappings against your data.
3. **The actual monthly close as Heywood does it today.** A screen recording or a written walk-through of a close in Caliber, including bank rec and payment release. The close agent and the accountant's checklist come from this.
4. **Heywood's current letter and notice templates** (collections, violations, ARC decisions, meeting notices, welcome letters). hey should draft in your voice, not mine.
5. **The board approval reality.** How many approvals, who really approves, what gets auto-approved today, how fast, what happens when a board member is unreachable.
6. **Call volume and reasons** for a month, even as tallies. Decides whether voice is Phase 2 or Phase 3.
7. **Which states in year one** and the governing-doc quirks you already know (rental caps, assessment caps, special assessment votes).
8. **Caliber read-only key and a tenant** (already discussed), and whether FrontSteps will give a sandbox write key.
9. **What a board must never see from hey, and what an owner must never see**, in your words. Becomes the escalation list and the public-data defaults.
10. **Risk appetite for agent autonomy**: which lanes you would let act alone first, and the dollar threshold under which a matched recurring invoice can be queued without a human look.
