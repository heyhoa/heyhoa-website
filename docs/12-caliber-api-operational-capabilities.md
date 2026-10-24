# 12 · What Caliber's API can and cannot do for us

Source: the sandbox Swagger spec in `docs/api/` (Caliber API v2, 310 paths) and endpoint descriptions. Everything here is from the spec; nothing has been exercised against a live tenant yet. The first job with a key is the verification list at the end.

## The short version
- **Caliber is the system of record. We never try to replace its ledger.** The API reads almost everything and writes the handful of things that matter operationally: vendor invoices, invoice approvals, payments, fines, ACH/autopay and payment plans, owner contact data, service requests, ARC items, violations, notes, new owners at resale, vendors and 1099 adjustments.
- **Financials: yes, with one trick.** The chart of accounts returns a lifetime `Balance` and a fiscal-year `FYBalance` per account. That gives a balance sheet and a YTD income statement at any moment. There is **no GL journal endpoint and no "activity for a period" endpoint**, so a *monthly* income statement comes from the difference between two snapshots of `FYBalance`. We snapshot the chart of accounts every night and on the 1st; month = end snapshot minus start snapshot. Budgets do not exist in the API at all, so we hold the budget.
- **Bank reconciliation: not through the API.** No bank transactions, no reconciliation endpoint. Bank data enters Caliber through its bank integrations (First Citizens is a listed Caliber partner, with CheckAlt lockbox since 2026) and the reconciliation is done inside the Caliber desktop/web product. Our accountant reviews it there; the API lets us *verify* (cash GL balance vs bank statement balance) and *explain* (AP payments and AR applied payments account for most cash movement).
- **Communications: nothing.** No email, SMS, letter generation or mail. Caliber can print templated letters internally (`printeddocument`), but we cannot trigger them. We send everything ourselves and log it back as a note on the unit account.
- **Setup: nothing.** No client, unit, billing-record or chart-of-accounts creation. New communities are set up in the Caliber UI (by us with a Caliber login, or by FrontSteps onboarding). Assessment schedules (billing records) and late-fee rules are read-only.

## By function

Legend for "Automation": **A** fully automatic via API · **D** hey drafts/decides, person confirms (in our portal or in Caliber) · **UI** done by a person in the Caliber UI, API gives visibility · **X** outside Caliber entirely (our stack or a vendor).

