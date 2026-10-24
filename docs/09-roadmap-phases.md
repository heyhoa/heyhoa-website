# 09 · Roadmap & phases

How to use this: each phase is a checklist. Work the unchecked boxes top to bottom. When a box is done, tick it, commit, and re-read the phase goal. Any box can be handed to an agent with the instruction "complete this box, run the tests, commit". Create one GitHub issue per unchecked box when you want external tracking (`scripts/make_issues.py` can do it from this file).

Status legend: `[x]` done · `[ ]` open · `[~]` in progress.

## Priority order (founders, Oct 24)
1. **Sales and marketing: the first customer.** Everything below that is not on this path waits.
2. **Board onboarding.** The interview, the document list, the community brain, Caliber setup, go-live.
3. **Board portal.** Live data, approvals, packet.
4. **Ops portal.** Agents out of shadow, close pipeline, collections.
5. **Homeowner portal.** Payments, requests, ask hey.

## Now (next three boxes, in order)
1. Phase 1 · Deploy: connect the repo on Render (render.yaml is in the repo), set secrets, point heyhoa.com, confirm CI green
2. Phase 1 · Postmark account: server token, inbound stream, SPF/DKIM on heyhoa.com, so proposals and sequence A actually send
3. Phase 1 · First 150-row outreach CSV from Texas management certificates, imported with `scripts/outreach_import.py`; founder approves touch 1 from the review queue

Keep this list to three. When one is done, tick its box below and promote the next.

## Phase 0 — Foundation (this commit)
Goal: plan, brand, mock-ups, scaffold. Everything renders with demo data.
- [x] Business model, marketing, GTM, brand, launch, outreach, product, architecture docs
- [x] `hey` mark traced to SVG (mark, white, lime, currentColor, three tiles)
- [x] Design system (`hey.css`) with dark marketing theme and light portal theme
- [x] Flask app factory, blueprints, config, models
- [x] Provider interface + mock provider with realistic demo data
- [x] FrontSteps CAPI2 client with endpoint coverage from the committed Swagger spec
- [x] Marketing site: 20 pages
- [x] Homeowner portal: 9 pages
- [x] Board portal: 16 pages, with working approve/hold/reject and ARC actions
- [x] AI layer with live (Claude) and demo modes
- [x] Smoke tests for every route

## Phase 1 — First customer (sales and marketing)
Goal: a signed community. Site live, proposals out, sequence running, books reviews delivered, reference calls available.
- [x] Placeholder testimonials removed; home shows three trust points, /reviews offers reference calls; real quotes added only with permission
- [x] Sample financial packet PDF (annotated) downloadable from `/pricing`, `/how-it-works` and the home page (`/sample-packet` is the HTML source; `node scripts/build_sample_packet.js` regenerates the PDF)
- [x] Lead notification: email to the ops inbox + Slack ping on new `Lead`, with score, plan and attribution (`services/notify.py`)
- [ ] Postmark account: server token, inbound stream → `/api/webhooks/postmark?token=…`, per-community aliases, SPF/DKIM on heyhoa.com
- [x] Quote form: plan preselect from `?plan=`, UTM capture, honeypot, rate limit
- [x] Sales lane: proposal email drafted on every quote, sequence A follow-ups scheduled (days 4, 7, 11, 14), stopped when a lead is contacted/lost; leads pipeline at `/ops/leads`
- [x] Web proposal per lead (`/proposal/<token>`): exact price, tier contents, onboarding calendar, agreement in plain words, accept button
- [x] Free books review page (`/books-review`) with uploads → sales work item for the accountant (2-business-day memo)
- [x] Pricing calculator on `/pricing`
- [x] Outreach import script + CSV template (`outreach/`)
- [ ] Books review: the memo template and the accountant's checklist (what we look for, how we present findings)
- [ ] Call booking link (Cal.com/Calendly) on proposal, quote-thanks and sequence emails
- [ ] Founder email identity for sequence A (name, signature, reply-to) and a reply handler that marks the lead contacted and stops the sequence
- [x] Contact form: becomes a work item in the CS lane plus an ops email and a Slack ping for sales topics
- [ ] Blog: move posts to markdown files, add RSS, add 9 more posts from the content calendar
- [ ] SEO: sitemap.xml, robots.txt, OG image per page, schema.org Organization + FAQ
- [ ] Analytics: privacy-friendly (Plausible) with quote-funnel events
- [ ] Legal: counsel review of `/terms`, `/privacy`, the 5th-or-free clause, state manager-licensing language
- [x] Deploy config: `render.yaml` (web + Postgres + two crons), `Procfile`, GitHub Actions CI, Postgres driver and URL normalisation
- [ ] Deploy: connect the repo on Render, set secrets, custom domain, TLS, confirm CI green
- [ ] Portal sidebar collapses to a top bar on phones (currently a full-screen nav list)
- [x] Services agreement template added to `legal/` and mapped to tiers, fees and collections (doc 11)
- [ ] Tailor the PSA for hey hoa: hey entity as Service Provider, term decision, 5th-or-free clause, hey hoa Exhibit A, AI review clause, state exhibits (AZ, TX); then counsel
- [ ] Founding-customer one-pager PDF
- [ ] Outreach: 150-row CSV of Central Texas treasurers from management certificates, imported; touch 1 approved and sent; Heywood community migration scheduled

