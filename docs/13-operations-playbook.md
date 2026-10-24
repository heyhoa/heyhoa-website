# 13 · Operations playbook: an AI-first team

Goal: one accountant and one coordinator run 80–120 communities, because hey does the first pass on everything and people do judgment, signatures and the Caliber UI tasks the API cannot. This doc says who does what, through which channel, with what tooling, and how far each task is automated. It assumes doc 12 (what Caliber's API can do).

## 1. Operating principles
1. **Everything is a ticket.** Every inbound (email, text, call, portal form, lockbox exception, bank exception, Caliber alert) becomes a ticket with a community, a unit (if any), a category, an owner (hey / person / board) and an SLA. Nothing lives in a personal inbox.
2. **hey first, person second, board last.** hey resolves what it can source. A person handles what hey cannot. The board only sees decisions: approvals, votes, policy. Boards do not get tickets; they get a "needs a decision" list.
3. **Write to Caliber through the small write surface; log everything.** Any Caliber write hey makes is logged with the payload and shown in the board activity log. Anything outside the write surface becomes a ticket for the accountant's Caliber seat.
4. **Drafts are drafts.** Letters, notices, announcements, minutes, budgets: hey writes, a person sends. Payments: two board approvals, accountant releases.
5. **Measure the two numbers that matter:** percent of tickets closed by hey without a person (target 70%+), and zero incorrect sourced answers (weekly audit of a sample).

## 2. Channels

### Email (`help@heyhoa.com` plus one alias per community)
- **Help Scout** is the shared inbox and the ticket system. Two mailboxes: Support (owners, boards, vendors) and Sales (quote requests, website messages, closing-doc orders). Each community gets an alias (`willowcreek@heyhoa.com`) that forwards into Support; the alias identifies the community. Owners can also email the board alias we host, which routes to the same queue with the board on copy.
- hey reads every inbound: identifies the community and the owner (from the roster), classifies, drafts, and either sends (sourced, low-risk categories) or queues for a person.
- Categories hey sends on its own after a confidence check: balance and payment questions, document requests, "what does the rule say", autopay setup, contact changes it already made, status of a request. Everything with money adjustments, disputes, legal threats, emotion or a board decision goes to a person with a draft attached.
- Reply time targets: hey under 2 minutes; person under 4 business hours; board decision items surfaced same day.

### Text (SMS)
- One number per community via Twilio. Owners opt in during onboarding (the mail matrix in Caliber records preference).
- Outbound: payment confirmations, late notices (as a courtesy ahead of the mailed notice), gate codes, announcements the board marks "text".
- Inbound: same pipeline as email. Short answers, link to the portal for anything longer.

### Phone
- One national number and per-community numbers (Twilio Voice). During business hours a voice agent answers first; a person is reachable by saying "person" or pressing 0; after hours the agent handles what it can and takes a message that becomes a ticket.
- **Voice stack now:** Twilio Media Streams → speech-to-text → Claude with the same tools hey uses in chat → text-to-speech. Latency is acceptable for account questions and intake. Design the layer so the speech model is a module.
- **Dessa:** Block's full-duplex speech model is the target experience (natural turn-taking, interruptions, backchannels). As of its release it is a research model on a waitlist that runs locally on an M4 Max class machine, not a telephony product. We request access, run it on a Mac in the office against a test number, and swap it in for the first pass when it is stable and hostable. Until then the stack above.
- What the voice agent may do: look up balance and due date, explain a charge with the ledger line, take a payment by handing off to the provider's IVR or texting a link, set up autopay or a payment plan within policy, file a maintenance request, answer rule questions with the section, take a message for the board. What it may never do: waive a fee, discuss another owner's account, give legal advice, promise an outcome.
- Every call is transcribed, summarized and attached to the ticket; the owner gets a text recap.

### Portal
- Owner and board portals are the preferred channel; email and phone nudge toward them ("I've put the form in your portal; tap here").
- "Ask hey" in both portals uses the same brain as email and phone, with the user already identified.

### Mail
- Outbound letters (collection notices that policy or statute require by mail, annual meeting notices, ballots) go through a print-and-mail API (Lob or PostGrid) with proof of delivery stored on the ticket. Inbound mail goes to a scanning service; checks go to the lockbox, never to us.

## 3. The ticket system
- One queue: Help Scout conversations. Our app mirrors each into `PortalRequest` (`remote_id` = `hs:<conversation id>`) so the portals show status without exposing the tool. Routing and hey's actions use tags (`cat:*`, `route:*`, `hey:replied|drafted`) and assignment, so the coordinator can filter by route in Help Scout's own views.
- Mechanics (built, `app/services/triage.py`): Help Scout webhook (`convo.created`, `convo.customer.reply.created`) → `/api/webhooks/helpscout` (HMAC verified) → community from the alias, owner from the roster → hey classifies and drafts → auto-reply for sourced balance/payment/autopay/document/rule/status questions from a known owner, otherwise an internal note with the draft, tags and assignment to the coordinator, accountant or board contact. Quote requests and website messages are created as Sales conversations (`app/services/notify.py`), with a Slack ping for leads.
- Ticket fields: community · unit/owner · channel · category (balance, payment, autopay, document, rule question, maintenance, ARC, violation, resale, vendor, invoice, adjustment, dispute, board, onboarding, other) · owner: hey / coordinator / accountant / board · SLA · AI confidence · outcome.
- Routing rules:
  - hey auto-resolves: sourced answers, status lookups, self-service tasks it can do via API (contact change, autopay, plan within policy, maintenance intake, ARC intake).
  - Coordinator: anything emotional, ambiguous, multi-party, vendor coordination, meeting and election admin, onboarding.
  - Accountant: adjustments, waivers, disputes on amounts, bank exceptions, AP release, close, 1099s, resale figures.
  - Board: approvals (AP, ARC), policy questions, escalations (attorney referral), vendor selection, budget. These appear in the board portal's decision list, not as tickets.
- Weekly review: every ticket hey resolved on its own gets sampled (10%) by the coordinator; errors become eval cases.

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
| 2–3 | Adjustments, accruals if any, late-fee review in Caliber | UI |
| 3–4 | hey re-renders packet, writes the board summary, flags variances > 10% or > $500 | A |
| 4–5 | Accountant review and sign-off in our portal; packet delivered; board notified; "5th" SLA timer closes | D |
| 5+ | Board meeting agenda drafted from the month | A |

### Collections (Exhibit B as data)
hey computes stage daily; drafts the notice from the ledger and policy; coordinator sends (email + mail where required) and the fee posts to the owner ledger; `addnote` records it; at the $400/75-day threshold hey prepares the lien packet for the accountant; attorney referral only after a board vote recorded in the portal. Payment plans: owner self-service in portal within policy; hey creates the ACH plan via API; breaches detected from missed ACH and re-staged.

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
| Community coordinator | Tickets hey cannot close, boards, vendors, onboarding interviews, weekly reviews | 1 per 40–60 communities |
| Founder / ops lead | Sales, onboarding kickoff, escalations, eval reviews, FrontSteps relationship | — |
| hey | First pass on everything; all API writes in the surface; drafts; monitoring | all |

Tooling: Caliber (desktop seats for accountants) · First Citizens via the Caliber bank integration and lockbox (no direct bank API in year one) · Help Scout (shared inbox and tickets, Support and Sales mailboxes, per-community aliases) · Twilio (SMS, voice) · print-and-mail API · e-signature · our Flask app (portals, hey, snapshots, budgets, community brain, audit log) · Claude via the Anthropic API · Slack for internal pings · an eval harness with real tickets.

## 7. What stays human, on purpose
Releasing money · waiving or adjusting a charge · any legal-adjacent letter (lien, attorney, violation hearing) · talking to an owner in distress · board politics · vendor selection · anything hey cannot cite. These are listed in each community's escalation list and in hey's system prompt.
