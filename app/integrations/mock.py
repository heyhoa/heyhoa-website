"""Deterministic demo data so every portal page renders without credentials.

Two communities, one homeowner, one board member. Mutations (approvals, new
requests) persist for the life of the process so click-throughs feel real.
"""
from __future__ import annotations

import datetime as dt

from .base import (
    AccountingProvider,
    ArcRequest,
    Community,
    Delinquency,
    Document,
    FinancialSnapshot,
    Invoice,
    LedgerLine,
    ServiceRequest,
    UnitAccount,
    Vendor,
    Violation,
)

TODAY = dt.date(2026, 10, 24)


def _d(days_ago: int) -> str:
    return (TODAY - dt.timedelta(days=days_ago)).isoformat()


COMMUNITIES = {
    "1001": Community(id="1001", name="Willow Creek Townhomes", kind="townhome", units=48, city="Round Rock", state="TX", dues_frequency="monthly"),
    "1002": Community(id="1002", name="Maple Court Condominiums", kind="condo", units=24, city="Fort Collins", state="CO", fiscal_year_end="06/30", dues_frequency="quarterly"),
}

_OWNERS = [
    ("Reed, Marcus & Priya", "12"), ("Okafor, Chidi", "3"), ("Lindqvist, Anna", "7"), ("Whitfield, Dana", "21"),
    ("Nguyen, Tam", "9"), ("Bauer, Hannah", "14"), ("Castillo, Luis", "18"), ("Patel, Riya", "22"),
    ("Thompson, Grace", "27"), ("Yamada, Ken", "31"), ("Osei, Kwame", "35"), ("Fischer, Lena", "40"),
    ("Moreau, Elise", "44"), ("Dubois, Theo", "2"), ("Hassan, Omar", "5"), ("Kowalski, Piotr", "11"),
]

UNIT_ACCOUNTS: dict[str, UnitAccount] = {}
for i, (name, unit) in enumerate(_OWNERS):
    uid = f"ua-10{int(unit):02d}"
    balance = 0.0
    status = "current"
    if unit == "3":
        balance, status = 1240.00, "collections"
    elif unit == "14":
        balance, status = 620.00, "late"
    elif unit == "31":
        balance, status = 310.00, "late"
    elif unit == "40":
        balance, status = 930.00, "late"
    elif unit == "12":
        balance = 0.0
    UNIT_ACCOUNTS[uid] = UnitAccount(
        id=uid, community_id="1001", unit_label=f"Unit {unit}", address=f"{1200 + int(unit) * 2} Willow Creek Dr",
        owner_name=name, email=f"{name.split(',')[0].lower()}@example.com", phone="(512) 555-01" + unit.zfill(2),
        balance=balance, autopay=(i % 3 != 0), next_due_date="2026-11-01", next_due_amount=310.00, status=status,
    )

DEMO_HOMEOWNER = {"id": "contact-4412", "name": "Marcus Reed", "email": "marcus@example.com", "unit_account_id": "ua-1012", "community_id": "1001", "role": "homeowner"}
DEMO_BOARD = {"id": "cc-7", "name": "Dana Whitfield", "email": "treasurer@willowcreek.example", "title": "Treasurer", "community_id": "1001", "role": "board"}

LEDGER = {
    "ua-1012": [
        LedgerLine(_d(145), "Monthly assessment — June", 310.00, 0, 310.00),
        LedgerLine(_d(140), "ACH autopay", 0, 310.00, 0.00),
        LedgerLine(_d(115), "Monthly assessment — July", 310.00, 0, 310.00),
        LedgerLine(_d(110), "ACH autopay", 0, 310.00, 0.00),
        LedgerLine(_d(84), "Monthly assessment — August", 310.00, 0, 310.00),
        LedgerLine(_d(79), "ACH autopay", 0, 310.00, 0.00),
        LedgerLine(_d(53), "Monthly assessment — September", 310.00, 0, 310.00),
        LedgerLine(_d(48), "ACH autopay", 0, 310.00, 0.00),
        LedgerLine(_d(23), "Monthly assessment — October", 310.00, 0, 310.00),
        LedgerLine(_d(18), "ACH autopay", 0, 310.00, 0.00),
    ]
}

