# 07 · Product spec

Three applications, one Flask codebase, one design system, one provider interface for accounting data.

## 1. Sales & marketing site (`/`)
Dark theme. Goal: quote requests and demo-portal visits.

| Page | Route | Purpose | Status |
|---|---|---|---|
| Home | `/` | Promise, positioning, proof, FAQ, CTA | Mocked |
| Pricing | `/pricing` | Three tiers, worked examples, add-ons, FAQ | Mocked |
| Services | `/services`, `/services/{accounting,back-office,collections}` | Deliverables + where `hey` fits | Mocked |
| How it works | `/how-it-works` | 3-week onboarding, monthly rhythm | Mocked |
| Self-managed | `/self-managed` | Keep vs hand off; signs it is time | Mocked |
| Compare | `/compare` | DIY vs manager vs remote firm vs hey | Mocked |
| Reviews | `/reviews` | Testimonials (placeholders until real) | Mocked |
| About | `/about` | Origin, beliefs | Mocked |
| FAQ | `/faq` | Objections answered | Mocked |
| Blog | `/blog`, `/blog/<slug>` | SEO content (3 posts seeded) | Mocked |
| Homeowners | `/homeowners` | Help hub picklist | Mocked |
| Realtors | `/realtors` | Order closing documents | Mocked |
| Quote | `/quote` → `/quote/thanks` | 3-step form, saves Lead, scores it | Working |
| Contact | `/contact` | Saves ContactMessage | Working |
| Legal | `/privacy`, `/terms` | Drafts for counsel | Mocked |
| Brand | `/brand` | Internal brand sheet (noindex) | Working |
| Login | `/login`, `/login/<role>` | Role pick, demo sign-in (magic link later) | Demo |

## 2. Homeowner portal (`/me`)
Light theme, sidebar. Goal: pay, ask, file, find.

| Page | Route | Key content |
|---|---|---|
| Home | `/me/dashboard` | Balance, next due, open items, recent ledger, board announcements, Ask hey |
| Pay | `/me/pay` | Amount, ACH/card, autopay toggle, payment plan, other ways to pay |
| Ledger & statements | `/me/ledger` | Full ledger table, monthly statement PDFs, CSV export |
| Maintenance requests | `/me/requests`, `/me/requests/new` | List with status/vendor; 2-step form, `hey` classifies, photo upload, urgent flag |
| ARC | `/me/arc`, `/me/arc/new` | List with approvals count; 3-step application with palette/rule hints |
| Documents | `/me/documents` | Governing, ARC, financial, meetings, insurance, plus anything the board filed for owners |
| Community spending | `/me/spending` | Cash, reserves, YTD spend, every paid bill by vendor and category, except bills the board marked confidential |
| Board & contacts | `/me/directory` | Board, hey contact, emergency numbers |
| Profile | `/me/profile` | Contact info, mailing address, notification prefs, directory opt-in |
| Ask hey | `/me/ask` | Chat with sourced answers; unsourced → human |

## 3. Board portal (`/board`)
Light theme, sidebar grouped Money / Community / hey. Goal: decide fast with the evidence attached.

| Page | Route | Key content |
|---|---|---|
| Dashboard | `/board/dashboard` | Cash, reserves, AR, AP pending; needs-a-decision list; cash chart; delinquencies; open maintenance; `hey says` |
| Financials | `/board/financials` | Strict cash basis: YTD income/expense vs budget, cash-basis balance sheet, recon status, board and homeowner package downloads, bank card (Client Connect for statements and signature cards; money moves only there) |
| Approve payments | `/board/invoices` | Queue with `hey` notes (contract match, trend variance); approve / hold / reject; 2-approval rule; hide-from-owners flag for protected bills |
| Decisions | `/board/decisions` | Everything else that needs a vote: bank transfers, CDs/yield vehicles, bids, work orders, ARC when assigned, special assessments, budget, policies, collections steps, fee waivers, vendors, insurance, meetings; quorum per type; votes logged; approved → execution item for the accountant/coordinator |
| Owner inbox | `/board/inbox` | Every call, text, email and portal request from owners with hey's answer and state; board replies under its own name |
| Reserve plan | `/board/reserves` | Components from the reserve study (upload → hey extracts), accrued vs balance, percent funded, suggested contribution, ten-year horizon |
| Delinquencies | `/board/delinquencies` | Stage, days, last/next action; draft notice via `hey` |
| Budget & reserves | `/board/budget` | Dues, reserve funding %, `hey` draft budget, component table |
| Vendors | `/board/vendors` | COI expiry, W-9 status, YTD paid; payment block without W-9 |
| Owners & units | `/board/owners` | Roster with balance, autopay, status; export |
| Maintenance | `/board/requests` | All requests, vendor assignment |
| ARC review | `/board/arc` | Approve / request info / deny with rule citation; approvals count |
| Violations | `/board/violations` | Stage tracking (Board+) |
| Announcements | `/board/announcements` | Compose, channel, `hey` draft from a brief; sent history |
| Meetings | `/board/meetings` | Next meeting, `hey`-drafted agenda, minutes archive |
| Documents | `/board/documents` | The association's system of record: upload governing docs, rules, policies, contracts, warranties, insurance, reserve studies, meeting records; vendor, effective and expiry dates; 90-day expiry warnings; owner/board visibility |
| Ask hey | `/board/ask` | Numbers with GL citations, drafts |
| Activity log | `/board/activity` | Every human and `hey` action with inputs |
| Settings | `/board/settings` | Approval rules, integrations status, board members, plan |

