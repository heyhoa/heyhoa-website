# 01 · Business model

## One line
AI-first accounting and back office for self-managed HOAs and condos, sold at a public flat price, delivered on a date we are penalized for missing.

## Who we serve (ICP)
- **Self-governed communities, 15–200 doors.** Townhomes, small condos, single-family HOAs. Big enough that the books matter, small enough that a management company is overkill.
- **Buyer:** the treasurer (first) and the president (second). Volunteer, usually the most competent person on the board, usually tired.
- **Trigger events:** treasurer resigns or moves; financials chronically late; a duplicate payment or missed reconciliation surfaces; a closing is delayed for lack of a resale certificate; management contract renewal with a price hike; annual meeting with no budget.
- **Geography:** US-wide (remote by design). Beachhead is **Arizona** (Phoenix metro), where the operating entity, the services agreement and the first client already are. Second wave: TX, CO, NC, GA, UT, NV, WA; FL after CAM-licensing review.
- **Not a fit (yet):** sub-10-door communities that want only tax filing; 300+ door communities with on-site staff; communities that want someone to walk the property.

## What we sell
Three tiers, public, flat by door band, then per door. Written agreement, 30 days' notice, no multi-year lock-in (term decision pending, doc 11).

| Tier | Base (≤30 doors) | Per door after | What it is |
|---|---|---|---|
| Books | $199/mo | $6 | Accounting only |
| Back Office | $349/mo | $9 | Books + owner support, collections, ARC intake, resale docs, meeting admin |
| Board+ | $549/mo | $12 | Back Office + named coordinator, budget/reserve, vendor sourcing, violations, insurance coordination |

Add-ons priced to the party that benefits, following Exhibit A of the services agreement (doc 11): collections notices and payment-plan fees charged to the owner ledger, resale packages ($275) and lender questionnaires ($250–$350) paid by the requester, special assessment setup ($500 + $2/door per cycle), non-partner bank accounts ($50/account/month). Statements, 1099s, minutes, ARC admin and the portals are inside the flat fee. Onboarding is free; it is the biggest objection and the cheapest thing to give away.

**The promise:** financial packet by the 5th business day or that month's base fee is waived. It is in the contract. It is also the entire marketing message.

## Why AI changes the economics
A remote accounting firm's cost is almost entirely labor: bookkeepers coding invoices, reconciling, answering email. Rough industry rule: one bookkeeper per 25–35 small associations.

With `hey` doing first-pass invoice coding, bank matching, owner Q&A from source documents, and letter drafting, one accountant plus one coordinator can run 80–120 communities. The human job becomes review, exceptions and judgment.

| | Traditional remote firm | hey hoa |
|---|---|---|
| Communities per accountant | ~30 | ~100 |
| Owner question handling | human reads, human replies, 1–2 days | AI answers with source in a minute; human sees only unsourced items |
| Invoice coding | human, month-end | AI on arrival, human reviews exceptions |
| Gross margin at scale | 40–55% | 70–80% |

That margin gap funds public pricing roughly 30% under the remote-firm range and the "late = free" guarantee.

## Unit economics (planning assumptions, to be replaced with actuals)
- Average community: 55 doors on Back Office → $349 + 25 × $9 = **$574/mo**, ~$6.9k ARR.
- Add-on and pass-through revenue: ~$60/mo per community (resale docs scale with turnover ≈ 6%/yr).
- Payment processing: card fees passed through at cost; ACH free. Potential future margin via processor rev-share, not modeled.
- Direct cost per community at 100-community scale: ~$120/mo (share of accountant + coordinator + software + AI inference ~$8/mo). Gross margin ≈ 79%.
- Payback: CAC target < $1,500 (founder-led sales, content). Payback < 4 months on gross margin.
- Churn target: < 1%/mo. Boards change every election; onboarding the new treasurer well is the retention lever.

## Milestones
| Communities | MRR | What it means |
|---|---|---|
| 1 | ~$500 | Proof: packet on the 5th, owner answers in a minute |
| 10 | ~$6k | Repeatable onboarding, first case studies |
| 50 | ~$30k | First hire (accountant), SEO flywheel on |
| 150 | ~$90k | Second backend integration, state expansion, Board+ tier maturing |
| 400 | ~$240k | Default-alive, consider own ledger to drop platform license |

## Revenue beyond the core (later)
- Insurance referral (CSM does this; high-margin, regulated, phase 4+).
- Reserve study partnerships (referral fee).
- Collections attorney network (referral, flat fee per file).
- Vendor marketplace for small HOAs (bids through `hey`).
- White-label back office for small management companies who want to be "AI-first" without building it.

## Risks and how we hold them
- **Trust on money.** Operating and reserve accounts are in the association's name and tax ID at an FDIC-insured partner bank; we process approved payments from them (PSA §2.6–2.7). Two board approvals on every payment in the portal. Everything logged.
- **AI errors.** AI drafts; a person sends. Every automated action is sourced and logged in the board activity log.
- **Platform dependence (FrontSteps).** Provider interface in code from day one; mock provider proves the UI does not care who the backend is.
- **State regulation.** Arizona does not license community managers. Some states do (FL CAM, NV, etc.). The PSA already disclaims property management, legal and adjusting services; copy says the same. Counsel review before FL/NV launch.
- **Seasonality.** Boards switch at fiscal year end (Jan 1 mostly). Sales pushes Sept–Nov and Mar–May.