## Phase 2 — Board onboarding, then the board portal on real data
Goal: the first community onboarded end to end (interview, documents, Caliber setup, go-live) and its board using the portal on real data. Homeowner-facing work waits unless the board needs it.
- [ ] FrontSteps tenant/sandbox API key; run the 13-step verification list in doc 12; record observed payloads; fix `_map_*` field names
- [x] COA snapshot job and budget model; period financials derived from snapshots (`services/financials.py`, `flask snapshot-coa`)
- [ ] Nightly cron for `snapshot-coa` on the host; opening snapshot on each community's go-live day
- [ ] Budget entry UI in the board portal (`BudgetLine`), approval recorded; budget vs actual on `/board/financials` from the service
- [ ] Bank reconciliation verification: statement balance entry (manual/CSV from First Citizens) vs COA cash; status on the financials page
- [ ] Magic-link auth (email), session hardening, CSRF (Flask-WTF), password-less board invites
- [ ] Link portal users to FrontSteps `contact` / `clientcontact` ids; owner sees only own unit account
- [ ] Homeowner: live ledger, statements (PDF proxy), autopay via `unitaccount/{id}/ach`
- [ ] Payments: hosted processor redirect from `paymentproviders`; webhook → `POST paymentaccepted`
- [ ] Board: live invoices queue with `invoice/{id}/{cc}/action`; approval rules from settings
- [ ] Board: live financial snapshot from COA snapshots + delinquencies + AP; packet PDF generation from the sample-packet template with real data
- [ ] Maintenance + ARC: write-through to `servicerequest` / `architectural/savenew` and document upload
- [ ] Documents: proxy `client/{id}/documents` with visibility flags
- [ ] Announcements: email (Postmark) + SMS (Twilio) delivery with opt-in tracking
- [x] hey ops: work items, six agent lanes with risk-tiered tools, review queue, shadow mode, Postmark inbound, scheduled daily agents (`app/agents/`, `/ops`)
- [x] Strict cash basis everywhere: COA, packet, balance sheet, docs
- [x] Board decisions queue with quorums per type (transfers, CDs, bids, work orders, ARC, assessments, budget, policies, collections, waivers, vendors, insurance, meetings); votes logged; approved → execution item
- [x] Board owner inbox: calls, texts, emails, portal requests with hey's answer; board replies under its own name
- [x] Board documents as system of record: upload with category, vendor, effective/expiry, owner visibility; 90-day expiry warnings
- [x] Reserve plan: upload study → extraction item; components, accrued vs balance, percent funded, suggested contribution, ten-year horizon
- [x] Owner spending page: paid bills minus board-flagged confidential bills; owners never see delinquencies, violations or other balances
- [x] Phone intake (Twilio TwiML): name, reason, callback → work item in the board inbox
- [x] Inbound data importer and intake guide (doc 15)
- [ ] Reserve study extraction in live mode (PDF → components via Claude) replacing the demo seed
- [ ] Per-community quorum settings and signer list for decisions; signatures on approved transfers
- [ ] Contract rates from Documents feed the AP lane's invoice matching
- [ ] Two weeks of shadow mode on the Heywood community; weekly 10% audit of agent-closed items; then `LIVE_COMMUNITIES` for CS/AP/Board lanes
- [ ] Portal: owners see their work items (status and outcome) under Requests; board sees Board-lane decisions in its decision list
- [ ] Live agent mode exercised end to end with a key: tool-use loop, token accounting, cost per item on the activity page
- [x] Agent-native surfaces: MCP server scoped by persona (`app/mcp_server.py`), agent discovery file, public community pages with JSON twins, statutory records requests with SLA (doc 14)
- [ ] MCP tokens issued and revoked from the portals (Settings → Connect your assistant); bearer auth on the HTTP transport; deploy the MCP server at mcp.heyhoa.com
- [ ] Board setting for what is public per community (documents, financial summary, packet, meetings); `PUBLISH_DEFAULTS` moves to the DB
- [ ] Vendor tools: W-9/COI upload via MCP and email attachments; vendor tokens issued at onboarding
- [ ] Board agent approvals: per-board switch allowing a member's assistant to approve contract-matched invoices under a threshold
- [ ] Community brain as data: profile, policies, decision rights, board notes with sources; `search_rules` reads it instead of the prompt context
- [ ] AP intake from email attachments: PDF → extraction → `post_invoice` proposal with the PDF attached as evidence
- [ ] Onboarding interview script + community-brain schema in the DB; first interview run with the Heywood community
- [ ] Audit log: every provider mutation and every AI action logged with inputs
- [ ] Onboarding runbook executed on customer #1 (doc 05 checklist)

