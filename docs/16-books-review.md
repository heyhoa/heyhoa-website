# 16 · The free books review

The offer in sequence A and on `/books-review`: send three recent bank statements and in two business
days we tell you what we would find. It is the sales document that costs us two hours and earns the
treasurer's trust before a contract exists. The checklist is the work; the memo is the deliverable.

## Flow

1. Treasurer uploads statements on `/books-review` (or emails them). A lead is created with source
   `books-review` and a `books_review` work item lands in the sales lane, which escalates to the accountant.
2. Accountant opens the lead in hey ops → **memo** (`/ops/leads/<id>/review`). The checklist sits beside the
   form. Findings go in the table, clean areas get ticked, the summary is three sentences.
3. "Save and mark delivered" stamps the date and moves the lead to `proposal`. Print the memo (`?print=1`)
   to PDF, email it from the founder's address with the proposal link, log the send on the lead's thread.
4. The founder follows up by hand or lets sequence A continue; a reply stops the sequence on its own.

Clock: two business days from receipt. If we miss it, say so in the email and why.

## What we look for (the checklist in `app/services/books_review.py`)

**Cash and reconciliation**
- Last statement balance ties to the books to the penny, or there are no books and we say so.
- Operating and reserve in separate accounts, in the association's name and TIN.
- Dormant accounts (90+ days no activity) and balances that never move.
- Reserve balance against the last study's recommendation.

**Assessments and collections**
- Deposits in the month vs units × assessment: collection rate.
- Months under 85% of billed: who is behind, is anyone acting.
- Late fees and collection fees charged per the governing documents, or not at all.
- Prepaid dues sitting in cash that reads as surplus.

**Vendors and disbursements**
- Same payee, same amount, within 45 days.
- Payees paid more than 12 times in 12 months; monthly amounts that stepped up without a contract change.
- Vendors over $600 with no W-9.
- Payments to individuals, board members, round-number transfers without an invoice.
- Insurance, utilities, taxes present every period they should be.

**Controls and reporting**
- Who can move money alone (single signer, debit card, online banking without dual approval).
- When the board last received a full package.
- A budget exists and spending is compared to it monthly.
- Tax return, insurance renewal, corporate filing, reserve study age.

## How we present findings

- One page. Lead with the finding that costs them the most.
- Every finding has a number or a date. "Duplicate landscaping payment, Aug 12 and Aug 27, $1,850 each."
- Say what we saw, not what we suspect. Never call a vendor or a volunteer dishonest; name the control that
  was missing and what we would do about it.
- Impact: high (money out the door or a legal exposure), medium (money at risk, a control gap), low, note.
- If the books are clean, the memo says so plainly. A clean review still ends with the proposal and the
  booking link; the pitch is time, not fear.
- Footer: not an audit, review or attestation; based on documents provided.

## Memo structure (`ops/books_review_memo.html`)

Header with the hey mark, community, date, who it is for · Title "What we found in X's books" · statements
reviewed and scope line · summary paragraph · findings table (area, what we saw, impact, amount, what we would
do) · "Looked fine" line · what happens next: exact monthly price, proposal link, booking link · footer.
