# 11 · Services agreement (starting point)

Source: `legal/2026-professional-services-agreement-template.docx` — the Professional Services Agreement (PSA) the founders already use, with Exhibit A (fee schedule, January 2026) and Exhibit B (assessment collection policy). It is the starting point; the product and the tiers bend to it, and where we want to differ we say so below and get counsel to redline.

## What the agreement establishes
- **Who we are.** Service Provider is Heywood Realty & Investment, Inc., an Arizona company. hey hoa is the brand; the contracting entity stays Heywood unless a new entity is formed. Governing law and mediation/arbitration are Arizona (A.R.S. § 12-1501, Maricopa County). **This moves the beachhead to Arizona** (Phoenix metro: Mesa, Gilbert, Chandler, Scottsdale, Tempe), with Texas as the second wave.
- **What we are.** "Exclusive servicing agent" in an administrative and advisory capacity. Expressly *not* property management: no supervision of physical property, no vendor licensing checks, no legal advice, no insurance adjusting. The board keeps every decision. This is exactly the positioning on the site.
- **Money.** Operating and reserve accounts are opened in the association's name and tax ID at an FDIC-insured partner bank of our choosing; we disburse from them for approved bills, insurance, taxes and our own fees (§2.3, §2.6, §2.7). Non-partner banks cost $50 per account per month (Exhibit A). *Site copy that said "we never hold funds" and "we work with the bank you have" was wrong and has been corrected to: accounts stay in the association's name and tax ID at our partner bank; the board approves, we process.*
- **Approvals and fraud.** We may rely on instructions from any apparent Authorized Representative, including email, with no duty to verify; the association carries the fraud, chargeback and processor risk (§2.6). *Product decision: the portal's two-approval rule and audit log go beyond the contract on purpose. They are a feature, not a duty of care, and the terms page says so.*
- **Reporting.** Monthly cash-basis statements (§2.8). Our "by the 5th or the month is free" promise is an addition to the template and needs a clause (see decisions).
- **Scope of routine services** (§2): notice to owners, owner communications, AP processing, assessment billing and collection under our Standard Collection Policy, bank accounts, monthly statements, tax-prep assistance, owner records and ownership monitoring, account questions, meetings by phone/web at hourly rates, resale/disclosure/refinance work paid by the requester, letters and notices, insurance purchase assistance, violation notices at the board's direction, annual budget draft 30 days before fiscal year.
- **Non-routine services** (§3): litigation support, special assessments, loans, audits, records requests, insurance claim admin, custom reports: hourly or quoted, billed monthly, due in 10 days, 1.5%/month late.
- **Association obligations** (§4): documents within 20 days, a board liaison (president by default), vendor licensing and insurance, GL/umbrella/D&O coverage naming us as additional insured, confidentiality, one-year non-solicit of our staff ($2,500/month liquidated damages).
- **Term** (§5): 12-month initial term, auto-renews 12 months, 30 days' notice before expiration, minimum 3% annual increase deemed approved with the budget, 60-day cure, off-boarding accounting within 30 days.
- **Liability** (§6.4): association indemnifies us; our aggregate liability is capped at six months of fees.
- **AI** (§6.12, §6.14): we may use AI and automation; third-party AI may process association data; AI-enhanced services may be billed as additional services; internal work product (drafts, transcripts, analytics) is ours, only delivered records are association records. *This is the clause that lets hey exist. Keep it.*

## Mapping Exhibit A onto our tiers
Principle: what Exhibit A bills **to the association** per item, we fold into the flat tier price. What Exhibit A bills **to an owner or a third party** stays itemized, because the party who benefits pays and it keeps dues lower for everyone else.