## Phase 3 — hey does the work (month 2–3)
Goal: AI handles first pass on invoices, owner questions and letters at production quality.
- [ ] Governing-document ingestion: PDF → text → chunked index with section ids; citations resolve to page/section
- [ ] Owner Q&A with retrieval; confidence gate; unsourced → ticket to coordinator; weekly accuracy review
- [ ] Invoice intake: email/upload → extraction → GL coding + contract match + 12-month trend note → queue
- [ ] Bank feed ingestion (Plaid or bank export) → auto-match to invoices/payments → reconciliation exceptions
- [ ] Delinquency engine: policy stages as data; drafts generated on schedule; human send; proof of delivery
- [ ] ARC assistant: palette/rule check at submission; decision letter drafts; day-25 nudges
- [ ] Meeting assistant: agenda from month's activity; minutes from recording (transcript upload)
- [ ] Phone: Twilio Voice + streaming STT/Claude/TTS agent for balance, intake and rule questions; person handoff; call summary to ticket (doc 13 §2)
- [ ] Dessa access requested; local test rig against a test number; swap-in criteria defined
- [ ] Print-and-mail API (Lob/PostGrid) for statutory notices with proof of delivery
- [ ] Budget draft from actuals + reserve study
- [ ] Eval set: 100 real owner questions with gold answers; run on every prompt change
- [ ] Cost tracking per community for AI inference

## Phase 4 — Scale the business (month 4–6)
- [ ] Internal ops console: all communities, packet status board, exceptions queue, SLA timers for the 5th
- [ ] Resale/estoppel ordering with payment, generation from ledger + docs, 3-day SLA tracking
- [ ] Multi-community users (board member on two boards; staff)
- [ ] Violations module (Board+), vendor bid requests, insurance renewal tracking
- [ ] Second accounting backend or own ledger spike; decide by community #150
- [ ] State expansion checklist (TX governing-law PSA variant, CO, NC, GA, UT; FL/NV counsel)
- [ ] Partner portal for title companies (order + status)
- [ ] Case studies ×3, referral program, annual prepay option

## Running this recursively
Each phase box is sized to be done in one focused session. Suggested loop for an agent or a person:
1. Pick the top unchecked box in the lowest unfinished phase.
2. Read the related doc section (07 for pages, 08 for integration).
3. Implement; add or update a smoke test; run `pytest -q`.
4. Tick the box, commit with the box text as the message, push.
5. If the box exposed a new need, add a box under the right phase rather than widening the current one.