## 4. hey ops (`/ops`)
Light theme, sidebar. The admin console. Humans review what the agents propose; nobody works out of an inbox.

| Page | Route | Key content |
|---|---|---|
| Dashboard | `/ops/dashboard` | Waiting-for-a-person count by lane, SLA breaches, done today, percent closed by agents alone, needs-a-person list, lane summary |
| Review queue | `/ops/review` | Proposed and escalated items with the proposal preview, editable body, approve/reject |
| All work | `/ops/queue` | Filter by lane, state, community |
| Item | `/ops/item/<id>` | Thread (all channels), evidence, proposal with payload, approve/reject, internal notes, agent runs, re-run in another lane |
| Log a call / item | `/ops/new` | Manual intake for calls and walk-ins; runs the lane's agent |
| Lanes & policy | `/ops/agents` | Each agent's description, tools by risk, what it may execute alone, stats, system prompt |
| Messages | `/ops/threads` | Every inbound and outbound message with delivery status |
| Runs & audit | `/ops/activity` | Agent runs with tokens and timing; audit log |
| Settings | `/ops/settings` | Shadow mode, live communities, confidence floor, transports, aliases |

## Data model (local, `app/models.py`)
`WorkItem` (the unit of work for hey ops) · `Message` (thread entries, any channel) · `AgentRun` (every agent step with tokens and timing) · `Lead` (quote requests, scored) · `ContactMessage` · `PortalRequest` (maintenance/ARC submissions mirrored to the provider) · `Announcement` · `AuditLog` · `CoaSnapshot` (nightly chart of accounts, the basis for monthly statements) · `BudgetLine` (we are the system of record for budgets).
Live accounting data (communities, units, ledgers, invoices, delinquencies, ARC, documents, vendors, violations) comes from the **provider interface** (`app/integrations/base.py`). Period financials are *derived* in `app/services/financials.py` from snapshots, because Caliber exposes balances but not activity by period (doc 12). Bank reconciliation is done in Caliber; we verify and present it.

## Agents (`app/agents/`)
Six lanes (CS, AR, AP, Board, Close, Onboarding) built on one framework: tools with risk levels, demo planners and a live Claude tool-use loop, a review policy with shadow mode. See doc 13 §3. The assistant functions below are what the lanes call for drafting and classification.

## AI jobs (`app/ai/assistant.py`)
| Job | Input | Output | Human in loop |
|---|---|---|---|
| Answer owner question | question + governing docs + owner ledger | sourced answer or "routing to a person" | only when unsourced |
| Answer board question | question + GL + invoices + docs | numbers with GL citations, drafts | drafts need a send |
| Classify maintenance request | free text | category, responsibility, urgency | board assigns vendor |
| Code an invoice | invoice PDF + contract + COA + history | GL account, match/variance note | board approves payment |
| Draft delinquency notice | ledger + policy + stage | letter marked DRAFT | person sends |
| Draft announcement / agenda / minutes | brief or month's activity | text | board edits, sends |
| Draft budget | actuals + reserve study + known increases | line-item draft | board votes |
Live mode uses Claude via the Anthropic SDK (model from `HEY_AI_MODEL`, default Opus 5.5, server-side refusal fallbacks on). Demo mode is rule-based so every page works offline.

## Self-serve signup and onboarding

A board member can sign up at `/start`, sign the agreement and start onboarding without a call.
Signup takes the community basics (name, type, standalone/master/sub, units or lots, city, billing
frequency, who keeps the books today), the plan, and the person. The agreement page shows the deal in
a table (service, fee, term, money, access, data, law) with the full PSA under it; typing a name and
ticking the box records a signature with version, hash, time and IP. The onboarding page then lists,
in order: community details structured like the Caliber client (legal name, incorporation state, EIN
last 4, address, county, fiscal year end, assessment amount, board roster with signers), the owner
roster by CSV, documents, board rules (approvals per decision type) and the bank steps.

Bank: we open operating and reserve accounts at the partner bank in the association's name and EIN.
The board mails a **start-up check** (one assessment cycle, floor in config) to the lockbox so bills
can be paid from day one; after the parallel month the board closes the old accounts and mails the
**final funds transfer** as checks. A person in ops confirms each check. Go-live is a person creating
the Caliber client and entering its id; approval rules are rekeyed to it.

