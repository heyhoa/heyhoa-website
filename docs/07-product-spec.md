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
| Documents | `/me/documents` | Governing, ARC, financial, meetings, insurance |
| Board & contacts | `/me/directory` | Board, hey contact, emergency numbers |
| Profile | `/me/profile` | Contact info, mailing address, notification prefs, directory opt-in |
| Ask hey | `/me/ask` | Chat with sourced answers; unsourced → human |

## 3. Board portal (`/board`)
Light theme, sidebar grouped Money / Community / hey. Goal: decide fast with the evidence attached.

| Page | Route | Key content |
|---|---|---|
| Dashboard | `/board/dashboard` | Cash, reserves, AR, AP pending; needs-a-decision list; cash chart; delinquencies; open maintenance; `hey says` |
| Financials | `/board/financials` | YTD income/expense vs budget, balance sheet summary, recon status, packet downloads |
| Approve payments | `/board/invoices` | Queue with `hey` notes (contract match, trend variance); approve / hold / reject; 2-approval rule |
| Delinquencies | `/board/delinquencies` | Stage, days, last/next action; draft notice via `hey` |
| Budget & reserves | `/board/budget` | Dues, reserve funding %, `hey` draft budget, component table |
| Vendors | `/board/vendors` | COI expiry, W-9 status, YTD paid; payment block without W-9 |
| Owners & units | `/board/owners` | Roster with balance, autopay, status; export |
| Maintenance | `/board/requests` | All requests, vendor assignment |
| ARC review | `/board/arc` | Approve / request info / deny with rule citation; approvals count |
| Violations | `/board/violations` | Stage tracking (Board+) |
| Announcements | `/board/announcements` | Compose, channel, `hey` draft from a brief; sent history |
| Meetings | `/board/meetings` | Next meeting, `hey`-drafted agenda, minutes archive |
| Documents | `/board/documents` | Board-only + owner-visible with visibility flags |
| Ask hey | `/board/ask` | Numbers with GL citations, drafts |
| Activity log | `/board/activity` | Every human and `hey` action with inputs |
| Settings | `/board/settings` | Approval rules, integrations status, board members, plan |

## Data model (local, `app/models.py`)
`Lead` (quote requests, scored) · `ContactMessage` · `PortalRequest` (maintenance/ARC submissions mirrored to the provider) · `Announcement` · `AuditLog`.
Accounting data (communities, units, ledgers, invoices, delinquencies, ARC, documents, vendors, violations, financial snapshot) comes from the **provider interface** (`app/integrations/base.py`) and is never stored locally in Phase 1–2.

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

## Non-goals (for now)
No on-site services, no violations inspection, no funds custody, no mobile app (responsive web is enough), no multi-community board users until Phase 4.