| Exhibit A item | Exhibit A price | hey hoa |
|---|---|---|
| Regular assessment statement / e-statement | $2.27 / $1.95 | Included in every tier (paper mailing $1.25 pass-through) |
| Copies, envelopes, checks, return mail | $0.22–$3.50 | Included; postage pass-through |
| 1099 / 1096 forms, tax file prep | $45 / $60 / $125 | Included in Books and up |
| Online invoice approval, e-file storage, owner portal | Included | Included |
| Meeting minutes, board meeting attendance | Included / hourly | Minutes drafts included (Back Office+); virtual attendance $125/hour, in-person not offered |
| Compliance violation letter | $5 | Included in Board+; $5 each otherwise |
| ARC form administration | $45 | Included in Back Office+ |
| Vendor insurance tracking | Included | Included |
| Community website | $70/mo | Portal replaces it; included |
| Online voting setup | $300 | $300 (pass-through to e-voting vendor) |
| Non-partner bank account | $50/acct/mo | $50/acct/mo |
| Special assessment / loan setup | $500 + $2.50/unit | $500 setup + $2/door per cycle |
| Payroll administration | $195/mo | Not offered in year one |
| Registered agent, corporation report filing | $135/yr, $75 | $135/yr, $75 |
| Client setup | Included (header shows $750) | Included (free onboarding is the offer) |
| Off-boarding administration | $750 | **Decision needed.** Recommend $0 for a clean month-to-month story, or $750 only inside an initial term |
| Collections notices (to owner) | $25–$275 per step | Same schedule, charged to the owner ledger per Exhibit B |
| Payment plan setup / breach / cancel | $75 / $45 / $45 | Same; portal self-service still charges $75 |
| NSF / chargeback | $49 | $49 |
| Resale/disclosure package | Statutory or market | $275 (AZ statutory cap applies: A.R.S. § 33-1260 / § 33-1806); rush $100 |
| Lender questionnaire standard / custom | $250 / $350 | $250 / $350 |
| Lender refinance statement | $150 | $150 |

These now live in `app/brand.py` (`ASSOCIATION_FEES`, `OWNER_FEES`) and render on `/pricing`.

## Exhibit B → the collections engine
Stages, in days past due: **late notice** (past due) → **15** rebill notice → **30** pre-legal demand → **60** intent to lien → **75** lien recorded → **90** intent to further legal action → **90+** suspension of rights / attorney. Lien or attorney only once the balance is ≥ $400 or the account is ≥ 75 days late. Payment application order per A.R.S.: assessments, then current assessments, late fees, collection costs, attorney fees, other. Payment plans and waivers per board policy; hard costs never waived.

The demo data, the delinquency page and hey's context now use these stages and fees. Phase 3's delinquency engine implements the schedule as data with a human send on every notice.

## Decisions to make before counsel (owner: founders)
1. **Term.** Template: 12-month auto-renew, 3% floor. Site: "month to month". Options: (a) keep 12-month and change the site to "one-year agreement, 30 days' notice, no multi-year lock-in"; (b) month-to-month after a 3-month minimum, keep the off-boarding fee at $750 to discourage churn; (c) month-to-month, no fees, differentiate hard. Recommendation: (b).
2. **The 5th-or-free promise.** Add a service-level clause: packet by the 5th business day when bank access and documents were timely; miss = that month's Services Fee waived. Caps the promise at the base fee; excludes months with incomplete onboarding.
3. **Contracting entity and brand.** "hey hoa, a service of Heywood Realty & Investment, Inc." in the agreement header, footer and invoices, or form a new entity. Footer now carries the Heywood line.
4. **Fraud and approvals.** Keep §2.6 as written (we rely on apparent authority) and add that the portal's two-approval setting is a courtesy control, not a duty.
5. **AI clause.** Keep §6.12 and add that AI output is reviewed by a person before any notice, letter or payment leaves.
6. **Fee schedule.** Adopt the mapping table above as the new Exhibit A for hey hoa tiers.
7. **Other states.** Texas (second wave) needs a TX governing-law version and the resale certificate statute swap (Tex. Prop. Code § 207).

## Where it touched the product
- `app/brand.py`: legal entity, fee schedules, collection stages.
- `/pricing`: fee schedule tables; "included vs owner-charged" framing.
- `/`, `/how-it-works`, `/about`, `/faq`, `/terms`: funds, banking and term language corrected.
- Demo community moved to Mesa, AZ; Arizona statute references in the ARC and hey answers.
- `docs/01`, `03`, `06`: Arizona beachhead, Maricopa County lists.
