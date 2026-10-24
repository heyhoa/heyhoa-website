# 06 · Sales outreach campaigns

Founder-led, high-touch, low-volume. 300 touches a month is plenty. Every reply gets a human answer within an hour during business hours.

## Lists: where treasurers come from
1. **County records.** HOA declarations are recorded; management certificates (Texas Property Code §209.004) list the association's contact and whether it is self-managed. Pull by county; filter where the contact is a person, not a management company.
2. **State nonprofit registries.** Associations are nonprofits; officer names are on the annual report. Cross with (1).
3. **LinkedIn.** Search "HOA treasurer", "board treasurer homeowners association", "HOA president" by metro. Low volume, high quality.
4. **Board forums.** Reddit r/HOA, Facebook HOA board groups, Nextdoor. Do not scrape; participate.
5. **Partner referrals.** Title companies and HOA attorneys know which boards are struggling.
6. **Inbound from content.** Blog readers who download the checklist or the sample packet.

Track in a simple CRM (Notion/Airtable/HubSpot free). Fields: community, doors, state, contact, role, trigger, source, stage, next step, notes. Leads from the site land in the `leads` table with a 0–100 fit score (`app/services/leads.py`); mirror them to the CRM nightly.

## Sequence A: cold email to a treasurer (5 touches, 14 days)
**Day 1 — subject: your financial packet date**
> Hi {{first}}, I run hey hoa, an accounting and back office for self-managed communities like {{community}}. One question: what day of the month does your board get financials? Most treasurers tell us the 20th or later. We deliver by the 5th, in the contract, or that month is free. Pricing is public (heyhoa.com/pricing): {{quote_estimate}} for {{doors}} doors. If it is useful, I can look at your last three bank statements and tell you what we would find, no charge. — {{founder}}

**Day 4 — subject: re: your financial packet date**
> One more thing that might matter: owners can text a question and get an answer with the bylaw section in about a minute. The board group chat gets quiet. Here is the board portal with demo data, no signup: heyhoa.com/login/board?demo=1

**Day 7 — subject: a thing we found**
> We did a free books review for a 48-door community last month and found $4,100 in duplicate landscaping payments. Not saying you have that. Saying it takes us two days to check. Want me to?

**Day 11 — subject: resale certificates**
> Different angle: if a closing has ever been delayed waiting on a resale certificate, that is also us. Three business days, paid by the seller, never a board task again.

**Day 14 — subject: closing the loop**
> I will stop here. If timing is wrong, reply "later" and I will check in before your next budget season. If you want the free review, send three statements to {{email}}. Thanks for reading.

## Sequence B: management-company switchers (3 touches)
Trigger: public complaints, contract renewal season (Sept–Nov), or a referral.
1. "Most of full service at a third of the price" with the comparison page.
2. The guarantee and the no-contract term; what leaving looks like (30 days, full export).
3. Offer to run in parallel for a month before they give notice.

## Sequence C: partners (title, attorney, CPA, reserve firm)
1. What we do, what we pay or reciprocate, the resale turnaround promise.
2. A one-page PDF they can hand to boards.
3. Quarterly check-in with a count of closings or files we handled from their referrals.

## Call script (15 minutes)
1. **Open (1 min):** "Thanks for the time. I want to understand how the books run today and tell you honestly whether we are a fit. If we are not, I will say so."
2. **Discover (6 min):** Who does the books? When does the packet land? What does it cost (money and hours)? What broke last? Bank and software? Contract end date? Annual meeting date?
3. **Show (5 min):** Board portal: approve-payments queue with `hey` notes, financials page, delinquencies with a drafted letter. Homeowner portal: ask `hey` a bylaw question.
4. **Price (1 min):** "For {{doors}} doors on Back Office that is {{price}} a month, month to month, onboarding free, 5th or free."
5. **Close (2 min):** "Two paths: send me three statements for the free review, or I send the proposal tonight and you take it to the board. Which?"

## Objections
| They say | We say |
|---|---|
| We are too small for this | Books tier is $199 for up to 30 doors. Less than the hours your treasurer spends. |
| We just need someone on site | Then you need a manager, and we are not that. Keep your volunteer walk-throughs; we do everything that does not need a car. |
| The board will not trust AI with money | Nothing moves without two board approvals. AI reads and drafts; people decide. Every action is logged where the board can see it. |
| Our bookkeeper is a friend | Keep them for review if you like. We will send them the packet. Most boards find the friend is relieved. |
| What if you miss the 5th | That month is free. It is in the contract. |
| What happens to our data if you fail | Exports in standard formats any time; FrontSteps or our ledger, your name on the account. |
| We are mid-year | We rebuild in parallel and go live at month end. Most boards switch in three weeks. |
| Is this legal in our state | We provide bookkeeping and admin, not management; no license required. Counsel reviewed for TX, CO, AZ, NC, GA. FL/NV pending. |

## Cadence and hygiene
- Send Tue–Thu, 8–10am local. Plain text, no images, one link.
- Personalize line one from county records or the site (door count, last meeting, a visible issue).
- Reply within one hour, 8am–6pm. Replies after hours get a two-line human reply the next morning, never an autoresponder.
- Unsubscribe on request immediately; never re-add.
- Weekly review: reply rate, meeting rate, which subject lines and pains got traction. Rewrite the weakest touch each week.

## Targets, month one
300 touches → 25 replies (8%) → 10 calls → 4 free reviews → 2 proposals → 1 signed.