## Board rules

`ApprovalRule` per community and decision type: invoices 2, bank transfers 3, CDs 3, new vendors 2,
bids 2, ARC 2, special assessments 3, budget 3, liens and attorney 2, fee waivers 2 by default. Set at
onboarding, changed in board Settings, applied to the next decision. Never below 1.

## Meetings

Board, annual, budget, special and executive templates. "Schedule" builds the agenda from what is
actually pending (decisions, invoices, projects due, the latest package, open requests), the board
edits it, sends the notice by email, portal, text and letter (to owners without email, or everyone),
and records minutes. Print view for the packet. Notice days per type with a "late" flag.

## Letters and email blasts

Email and text blasts live on Announcements; a "letter" option also mails owners without email (or
all owners). The Letters page has templates (general, meeting notice, budget letter, collection
notice, courtesy/violation, welcome), audiences (all, no email on file, one unit), a preview with
per-recipient fields, certified mail, and a log with cost. Lob when configured; otherwise the letter
is recorded and a person prints and mails it. Cost is a pass-through.

## Insurance

Policies with carrier, number, coverage, deductible, premium, dates, agent and the declarations page;
gaps against the recommended set (property, liability, D&O, fidelity, cyber) and renewals within 60
days. A standing cyber callout: account access and actions are the association's; buy a policy here.

## Projects, reserve plan, who fixes what

Three board pages, each a copy of a sheet treasurers already keep, each editable under the table:

- **Projects** (`/board/projects`): priority (1 now, 2 next, 3 someday), project, estimated cost
  (a range is fine), year, status (planned, in progress, under review, scoping, completed), a
  sentence on what it is, paid from (reserves, operating, special assessment).
- **Reserve plan** (`/board/reserves`): the reserve-funded projects with cost and a sentence; the
  same projects on a five-year grid; under it starting amount, reserve contributions, special
  assessment, funds available, total expenditures, year end balance. Year one starts at today's
  reserve cash; a red year end is the whole point of the page. Reserve study components extracted
  by hey sit below until the board pulls them into the plan.
- **Who fixes what** (`/board/who-fixes-what`): item, homeowner X or association X, a note with the
  resolution or CC&R section.

Owners see projects and who-fixes-what on one page (`/me/community`). Both are on the public
community JSON, in the MCP (`who_fixes_what`, `community_projects`) and in the CS lane's tools, so
"who fixes my patio gate" is answered from the board's own chart with its source.

## The monthly financial package (from the founders)
Board package, in order: 1 branded cover sheet · 2 monthly update and change summary · 3 budget comparison / P&L · 4 balance sheet · 5 aged owner balance report · 6 collection report · 7 prepaid report · 8 check register / AP distributions · 9 bank reconciliation(s) · 10 bank statement(s), attached as received from First Citizens. Homeowner package: sections 1–4. Strict cash basis. Defined in `app/services/packet.py`; sample at `/sample-packet?audience=board|homeowner`.

## Money movement
Transfers, CD purchases and redemptions are never done by software. Board decision → accountant executes in First Citizens Client Connect with the board's signers → confirmation on the decision → recorded in Caliber. Boards use Client Connect for signature cards and statements.

## Visibility rules (from the founders)
| Who | Sees | Never sees |
|---|---|---|
| Owner | own ledger, statements, own requests, documents marked for owners, paid bills (minus confidential), published financial summary, meeting notices | compliance/violations list, delinquency list, any other owner's balance or ledger, unpaid-bill queue, board-only documents, ops screens, agent proposals |
| Board member | everything about the community: financials, approvals, decisions, delinquencies, violations, owner inbox with hey's answers, all documents, reserve plan, audit log for the community | ops screens, other communities, agent internals (runs, prompts), the hey team's review queue |
| Vendor (via MCP/email) | own invoices and payment status | anything else |
| Realtor/lender (via MCP) | public profile, fee schedule, their own orders | anything else |
| hey team (ops) | all of it, across communities | — |

Confidential invoices: the board hides a specific bill (legal, HR, protected information) with a reason; it stays in the board view and the packet, and leaves the owner spending page.

## Decision types and quorums (defaults)
Bank transfer 2 · CD / yield vehicle 2 · vendor bid 2 · open work order 1 · ARC (if assigned to the board) 2 · special assessment 3 · budget 3 · policy 3 · collections step (attorney, lien) 2 · fee waiver 2 · new vendor / contract 2 · insurance 2 · meeting notice / election 1 · announcement 1 · invoice 2 (Caliber flow). Quorums are defaults from the bylaws; editable per community (Phase 2). Approved money decisions become an execution item for the accountant (bank + Caliber); others go to the coordinator.

## Non-goals (for now)
No on-site services, no violations inspection, no funds custody, no mobile app (responsive web is enough), no multi-community board users until Phase 4.