### Financial statements and reporting
| Need | API | Automation | How |
|---|---|---|---|
| Balance sheet | `client/{id}/chartofaccounts` (`Balance`) | A | Assets/liabilities/equity from COA at snapshot date. Operating vs reserve by account or cost center (`costcenters`). |
| YTD income statement | `chartofaccounts` (`FYBalance`) | A | Income/expense accounts' FY balance. |
| Monthly income statement | derived | A | Nightly COA snapshots in our DB; month = Δ FYBalance. First month after go-live needs an opening snapshot on day 1. Prior-year comparatives need Caliber's own reports until we have 13 months of snapshots. |
| Budget vs actual | **no budget in API** | A (ours) | `BudgetLine` table in our DB per community/fiscal year/account; actuals from snapshots. Board approves the budget in our portal. |
| AR aging | `client/{id}/delinquencies`, `client/{id}/charges/{since}`, `unitaccount/{id}/openchargessummary` | A | Delinquency list gives balances and (we expect) aging; charges give the open items. Verify fields. |
| AP aging | `client/{id}/invoices?histType=…`, `invoice/{id}/details` | A | Invoices with Received/Validated/Approved/ReadyToPay/APPosted flags and due dates. |
| GL detail | **no journal endpoint** | UI | Only owner-ledger transactions (`client/{id}/transactions/{tAcct}/{since}`), AP invoices/payments and AR applied payments are exposed. Full GL detail is a Caliber report; the accountant exports it monthly and we attach it. |
| Bank reconciliation | **none** | UI | Done in Caliber with the bank integration. We verify: COA cash balance vs bank statement balance; flag if the statement date rec is not marked done. |
| Monthly packet PDF | assembled by us | A + review | Snapshots + delinquencies + AP + budget → packet; accountant reviews before the 5th. |
| Year-end 1099s | `client/{id}/1099adj/{year}`, `vendor/{id}/*`, `POST vendor/1099adj` | D | Vendor totals and adjustments readable; filing itself is ours (or Caliber's 1099 module in the UI). |

### Accounts receivable (dues)
| Need | API | Automation | How |
|---|---|---|---|
| Owner balance, ledger, statements | `unitaccount/{id}/ledger/{tAcct}/{from}`, `.../statements`, `.../openchargessummary` | A | Portal reads live. `tAcctId=-1` returns all ledgers. |
| Assessment billing | `client/{id}/billingrecords/*` (read-only) | UI | Caliber generates charges from billing records on schedule. We read them; we cannot create or change the schedule. |
| Online payment | `paymentproviders` (hosted redirect), `POST paymentaccepted` | A | Owner pays on the provider's hosted page; we mark accepted. Card/ACH flow is the provider's. |
| Autopay (ACH) | `GET/POST/PUT unitaccount/{id}/ach`, `achoptions` | A | Full CRUD on ACH definitions and plans, including one-time ACH (`PaymentPlanType` 1). Owner self-service in portal. |
| Payment plans | `achpaymentplan` POST/PUT | A | Plan = ACH payment plan with start/end and amount. Policy rules (max 6 months, $75 fee) enforced by us; fee posted via `postfine`? **Verify**: `postfine` is for fines; a plan setup fee may need the UI. |
| Late fees | billing/late-fee rules in Caliber | UI (auto inside Caliber) | Caliber posts late fees per its configuration. We read, we do not post. |
| Fines (violations) | `POST postfine` | D | hey drafts, board or coordinator confirms, we post. |
| Waivers, credits, adjustments | **none** | UI | Reversing a late fee or applying a credit is a Caliber UI task. Log the request as a ticket; accountant does it; hey writes the note. |
| Lockbox / mailed checks | CheckAlt/bank lockbox → Caliber | X/UI | Flows into Caliber from the lockbox; we see it as applied payments. |
| Collections notices | `delinquencies` read; letters are ours | D | hey drafts from ledger + policy; person sends; `POST unitaccount/{id}/addnote` records it; collection fee via `postfine`. Caliber's own delinquency letters (`printeddocument`) are readable if the accountant runs them in the UI instead. |

### Accounts payable (vendor bills)
| Need | API | Automation | How |
|---|---|---|---|
| Invoice intake | `POST invoice` / `invoice/embed` with line items, GL, cost center, PO, terms | A | hey extracts from the PDF (email or upload), codes it, posts it with `APBasis`. Attach the PDF: `POST invoice/{id}/document`. |
| Duplicate / contract check | `client/{id}/invoices`, `vendor/{id}/invoices`, `vendor/{id}/payments/{days}` | A | 12-month vendor history for trend and duplicate detection before posting. |
| Board approval | `POST invoice/{id}/{clientContactId}/action` (`Approve`/`Reject`) | A | Our portal buttons call this with the board member's `clientContactId`; Caliber tracks `ActualNumberOfApprovals`. |
| Payment | `POST payment` (check/ACH, `PaymentType`, `CheckNumber`, `ACHBatchID`), `payment/{id}/void`, `checkimage` | D/UI | Payment *records* can be posted. **Actual disbursement** (check printing, ACH origination, positive pay) runs through Caliber's bank module and the bank. Expect: accountant releases a payment batch in Caliber UI; we read it back. |
| Vendor onboarding, W-9, COI | `POST vendor`, `vendor/{id}/contact`, `vendor/{id}/insurance` (read) | A/UI | Create vendors from the API; insurance records appear read-only, so COI entry may be UI. |
| 1099 adjustments | `POST vendor/1099adj` | A | |

### Owners, units, access
| Need | API | Automation |
|---|---|---|
| Roster, contacts, units, occupants, renters | `client/{id}/units`, `owners/current`, `contact/*`, `unit/{id}/currentowners` | A (read) |
| Contact updates (email, phone, mailing address, family, pets, vehicles via pbk) | `PUT/POST/PATCH contact/{id}/*`, `mailmatrix` | A (owner self-service, logged) |
| Communication preferences | `mailmatrix` (mail vs email per correspondence type), `optout` | A |
| Portal accounts | `requestnewuseraccount`, `resetpassword`, `login` (Basic), `multipass` | A, but **decision**: use Caliber accounts or our own magic links mapped to `contactId`. Recommend our own auth + Caliber ids. |
| New owner at closing | `POST unitaccount/{unitId}/addnewowner` (+contacts, docs, escrow date, deed names), `unit/{id}/escrowdocsalert` | A | hey processes the closing packet, posts the new owner, triggers the alert. |
| Resale / disclosure data | `client/{id}/resale`, `unit/{id}/resale`, `unitaccount/{id}/resale`, `client/{id}/unitresale/all` | A | Data for the resale package; the package document is ours. |

### Requests, ARC, violations, documents
| Need | API | Automation |
|---|---|---|
| Maintenance / service requests | `POST unit/{id}/servicerequest` (KB category), `maintenance/{id}/*`, `client/{id}/workorders/open` | A intake; vendor dispatch is a board decision in our portal; Caliber work order status read-only |
| ARC | `architectural/savenew`, `documentupload`, `boardapprove`, `note`, `types` | A intake; D decisions (committee clicks) |
| Violations | `POST violation`, `violation/{id}/*`, categories | D (Board+). Letters are ours; Caliber's printed letters readable if run in UI |
| Documents | `client/{id}/documents`, `document/{id}`, `hierarchy/docs` read; upload only for ARC/violation/invoice | A read; **uploading governing docs is UI** |
| Notes | `client/{id}/notes`, `unitaccount/{id}/addnote`, `clientcontact/*/notes` | A | Every hey action gets a note with `InternalViewOnly`/`BoardMembersOK` set correctly |
| Meetings, minutes, elections, announcements | **none** | X | Ours entirely |

### Setup and administration (Caliber UI only)
Client (community) creation · units and lots · chart of accounts and cost centers · billing records and assessment schedules · late-fee rules · bank accounts and the bank integration · check stock, positive pay, ACH origination · governing document upload · letter templates · user roles for Caliber desktop · reserve/budget (not in Caliber; ours).

## What this means for the operating model
1. **One Caliber desktop seat per accountant**, used for: community setup, bank reconciliation sign-off, payment batch release, adjustments and waivers, GL export, letter templates if we use them. Everything else happens in our portal and through the API.
2. **Our database holds what Caliber lacks:** budgets, COA snapshots, reserve studies and components, policies (collections, ARC rules), meeting records, communications log, tickets, the community knowledge base hey reads from.
3. **hey's write surface is deliberately small:** invoices, approvals, fines, ACH plans, contact updates, service requests, ARC items, notes, new owners. Each write is logged in our audit table with the payload. Anything else goes to a ticket for a person.
4. **The monthly close is a pipeline, not a project:** nightly snapshots → 1st: opening snapshot + draft packet → accountant reconciles in Caliber (bank feed) → hey re-renders packet with final numbers and writes the summary → accountant review → delivered by the 5th business day.

## Verification list (first day with a real key)
Run against the sandbox, then a Heywood tenant. Record real payload keys in `docs/api/observed-payloads.md` and fix `_map_*` in `app/integrations/frontsteps.py`.
1. `GET ping`, `GET time`, `GET mgmtco` — auth works.
2. `GET clientlist` → pick a client id.
3. `GET client/{id}/chartofaccounts` — confirm `Balance`, `FYBalance`, account type/number fields, operating vs reserve indicator.
4. `GET client/{id}/costcenters`, `transactionaccounts`, `postingcodes/all`.
5. `GET client/{id}/units` and one `unitaccount/{id}/ledger/-1/2026-01-01` — ledger shape, running balance.
6. `GET client/{id}/delinquencies` — is aging included or only balance?
7. `GET client/{id}/invoices` with `histType` 0/1/2 — which flags drive "pending board".
8. `GET client/{id}/billingrecords/current` — assessment amount/frequency per unit.
9. `GET unitaccount/{id}/ach` and `achoptions` — bank account handling and whether routing numbers are exposed (PCI/NACHA handling).
10. `GET paymentproviders` with a contact context — hosted payment URL shape.
11. `GET client/{id}/documents` + one `document/{id}` — binary vs link.
12. **Write tests in sandbox only:** `POST unitaccount/{id}/addnote`, `POST invoice` + `invoice/{id}/document`, `POST invoice/{id}/{cc}/action`, `POST unit/{id}/servicerequest`, `POST postfine` with a $0.01 fine, `POST unitaccount/{id}/ach` one-time. Confirm each shows in the Caliber UI.
13. Ask FrontSteps: rate limits, webhooks (none in spec; we poll), sandbox data reset, whether `transactions` for the cash transaction account exists, whether an invoice can be edited after posting, how payment release works with the First Citizens integration.

## Open questions for FrontSteps / Caliber
- Is there any endpoint or export for GL activity by period, or only the UI report?
- Can `postfine` post a negative amount (credit) or is there another adjustment path?
- Does `POST payment` create a payable disbursement that the bank module will release, or only a record of a payment made elsewhere?
- Webhooks or change feeds (`clientlist/{sinceDate}` and `*/{sinceDate}` variants suggest polling by date is the intended pattern).
- Document upload for client-level documents.
- API access terms for a self-managed association vs a management company tenant; per-tenant keys.
