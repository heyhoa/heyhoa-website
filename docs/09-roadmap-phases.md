# 09 · Roadmap & phases

How to use this: each phase is a checklist. Work the unchecked boxes top to bottom. When a box is done, tick it, commit, and re-read the phase goal. Any box can be handed to an agent with the instruction "complete this box, run the tests, commit". Create one GitHub issue per unchecked box when you want external tracking (`scripts/make_issues.py` can do it from this file).

Status legend: `[x]` done · `[ ]` open · `[~]` in progress.

## Now (next three boxes, in order)
1. Phase 1 · Sample financial packet PDF (annotated) downloadable from `/pricing` and `/how-it-works`
2. Phase 1 · Lead notification: email + Slack on new `Lead`
3. Phase 1 · Decide the term question (doc 11 decision 1) and send the PSA to counsel

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

## Phase 1 — Launch-ready site (week 1–2)
Goal: public site that converts; first customer signed by hand.
- [ ] Replace placeholder reviews with real quotes or remove the page until there are three
- [ ] Sample financial packet PDF (annotated) downloadable from `/pricing` and `/how-it-works`
- [ ] Lead notification: email + Slack on new `Lead`, with score and suggested tier
- [ ] Quote form: plan preselect from `?plan=`, UTM capture, honeypot, rate limit
- [ ] Contact form: email delivery (Postmark/SES)
- [ ] Blog: move posts to markdown files, add RSS, add 9 more posts from the content calendar
- [ ] SEO: sitemap.xml, robots.txt, OG image per page, schema.org Organization + FAQ
- [ ] Analytics: privacy-friendly (Plausible) with quote-funnel events
- [ ] Legal: counsel review of `/terms`, `/privacy`, the 5th-or-free clause, state manager-licensing language
- [ ] Deploy: Render/Fly with Postgres, custom domain, TLS, GitHub Actions running `pytest`
- [ ] Portal sidebar collapses to a top bar on phones (currently a full-screen nav list)
- [x] Services agreement template added to `legal/` and mapped to tiers, fees and collections (doc 11)
- [ ] Tailor the PSA for hey hoa: entity/brand line, term decision, 5th-or-free clause, hey hoa Exhibit A, AI review clause; then counsel
- [ ] Founding-customer one-pager PDF
- [ ] Outreach: list of 150 East Valley (AZ) treasurers from ACC filings, CRM set up, Sequence A loaded

## Phase 2 — Real data, real logins (week 3–6)
Goal: first community live on FrontSteps data; owners and board use the portals for real.
- [ ] FrontSteps tenant/sandbox API key; verify `ping`, `clientlist`, `chartofaccounts`, `ledger`; fix `_map_*` field names
- [ ] Magic-link auth (email), session hardening, CSRF (Flask-WTF), password-less board invites
- [ ] Link portal users to FrontSteps `contact` / `clientcontact` ids; owner sees only own unit account
- [ ] Homeowner: live ledger, statements (PDF proxy), autopay via `unitaccount/{id}/ach`
- [ ] Payments: hosted processor redirect from `paymentproviders`; webhook → `POST paymentaccepted`
- [ ] Board: live invoices queue with `invoice/{id}/{cc}/action`; approval rules from settings
- [ ] Board: live financial snapshot from COA + transaction accounts; packet PDF generation
- [ ] Maintenance + ARC: write-through to `servicerequest` / `architectural/savenew` and document upload
- [ ] Documents: proxy `client/{id}/documents` with visibility flags
- [ ] Announcements: email (Postmark) + SMS (Twilio) delivery with opt-in tracking
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