INVOICES: dict[str, Invoice] = {
    "inv-5101": Invoice("inv-5101", "1001", "GreenScape Lawn Co", "GS-20412", 1850.00, _d(6), _d(-24), "6210 Landscaping", "October landscape maintenance", "pending_board", ai_note="Matches contract rate ($1,850/mo). Coded to 6210 Landscaping. 12 of 12 invoices this year matched.", approvals=1),
    "inv-5102": Invoice("inv-5102", "1001", "Austin Pool Service", "AP-889", 640.00, _d(4), _d(-26), "6240 Pool", "Weekly service Oct + chemical balance", "pending_board", ai_note="Amount is 28% above the 12-month average ($498). Line item: chlorine shock treatment $142. Flagged for board review.", approvals=0),
    "inv-5103": Invoice("inv-5103", "1001", "City of Round Rock Utilities", "77-10-2026", 412.37, _d(9), _d(-5), "6310 Water/Irrigation", "Irrigation meter Sept", "pending_board", ai_note="Utility bill. Within 5% of same month last year. Recommend approve.", approvals=1),
    "inv-5104": Invoice("inv-5104", "1001", "Lone Star Insurance Agency", "LS-2026-Q4", 3975.00, _d(12), _d(-10), "6510 Insurance", "Q4 master policy premium", "pending_board", ai_note="Quarterly premium per policy #MP-44129. Unchanged from Q3. Recommend approve.", approvals=0),
    "inv-5105": Invoice("inv-5105", "1001", "GreenScape Lawn Co", "GS-20387", 1850.00, _d(36), _d(-2), "6210 Landscaping", "September landscape maintenance", "paid", approvals=2),
    "inv-5106": Invoice("inv-5106", "1001", "Bright Light Electric", "BL-1120", 285.00, _d(40), _d(-1), "6410 Repairs & Maintenance", "Replace entry monument lights", "paid", approvals=2),
    "inv-5107": Invoice("inv-5107", "1001", "Hill Country Reserve Studies", "HC-301", 2400.00, _d(60), _d(30), "7100 Reserve Study", "Level II reserve study update", "paid", approvals=2),
}

DELINQUENCIES = [
    Delinquency("ua-1003", "Unit 3", "Okafor, Chidi", 1240.00, 124, "demand", "Demand letter mailed " + _d(14), "Lien warning due " + _d(-16)),
    Delinquency("ua-1040", "Unit 40", "Fischer, Lena", 930.00, 93, "late_notice", "Second notice emailed " + _d(7), "Demand letter " + _d(-7)),
    Delinquency("ua-1014", "Unit 14", "Bauer, Hannah", 620.00, 62, "late_notice", "First notice emailed " + _d(31), "Second notice " + _d(-1)),
    Delinquency("ua-1031", "Unit 31", "Yamada, Ken", 310.00, 23, "reminder", "Friendly reminder text " + _d(8), "Late fee posts " + _d(-7)),
]

SERVICE_REQUESTS: dict[str, ServiceRequest] = {
    "sr-301": ServiceRequest("sr-301", "1001", "Unit 12", "Irrigation", "Sprinkler head broken at corner of Unit 12 / common area; spraying sidewalk", "in_progress", _d(5), "GreenScape Lawn Co"),
    "sr-302": ServiceRequest("sr-302", "1001", "Common area", "Lighting", "Pool pathway light out near gate B", "open", _d(2)),
    "sr-303": ServiceRequest("sr-303", "1001", "Unit 27", "Fence", "Shared fence panel leaning after storm", "awaiting_bid", _d(11), "Fence Masters"),
    "sr-304": ServiceRequest("sr-304", "1001", "Unit 12", "Roof", "Gutter overflow on north side", "closed", _d(70), "Top Notch Gutters"),
}

ARC_REQUESTS: dict[str, ArcRequest] = {
    "arc-71": ArcRequest("arc-71", "1001", "Unit 12", "Reed, Marcus & Priya", "Exterior paint (approved palette: Sandstone)", _d(9), "under_review", approvals=2, approvals_required=3, notes="Color sample attached. Matches approved palette B."),
    "arc-72": ArcRequest("arc-72", "1001", "Unit 22", "Patel, Riya", "Solar panels (rear roof)", _d(3), "submitted", approvals=0, notes="State law limits HOA restrictions on solar; review for placement only."),
    "arc-73": ArcRequest("arc-73", "1001", "Unit 5", "Hassan, Omar", "Backyard pergola 12x14", _d(20), "approved", approvals=3),
    "arc-74": ArcRequest("arc-74", "1001", "Unit 44", "Moreau, Elise", "Front door replacement (black)", _d(27), "more_info", approvals=1, notes="Need manufacturer spec sheet."),
}

