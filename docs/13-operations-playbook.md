# 13 · Operations playbook: an AI-first team

Goal: one accountant and one coordinator run 80–120 communities, because hey does the first pass on everything and people do judgment, signatures and the Caliber UI tasks the API cannot. This doc says who does what, through which channel, with what tooling, and how far each task is automated. It assumes doc 12 (what Caliber's API can do).

## 1. Operating principles
1. **Everything is a work item in hey ops.** Every inbound (email, text, call, portal form, lockbox exception, bank exception, Caliber signal, scheduled check) becomes a work item with a community, a unit (if any), a kind, an owning agent lane, a state, an SLA, evidence and a proposed action. Nothing lives in a personal inbox or in a third-party help desk. We do not use human-first tools as the system of record; the agents are the team and hey ops is where people review them.
2. **Agent first, person second, board last.** The lane's agent resolves what it can source and execute within policy. A person reviews proposals the policy holds back. The board only sees decisions: approvals, votes, policy. Boards do not get work items; they get a "needs a decision" list.
3. **Write to Caliber through the small write surface; log everything.** Any Caliber write hey makes is logged with the payload and shown in the board activity log. Anything outside the write surface becomes a ticket for the accountant's Caliber seat.
4. **Drafts are drafts.** Letters, notices, announcements, minutes, budgets: hey writes, a person sends. Payments: two board approvals, accountant releases.
5. **Measure the two numbers that matter:** percent of tickets closed by hey without a person (target 70%+), and zero incorrect sourced answers (weekly audit of a sample).

## 2. Channels

### Email (`help@heyhoa.com` plus one alias per community)
- **Postmark** is the transport, nothing more. Inbound mail to any `@heyhoa.com` address hits the inbound webhook (`/api/webhooks/postmark`); the address identifies the community (`willowcreek@heyhoa.com` → community 1001 via `COMMUNITY_ALIASES`). Outbound goes through the same provider with per-lane tags. Threads live in our database on the work item. There is no mailbox UI; people read threads in hey ops.
- The CS agent reads every inbound: identifies the community and the owner (from the roster), classifies, drafts, and either sends (sourced, low-risk categories, when the community is out of shadow) or proposes for a person in the review queue. It hands billing to the AR agent, invoices to AP, decisions to Board.
- Categories hey sends on its own after a confidence check: balance and payment questions, document requests, "what does the rule say", autopay setup, contact changes it already made, status of a request. Everything with money adjustments, disputes, legal threats, emotion or a board decision goes to a person with a draft attached.
- Reply time targets: hey under 2 minutes; person under 4 business hours; board decision items surfaced same day.

### Text (SMS)
- One number per community via Twilio. Owners opt in during onboarding (the mail matrix in Caliber records preference).
- Outbound: payment confirmations, late notices (as a courtesy ahead of the mailed notice), gate codes, announcements the board marks "text".
- Inbound: same pipeline as email. Short answers, link to the portal for anything longer.

### Phone
- **Keep it simple (founders' call).** One national number and per-community numbers (Twilio Voice). The phone says "Hey, thanks for calling", asks for the caller's name and unit, asks what they need, confirms the callback number, and says it will pass this to the board. That creates a work item: the board sees it in the owner inbox, the CS agent drafts the follow-up, and a person or the board replies. Built: `/api/webhooks/twilio/voice` (TwiML, speech gathering, no model in the loop).
- Later, if call volume justifies it: a conversational agent for balance and rule questions on the same number, with Dessa as the speech layer when it is hostable. Not before.
- What the phone may never do: waive a fee, discuss another owner's account, give legal advice, promise an outcome.
- Every call's speech results are attached to the work item. Calls that come to a person are logged in hey ops (Log a call) and the CS agent takes it from there.

### Portal
- Owner and board portals are the preferred channel; email and phone nudge toward them ("I've put the form in your portal; tap here"). Portal forms create work items like any other channel.
- "Ask hey" in both portals uses the same brain as email and phone, with the user already identified.

### Mail
- Outbound letters (collection notices that policy or statute require by mail, annual meeting notices, ballots) go through a print-and-mail API (Lob or PostGrid) with proof of delivery stored on the work item. Inbound mail goes to a scanning service; checks go to the lockbox, never to us.

## 3. hey ops: work items, agents, review
Built in `app/agents/` and `app/blueprints/ops/`.

- **Work item** fields: community · unit/owner · counterpart (email/name) · kind (email, sms, call, portal_form, delinquency, invoice, vendor_compliance, close, digest, decision, onboarding) · lane · state (new → working → proposed → approved → done, or escalated / rejected / failed) · priority · SLA due · evidence · proposal (action, payload, preview, confidence, sources, reason) · reviewer and outcome. Messages (any channel, any direction) and agent runs hang off it.
- **Six agent lanes**, each a system prompt + tools + policy: **CS** (communication), **AR** (dues, autopay, plans, Exhibit B ladder), **AP** (invoices, vendors, W-9/COI), **Board** (decision list, digests, agendas, minutes, announcements), **Close** (snapshots, cash checks, packet), **Onboarding** (documents, interview, community brain). Lanes hand items to each other.
- **Tools carry a risk level.** `read` tools run freely while the agent thinks. `write` (Caliber notes, service requests, invoice posting), `send` (email, text) and `money` (fines, payment plans, notices with fees) become the proposal. Money always waits for a person. Send and write wait for a person in shadow mode, or when the lane's policy or the confidence floor says so.
- **Shadow mode** (`SHADOW_MODE=true`, default) means every proposal is reviewed. Take a community out of shadow with `LIVE_COMMUNITIES=1001` after two clean weeks; then the CS lane answers sourced questions on its own, AP posts coded invoices for board approval on its own, Board sends digests on its own. AR never sends a notice without a person.
- **Review queue**: one screen per item with the thread, the evidence, the proposal and an editable body. Approve executes exactly what is on screen; reject sends nothing; re-run moves it to another lane. Everything lands in the audit log (board portal shows the community's slice).
- **Scheduled work** (`flask agents-daily` or `POST /api/agents/daily?token=…` from cron): AR items for every delinquent account, AP items for pending invoices and W-9 gaps, a Close check per community, a Board digest on Fridays. Idempotent: an open item per account/invoice is reused.
- **Modes**: `demo` planners (deterministic, no API key) or `live` (Claude with tool use). Same proposal shape either way, so the console and the tests do not care.
- Weekly review: every item an agent closed on its own gets sampled (10%) by the coordinator; errors become eval cases.

## 4. Onboarding: capturing the context hey needs
Onboarding is where most of hey's later accuracy is decided. We run a structured interview with a board member (usually the president or treasurer) and turn it into the **community brain**: a versioned knowledge base per community, stored in our DB and used in every hey prompt.

### Board interview (60–90 minutes, video, recorded and transcribed)
1. **People and roles.** Board members, officers, committees, who signs, who approves what, the liaison, how the board likes to be contacted, meeting cadence.
2. **How money works today.** Bank(s), who pays bills, how owners pay, late-fee practice vs policy, payment plans given in the past, the last audit/review, the reserve study, the budget process and dates.
3. **Rules in practice.** The CC&Rs say X; what does the board actually enforce? Parking, rentals, pets, exterior changes, pools, trash, noise. Which rules get complaints. Known exceptions and grandfathered items.
4. **Vendors.** Who does what, contract terms, who the board trusts, who they want replaced, emergency contacts, gate/access provider.
5. **Owners.** Known difficult accounts (with care), long-term renters, investor owners, owners with accessibility needs, language preferences.
6. **History.** Litigation, special assessments, insurance claims, recent elections, anything an owner might ask about that is not written down.
7. **Tone.** How the board wants hey to sound to owners; words to avoid; what hey should always escalate.

### Community brain (what we store)
- Profile: type, units, fiscal year, dues schedule, bank, key dates.
- Governing documents, ingested and chunked with section ids (Phase 3), plus a plain-language rules digest written by hey and approved by the board.
- Policies as data: collections ladder and fees (Exhibit B), ARC rules and palette, fine schedule, payment plan rules, approval thresholds.
- Decision rights: who approves what, quorum rules, signers.
- Vendors with roles, contacts, COI/W-9 status, contract rates (for invoice matching).
- "Board says" notes from the interview, tagged by topic, with dates, so hey can answer "can I park a trailer" the way the board actually enforces it.
- Escalation list: topics hey must never answer alone for this community.
- Every item has a source (document section, interview timestamp, board email) so hey can cite it.

### Onboarding checklist, with automation level
| Step | Who | Auto |
|---|---|---|
| Agreement signed, board liaison named, insurance certificates | coordinator | D (hey drafts the request list and chases) |
| Documents collected (PSA §4.1 list) | coordinator | D (upload portal; hey inventories what is missing) |
| Caliber client setup, units, COA, billing records, bank integration | accountant, Caliber UI | UI |
| Opening balances, reconciliation to last statement | accountant | UI + hey verifies COA vs statement |
| Owner roster loaded and verified; portal invites | hey | A (API read + our invites) |
| Vendor list loaded, W-9/COI requested | hey | A (`POST vendor`), D for chasing |
| Board interview → community brain | coordinator + hey | D |
| Governing docs ingested; 20 test questions answered and checked by the board | hey + board | D |
| Policies entered (collections, ARC, fines, plans) | coordinator | D |
| Budget and reserve study entered | accountant | D |
| Welcome email/text to owners; autopay drive | hey | A |
| First packet date on the calendar; founder owns it | all | — |

## 5. Runbooks

### Daily (hey, automatic; coordinator skims the exception list)
- Snapshot every community's chart of accounts (API) → our DB.
- Pull new invoices from the AP inbox (email) and uploads → extract, code, duplicate/contract check → `POST invoice` + PDF → board queue. Exceptions (unknown vendor, missing W-9, amount > threshold) → ticket.
- Pull applied payments and pending payments → post confirmations to owners → flag NSF/returns → ticket for accountant.
- Pull delinquencies → compute stage per Exhibit B → draft the day's notices → coordinator sends → `addnote` + fee via `postfine`.
- Process inbound email/text/call tickets.
- Pull service requests and ARC items → nudge vendors/committees on SLAs.
- Watch COI expirations, W-9 gaps, insurance renewals → tickets.

### Weekly (coordinator, 2 hours per 20 communities)
- Review hey's auto-resolved sample.
- Chase open vendor bids and board decisions older than 7 days.
- Send the board a Friday note: decisions pending, money in/out, anything unusual (hey drafts).

### Monthly close (accountant, with hey)
| Day | Step | Auto |
|---|---|---|
| 1 | Opening snapshot; hey drafts packet from snapshots, delinquencies, AP, budget | A |
| 1–3 | Bank reconciliation in Caliber (bank integration); accountant clears exceptions; hey verifies cash GL vs statement balance | UI + A verify |
| 2–3 | Adjustments and late-fee review in Caliber (cash basis: no accruals, ever) | UI |
| 3–4 | hey re-renders packet, writes the board summary, flags variances > 10% or > $500 | A |
| 4–5 | Accountant review and sign-off in our portal; board package (10 sections) and homeowner package (first 4) delivered; board notified; "5th" SLA timer closes | D |
| any | **Money movement.** Board decision (transfer, CD purchase/redemption, wire) → accountant executes in First Citizens Client Connect with the board's signers → confirmation attached to the decision → recorded in Caliber. Never automated. | UI, always |
| 5+ | Board meeting agenda drafted from the month | A |

### Collections (Exhibit B as data)
hey computes stage daily; drafts the notice from the ledger and policy; coordinator sends (email + mail where required) and the fee posts to the owner ledger; `addnote` records it; at the $400/75-day threshold hey prepares the lien packet for the accountant; attorney referral only after a board vote recorded in the portal. Payment plans: owner self-service in portal within policy; hey creates the ACH plan via API; breaches detected from missed ACH and re-staged.

### New community: bank steps (a person does every one)

1. Signed agreement arrives (work item `signup` in the onboarding lane). Open operating and reserve
   accounts at the partner bank in the association's legal name and EIN; add the board's signers; give
   them Client Connect access. Mark **accounts opened** on the ops onboarding page.
2. The board mails the **start-up check** (one assessment cycle, floor in config) to the lockbox. When
   it clears, mark **start-up check received**. The operating account is funded; bills can be paid.
3. Parallel month: hey rebuilds the books from statements while the old process runs.
4. The board closes the old accounts and mails the **final transfer** as checks. Mark **received**.
5. Create the Caliber client, import the roster and opening balances, enter the client id → live.

## Bank (First Citizens Client Connect)
The only place money moves. Accountant executes approved transfers and CD actions there; boards submit signature cards and download statements there; statements for the package are downloaded there and attached unchanged. hey verifies balances against statements and never touches the portal.

### Accounts payable
Intake → code → match → board approves in portal (API action) → accountant releases the batch in Caliber with the bank module (positive pay) → hey reads payments back, attaches check images, notifies the vendor if asked, updates 1099 totals.

### Resale and lender requests
Order form (site) → fee collected → hey assembles the package from `resale` endpoints, documents and the ledger → accountant checks the figures → delivered in 3 business days → at closing, hey posts the new owner (`addnewowner`) and triggers the escrow alert.

### Annual cycle
| When | What | Auto |
|---|---|---|
| T-120 days to FYE | Reserve study review, insurance renewal quotes, budget draft from actuals + study | D |
| T-60 | Board budget workshop; adoption; owner notice per statute | D |
| T-30 | Budget entered; billing records updated in Caliber UI for new dues | UI |
| January | 1099s from vendor totals + adjustments; tax-prep package to CPA | D |
| Annual meeting | Notice, proxies/ballots (print-and-mail + e-vote), minutes draft from recording | D |
| Ongoing | Corporation report, registered agent, insurance certificates, COI tracking | A reminders |

## 6. Team, ratios and tooling

| Role | Does | Ratio |
|---|---|---|
| HOA accountant (Caliber seat) | Setup, bank rec, adjustments, AP release, close sign-off, 1099s, resale figures | 1 per 60–80 communities |
| Community coordinator | Review queue, escalations, boards, vendors, onboarding interviews, weekly agent audits | 1 per 40–60 communities |
| Founder / ops lead | Sales, onboarding kickoff, escalations, eval reviews, FrontSteps relationship | — |
| hey (six agent lanes) | First pass on everything; all Caliber writes in the surface; drafts; scheduled checks; monitoring | all |

Tooling: our app (hey ops console, agents, portals, snapshots, budgets, community brain, audit log) · Caliber (desktop seats for accountants) · First Citizens via the Caliber bank integration and lockbox (no direct bank API in year one) · Postmark (email transport, inbound webhook) · Twilio (SMS, voice) · print-and-mail API · e-signature · Claude via the Anthropic API · Slack for internal pings · an eval harness built from reviewed work items. No third-party help desk, CRM or ticket tool.

## 7. What stays human, on purpose
Releasing money · waiving or adjusting a charge · any legal-adjacent letter (lien, attorney, violation hearing) · talking to an owner in distress · board politics · vendor selection · anything hey cannot cite. These are listed in each community's escalation list and in hey's system prompt.
