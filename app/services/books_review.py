"""Free books review: what the accountant looks for, and the one-page findings memo.

The offer: send three recent bank statements (plus whatever else they have) and in two business days
we say what we found. The memo is the sales document; the checklist is the work.
"""
from __future__ import annotations

CHECKLIST: list[tuple[str, str, list[str]]] = [
    ("cash", "Cash and reconciliation", [
        "Does the last statement balance tie to the books, to the penny? If there are no books, say so.",
        "Operating and reserve in separate accounts, both in the association's name and TIN?",
        "Any account with no activity for 90+ days, or a balance that never changes (orphaned CD, old lockbox)?",
        "Reserve balance vs the last reserve study's recommended balance (percent funded).",
    ]),
    ("income", "Assessments and collections", [
        "Monthly deposits vs units × assessment: what percent is collected in the month it is due?",
        "Any month with deposits below 85% of billed: who is behind, and is anyone acting on it?",
        "Late fees, interest and collection fees: charged per the governing documents or not at all?",
        "Prepaid dues sitting in cash that the board may be reading as surplus.",
    ]),
    ("vendors", "Vendors and disbursements", [
        "Same payee, same amount, within 45 days: duplicate payment candidates.",
        "Any payee paid more than 12 times in 12 months, or a monthly amount that stepped up without a contract change.",
        "Vendors paid over $600 with no W-9 on file (1099 exposure).",
        "Payments to individuals, board members or round-number transfers with no invoice.",
        "Insurance, utilities and tax payments present every period they should be; missing ones are the finding.",
    ]),
    ("controls", "Controls and reporting", [
        "Who can move money alone? One signer, debit card, or online banking without dual approval is the finding.",
        "When did the board last receive a full package (budget comparison, balance sheet, aged balances, reconciliation)?",
        "Budget exists and is used: is spending compared to it monthly?",
        "Annual items: tax return filed, insurance renewed, corporate filing current, reserve study under 5 years old.",
    ]),
]

AREAS = [(k, label) for k, label, _ in CHECKLIST]
IMPACTS = ["high", "medium", "low", "note"]


def blank_review() -> dict:
    return {"months": "", "findings": [], "summary": "", "clean": [], "delivered_at": None}


def review_from_form(form, existing: dict | None) -> dict:
    r = dict(existing or blank_review())
    r["months"] = (form.get("months") or "").strip()
    r["summary"] = (form.get("summary") or "").strip()
    r["clean"] = [k for k, _ in AREAS if form.get(f"clean_{k}")]
    findings = []
    for i in range(0, 12):
        finding = (form.get(f"f{i}_finding") or "").strip()
        if not finding:
            continue
        findings.append({"area": form.get(f"f{i}_area") or "cash", "finding": finding, "impact": form.get(f"f{i}_impact") or "medium",
                         "amount": (form.get(f"f{i}_amount") or "").strip(), "fix": (form.get(f"f{i}_fix") or "").strip()})
    r["findings"] = findings
    return r