DOCUMENTS = [
    Document("doc-1", "CC&Rs (Declaration) — recorded 2004", "governing", "2004-03-11"),
    Document("doc-2", "Bylaws — amended 2019", "governing", "2019-06-02"),
    Document("doc-3", "Rules & Regulations", "governing", "2024-01-15"),
    Document("doc-4", "Approved exterior paint palette", "arc", "2023-04-01"),
    Document("doc-5", "ARC application form", "arc", "2023-04-01"),
    Document("doc-6", "2026 Approved budget", "financial", "2025-11-20"),
    Document("doc-7", "Reserve study — Level II (2026)", "financial", "2026-08-30"),
    Document("doc-8", "September 2026 financial packet", "financial", "2026-10-05", board_only=False),
    Document("doc-9", "Annual meeting minutes — 2026", "meetings", "2026-02-18"),
    Document("doc-10", "Master insurance certificate", "insurance", "2026-07-01"),
    Document("doc-11", "Bank reconciliation — Sept 2026 (board)", "financial", "2026-10-03", board_only=True),
    Document("doc-12", "Collections policy (board)", "policy", "2025-05-10", board_only=True),
]

VENDORS = [
    Vendor("v-1", "GreenScape Lawn Co", "Landscaping", "(512) 555-0142", "ar@greenscape.example", "2027-03-01", True, 18500.00),
    Vendor("v-2", "Austin Pool Service", "Pool", "(512) 555-0177", "billing@austinpool.example", "2026-12-15", True, 5120.00),
    Vendor("v-3", "Bright Light Electric", "Electrical", "(512) 555-0110", "jobs@brightlight.example", "2026-11-02", True, 1385.00),
    Vendor("v-4", "Fence Masters", "Fencing", "(512) 555-0156", "quotes@fencemasters.example", "2026-10-30", False, 0.00),
    Vendor("v-5", "Lone Star Insurance Agency", "Insurance", "(512) 555-0199", "service@lonestarins.example", "2027-07-01", True, 15900.00),
    Vendor("v-6", "Hill Country Reserve Studies", "Consulting", "(512) 555-0188", "hello@hcrs.example", "2027-01-20", True, 2400.00),
]

VIOLATIONS = [
    Violation("vio-11", "Unit 18", "Trash cans visible", _d(12), "courtesy_notice", "open"),
    Violation("vio-12", "Unit 35", "Unapproved exterior change (shutters)", _d(30), "first_notice", "open"),
    Violation("vio-13", "Unit 9", "Lawn maintenance", _d(45), "resolved", "closed"),
]

CHART_OF_ACCOUNTS = [
    {"number": "1010", "name": "Operating cash — Frost Bank", "type": "Asset", "balance": 48210.55},
    {"number": "1020", "name": "Reserve cash — Frost MM", "type": "Asset", "balance": 162480.00},
    {"number": "1200", "name": "Assessments receivable", "type": "Asset", "balance": 3100.00},
    {"number": "2010", "name": "Accounts payable", "type": "Liability", "balance": 6877.37},
    {"number": "2100", "name": "Prepaid assessments", "type": "Liability", "balance": 1860.00},
    {"number": "4010", "name": "Assessment income", "type": "Income", "balance": 148800.00},
    {"number": "4100", "name": "Late fees & interest", "type": "Income", "balance": 925.00},
    {"number": "6210", "name": "Landscaping", "type": "Expense", "balance": 18500.00},
    {"number": "6240", "name": "Pool", "type": "Expense", "balance": 5120.00},
    {"number": "6310", "name": "Water / irrigation", "type": "Expense", "balance": 3890.12},
    {"number": "6410", "name": "Repairs & maintenance", "type": "Expense", "balance": 6410.00},
    {"number": "6510", "name": "Insurance", "type": "Expense", "balance": 11925.00},
    {"number": "6610", "name": "Management / accounting", "type": "Expense", "balance": 4290.00},
    {"number": "7100", "name": "Reserve study", "type": "Expense", "balance": 2400.00},
    {"number": "9010", "name": "Reserve contribution", "type": "Expense", "balance": 36000.00},
]


class MockProvider(AccountingProvider):
    name = "mock"

    def list_communities(self):
        return list(COMMUNITIES.values())

    def get_community(self, community_id):
        return COMMUNITIES[str(community_id)]

    def list_unit_accounts(self, community_id):
        return sorted(UNIT_ACCOUNTS.values(), key=lambda u: int(u.unit_label.split()[1]))

    def get_unit_account(self, unit_account_id):
        return UNIT_ACCOUNTS[unit_account_id]

    def get_ledger(self, unit_account_id, since=None):
        return list(reversed(LEDGER.get(unit_account_id, [])))

    def get_statements(self, unit_account_id):
        return [Document(f"st-{m}", f"Statement — {m}", "statement", f"2026-{m}-01") for m in ("10", "09", "08", "07", "06", "05")]

    def get_financial_snapshot(self, community_id):
        months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
        return FinancialSnapshot(
            as_of="2026-10-24",
            operating_cash=48210.55, reserve_cash=162480.00, ar_total=3100.00, ar_over_60=2790.00,
            ap_pending=6877.37, ytd_income=149725.00, ytd_expense=88535.12, ytd_budget_income=148800.00, ytd_budget_expense=92400.00,
            recon_status="September reconciled Oct 3 · October in progress", packet_ready=True, last_packet_date="2026-10-05",
            income_lines=[("Assessments", 148800.00, 148800.00), ("Late fees & interest", 925.00, 600.00), ("Other", 0.00, 0.00)],
            expense_lines=[("Landscaping", 18500.00, 18500.00), ("Pool", 5120.00, 4800.00), ("Water / irrigation", 3890.12, 4200.00), ("Repairs & maintenance", 6410.00, 7500.00), ("Insurance", 11925.00, 11925.00), ("Management / accounting", 4290.00, 4290.00), ("Reserve study", 2400.00, 2400.00), ("Reserve contribution", 36000.00, 36000.00)],
            monthly_cash=[(m, v, r) for m, v, r in zip(months, [41200, 43900, 45100, 44300, 46800, 48210], [142480, 146480, 150480, 154480, 158480, 162480])],
        )

    def get_chart_of_accounts(self, community_id):
        return CHART_OF_ACCOUNTS

    def list_invoices(self, community_id, status=None):
        inv = [i for i in INVOICES.values() if i.community_id == str(community_id)]
        if status:
            inv = [i for i in inv if i.status == status]
        return sorted(inv, key=lambda i: i.invoice_date, reverse=True)

    def act_on_invoice(self, invoice_id, actor_id, action, note=""):
        inv = INVOICES[invoice_id]
        if action == "approve":
            inv.approvals += 1
            if inv.approvals >= inv.approvals_required:
                inv.status = "approved"
        elif action == "reject":
            inv.status = "rejected"
            inv.ai_note = (inv.ai_note or "") + f" Rejected: {note}"
        elif action == "hold":
            inv.ai_note = (inv.ai_note or "") + f" On hold: {note}"
        return inv

    def list_delinquencies(self, community_id):
        return sorted(DELINQUENCIES, key=lambda d: -d.balance)

    def list_service_requests(self, community_id, unit_account_id=None):
        rows = list(SERVICE_REQUESTS.values())
        if unit_account_id:
            ua = UNIT_ACCOUNTS[unit_account_id]
            rows = [r for r in rows if r.unit_label == ua.unit_label]
        return sorted(rows, key=lambda r: r.created, reverse=True)

    def create_service_request(self, community_id, unit_account_id, category, summary):
        ua = UNIT_ACCOUNTS[unit_account_id]
        rid = f"sr-{300 + len(SERVICE_REQUESTS) + 1}"
        sr = ServiceRequest(rid, str(community_id), ua.unit_label, category, summary, "open", TODAY.isoformat())
        SERVICE_REQUESTS[rid] = sr
        return sr

    def list_arc_requests(self, community_id, unit_account_id=None):
        rows = list(ARC_REQUESTS.values())
        if unit_account_id:
            ua = UNIT_ACCOUNTS[unit_account_id]
            rows = [r for r in rows if r.unit_label == ua.unit_label]
        return sorted(rows, key=lambda r: r.submitted, reverse=True)

    def create_arc_request(self, community_id, unit_account_id, request_type, notes):
        ua = UNIT_ACCOUNTS[unit_account_id]
        rid = f"arc-{70 + len(ARC_REQUESTS) + 1}"
        arc = ArcRequest(rid, str(community_id), ua.unit_label, ua.owner_name, request_type, TODAY.isoformat(), "submitted", notes=notes)
        ARC_REQUESTS[rid] = arc
        return arc

    def act_on_arc(self, arc_id, actor_id, action, note=""):
        arc = ARC_REQUESTS[arc_id]
        if action == "approve":
            arc.approvals += 1
            arc.status = "approved" if arc.approvals >= arc.approvals_required else "under_review"
        elif action == "deny":
            arc.status = "denied"
            arc.notes = (arc.notes + " " + note).strip()
        elif action == "more_info":
            arc.status = "more_info"
            arc.notes = (arc.notes + " " + note).strip()
        return arc

    def list_documents(self, community_id, board=False):
        return [d for d in DOCUMENTS if board or not d.board_only]

    def list_vendors(self, community_id):
        return VENDORS

    def list_violations(self, community_id):
        return VIOLATIONS

    def post_payment(self, unit_account_id, amount, method):
        ua = UNIT_ACCOUNTS[unit_account_id]
        ua.balance = round(ua.balance - amount, 2)
        LEDGER.setdefault(unit_account_id, []).append(LedgerLine(TODAY.isoformat(), f"Online payment ({method})", 0, amount, ua.balance))
        return {"ok": True, "confirmation": f"HEY-{unit_account_id[-4:]}-{int(amount)}", "balance": ua.balance}
