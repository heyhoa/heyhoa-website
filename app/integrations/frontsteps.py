"""FrontSteps / Caliber API v2 (CAPI2) client.

Endpoints below come from the sandbox Swagger spec committed at
docs/api/frontsteps-caliber-v2.swagger.json (310 paths). The spec types most
responses as a bare `Object`, so this client parses defensively and maps the
fields we have seen in the field. Expect to adjust key names once we have a
real tenant key — every mapping lives in one `_map_*` function for that reason.

Auth: `apiKey` header. Owner/board scoped calls may also pass HTTP Basic
credentials, which limits `clientlist` to that user's association.
"""
from __future__ import annotations

import base64
import logging
from typing import Any

import requests

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

log = logging.getLogger(__name__)


class FrontStepsError(RuntimeError):
    pass


class FrontStepsClient:
    """Thin HTTP wrapper. One method per endpoint we use, named after the path."""

    def __init__(self, base_url: str, api_key: str, username: str | None = None, password: str | None = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.s = requests.Session()
        self.s.headers.update({"apiKey": api_key, "Accept": "application/json"})
        if username and password:
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
            self.s.headers["Authorization"] = f"Basic {token}"

    # ---- core -------------------------------------------------------------
    def _req(self, method: str, path: str, **kw) -> Any:
        url = f"{self.base_url}{path}"
        r = self.s.request(method, url, timeout=self.timeout, **kw)
        if r.status_code >= 400:
            raise FrontStepsError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        if not r.content:
            return None
        try:
            return r.json()
        except ValueError:
            return r.text

    def get(self, path, **params):
        return self._req("GET", path, params=params or None)

    def post(self, path, json=None):
        return self._req("POST", path, json=json)

    def put(self, path, json=None):
        return self._req("PUT", path, json=json)

    # ---- Misc / health ----------------------------------------------------
    def ping(self):
        return self.get("/api/v2/ping")

    def time(self):
        return self.get("/api/v2/time")

    def mgmtco(self):
        return self.get("/api/v2/mgmtco")

    # ---- Clients (associations) -------------------------------------------
    def clientlist(self, since: str | None = None):
        return self.get(f"/api/v2/clientlist/{since}" if since else "/api/v2/clientlist")

    def client(self, client_id):
        return self.get(f"/api/v2/client/{client_id}")

    def client_units(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/units")

    def client_owners_current(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/owners/current")

    def client_clientcontacts(self, client_id):
        """Board members / management contacts."""
        return self.get(f"/api/v2/client/{client_id}/clientcontacts")

    def client_chart_of_accounts(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/chartofaccounts")

    def client_transaction_accounts(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/transactionaccounts")

    def client_invoices(self, client_id, hist_type: int | None = None, start=None, end=None, sort=None):
        params = {k: v for k, v in {"histType": hist_type, "StartDate": start, "EndDate": end, "SortOrder": sort}.items() if v is not None}
        return self.get(f"/api/v2/client/{client_id}/invoices", **params)

    def client_delinquencies(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/delinquencies")

    def client_billing_records_current(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/billingrecords/current")

    def client_applied_payments(self, client_id, start, end):
        return self.get(f"/api/v2/client/{client_id}/appliedpayments/{start}/{end}")

    def client_charges(self, client_id, since):
        return self.get(f"/api/v2/client/{client_id}/charges/{since}")

    def client_transactions(self, client_id, tacct_id, since):
        return self.get(f"/api/v2/client/{client_id}/transactions/{tacct_id}/{since}")

    def client_documents(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/documents")

    def client_vendors(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/vendors")

    def client_insurance(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/insurance")

    def client_maintenance(self, client_id, all_=False):
        return self.get(f"/api/v2/client/{client_id}/maintenance" + ("/all" if all_ else ""))

    def client_workorders_open(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/workorders/open")

    def client_violations(self, client_id, scope: str = ""):
        return self.get(f"/api/v2/client/{client_id}/violations" + (f"/{scope}" if scope else ""))

    def client_architectural_items(self, client_id, hist_type: int | None = None):
        p = f"/api/v2/client/{client_id}/architecturalitems"
        return self.get(p + (f"/{hist_type}" if hist_type is not None else ""))

    def client_resale(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/resale")

    def client_1099adj(self, client_id, tax_year):
        return self.get(f"/api/v2/client/{client_id}/1099adj/{tax_year}")

    def client_factsheet(self, client_id):
        return self.get(f"/api/v2/client/{client_id}/factsheet")

    def client_pending_payments(self, client_id):
        return self.get(f"/api/v2/pendingpayments/{client_id}")

    # ---- Units / unit accounts (homeowner ledgers) ------------------------
    def unit(self, unit_id):
        return self.get(f"/api/v2/unit/{unit_id}")

    def unit_account(self, unit_account_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}")

    def unit_account_ledger(self, unit_account_id, tacct_id=0, from_date="2000-01-01"):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/ledger/{tacct_id}/{from_date}")

    def unit_account_transactions_all(self, unit_account_id, from_date="2000-01-01"):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/transactions/all/{from_date}")

    def unit_account_statements(self, unit_account_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/statements")

    def unit_account_statement(self, unit_account_id, statement_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/statements/{statement_id}")

    def unit_account_open_charges(self, unit_account_id, tacct_id=0):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/openchargessummary/{tacct_id}")

    def unit_account_contacts(self, unit_account_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/contacts")

    def unit_account_ach(self, unit_account_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/ach")

    def unit_account_ach_set(self, unit_account_id, ach_definition: dict):
        return self.put(f"/api/v2/unitaccount/{unit_account_id}/ach", json=ach_definition)

    def unit_account_ach_plan_set(self, unit_account_id, plan: dict):
        return self.put(f"/api/v2/unitaccount/{unit_account_id}/achpaymentplan", json=plan)

    def unit_account_delinquencies(self, unit_account_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/delinquencies")

    def unit_account_architectural(self, unit_account_id, scope=""):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/architectural" + (f"/{scope}" if scope else ""))

    def unit_account_maintenance(self, unit_account_id, scope=""):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/maintenance" + (f"/{scope}" if scope else ""))

    def unit_account_documents(self, unit_account_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/documents")

    def unit_account_resale(self, unit_account_id):
        return self.get(f"/api/v2/unitaccount/{unit_account_id}/resale")

    def unit_add_new_owner(self, unit_id, owner: dict):
        return self.post(f"/api/v2/unitaccount/{unit_id}/addnewowner", json=owner)

    def unit_escrow_docs_alert(self, unit_id, alert: dict):
        return self.post(f"/api/v2/unit/{unit_id}/escrowdocsalert", json=alert)

    # ---- Contacts (homeowners) --------------------------------------------
    def contact(self, contact_id):
        return self.get(f"/api/v2/contact/{contact_id}")

    def contact_details(self, contact_id):
        return self.get(f"/api/v2/contact/{contact_id}/contactdetails")

    def contact_units(self, contact_id):
        return self.get(f"/api/v2/contact/{contact_id}/units")

    def contact_update(self, contact_id, payload: dict):
        return self.put(f"/api/v2/contact/{contact_id}", json=payload)

    def contact_add_email(self, contact_id, email: dict):
        return self.post(f"/api/v2/contact/{contact_id}/email", json=email)

    def contact_add_phone(self, contact_id, phone: dict):
        return self.post(f"/api/v2/contact/{contact_id}/phone", json=phone)

    def search_contacts(self, first, last, scope="current"):
        return self.get(f"/api/v2/searchcontacts/{scope}/{first}/{last}")

    # ---- Login / account provisioning ------------------------------------
    def login(self):
        """Validates the Basic credentials on the session. Returns user object."""
        return self.get("/api/v2/login")

    def request_new_user_account(self, payload: dict):
        return self.post("/api/v2/requestnewuseraccount", json=payload)

    def reset_password(self, payload: dict):
        return self.post("/api/v2/resetpassword", json=payload)

    # ---- AP: invoices ------------------------------------------------------
    def invoice_details(self, invoice_id):
        return self.get(f"/api/v2/invoice/{invoice_id}/details")

    def invoice_line_items(self, invoice_id):
        return self.get(f"/api/v2/invoice/{invoice_id}/lineitems")

    def invoice_documents(self, invoice_id):
        return self.get(f"/api/v2/invoice/{invoice_id}/documents")

    def invoice_post(self, invoice: dict):
        return self.post("/api/v2/invoice", json=invoice)

    def invoice_action(self, invoice_id, client_contact_id, action: str, reject_text: str = ""):
        """Board approve/reject. `action` values observed: Approve | Reject | Hold."""
        return self.post(
            f"/api/v2/invoice/{invoice_id}/{client_contact_id}/action",
            json={"InvoiceID": invoice_id, "ClientContactID": client_contact_id, "Action": action, "RejectText": reject_text},
        )

    # ---- AR: payments / fines ---------------------------------------------
    def payment_post(self, payment: dict):
        return self.post("/api/v2/payment", json=payment)

    def payment_void(self, payment_id, reason, posting_date):
        return self.post(f"/api/v2/payment/{payment_id}/void", json={"Reason": reason, "PostingDate": posting_date})

    def post_fine(self, fine: dict):
        return self.post("/api/v2/postfine", json=fine)

    def payment_providers(self):
        return self.get("/api/v2/paymentproviders")

    # ---- Service requests / maintenance -----------------------------------
    def unit_service_request(self, unit_id, payload: dict):
        return self.post(f"/api/v2/unit/{unit_id}/servicerequest", json=payload)

    def maintenance(self, problem_id):
        return self.get(f"/api/v2/maintenance/{problem_id}")

    def maintenance_actions(self, problem_id):
        return self.get(f"/api/v2/maintenance/{problem_id}/actions")

    # ---- Architectural -----------------------------------------------------
    def architectural_types(self):
        return self.get("/api/v2/architectural/types")

    def architectural_item(self, arc_id):
        return self.get(f"/api/v2/architectural/item/{arc_id}")

    def architectural_savenew(self, payload: dict):
        return self.post("/api/v2/architectural/savenew", json=payload)

    def architectural_board_approve(self, payload: dict):
        return self.post("/api/v2/architectural/boardapprove", json=payload)

    def architectural_note(self, payload: dict):
        return self.post("/api/v2/architectural/note", json=payload)

    # ---- Violations --------------------------------------------------------
    def violation(self, violation_id):
        return self.get(f"/api/v2/violation/{violation_id}")

    def violation_create(self, payload: dict):
        return self.post("/api/v2/violation", json=payload)

    # ---- Vendors -----------------------------------------------------------
    def vendorlist(self):
        return self.get("/api/v2/vendorlist")

    def vendor(self, vendor_id):
        return self.get(f"/api/v2/vendor/{vendor_id}")

    def vendor_insurance(self, vendor_id):
        return self.get(f"/api/v2/vendor/{vendor_id}/insurance")

    def vendor_payments(self, vendor_id, days=365):
        return self.get(f"/api/v2/vendor/{vendor_id}/payments/{days}")

    def vendor_create(self, vendor: dict):
        return self.post("/api/v2/vendor", json=vendor)

    # ---- Documents ---------------------------------------------------------
    def document(self, document_id):
        return self.get(f"/api/v2/document/{document_id}")


def _g(d: Any, *keys, default=None):
    """Get first present key from a dict-like FrontSteps object."""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        for k in ("Items", "items", "Data", "data", "Results"):
            if isinstance(x.get(k), list):
                return x[k]
    return []


class FrontStepsProvider(AccountingProvider):
    """Maps CAPI2 payloads onto our provider dataclasses."""

    name = "frontsteps"

    def __init__(self, **kw):
        self.c = FrontStepsClient(**kw)

    # -- mapping helpers (adjust when real payloads differ) ------------------
    def _map_community(self, d) -> Community:
        return Community(
            id=str(_g(d, "ClientID", "ClientId", "Id", default="")),
            name=_g(d, "Name", "ClientName", default="Community"),
            kind=_g(d, "ClientType", "Type", default="hoa"),
            units=int(_g(d, "UnitCount", "Units", default=0) or 0),
            city=_g(d, "City", default=""),
            state=_g(d, "State", default=""),
            fiscal_year_end=_g(d, "FiscalYearEnd", default="12/31"),
        )

    def _map_unit_account(self, d) -> UnitAccount:
        bal = float(_g(d, "Balance", "CurrentBalance", default=0) or 0)
        return UnitAccount(
            id=str(_g(d, "UnitAccountID", "UnitAccountId", default="")),
            community_id=str(_g(d, "ClientID", default="")),
            unit_label=_g(d, "UnitNumber", "Unit", default=""),
            address=_g(d, "Address", "OneLine", default=""),
            owner_name=_g(d, "OwnerName", "DisplayName", default=""),
            email=_g(d, "Email", default=""),
            phone=_g(d, "Phone", default=""),
            balance=bal,
            autopay=bool(_g(d, "HasACH", "ACH", default=False)),
            next_due_date=_g(d, "NextDueDate", default=""),
            next_due_amount=float(_g(d, "NextDueAmount", "AssessmentAmount", default=0) or 0),
            status="late" if bal > 0 else "current",
        )

    # -- interface -----------------------------------------------------------
    def list_communities(self):
        return [self._map_community(d) for d in _list(self.c.clientlist())]

    def get_community(self, community_id):
        return self._map_community(self.c.client(community_id))

    def list_unit_accounts(self, community_id):
        out = []
        for u in _list(self.c.client_units(community_id)):
            ua = _g(u, "CurrentUnitAccount", "UnitAccount")
            out.append(self._map_unit_account({**u, **(ua or {})}))
        return out

    def get_unit_account(self, unit_account_id):
        return self._map_unit_account(self.c.unit_account(unit_account_id))

    def get_ledger(self, unit_account_id, since=None):
        rows = _list(self.c.unit_account_ledger(unit_account_id, 0, since or "2000-01-01"))
        out = []
        for r in rows:
            amt = float(_g(r, "Amount", default=0) or 0)
            out.append(
                LedgerLine(
                    date=str(_g(r, "PostingDate", "TransactionDate", "Date", default=""))[:10],
                    description=_g(r, "Description", "Memo", default=""),
                    charge=amt if amt > 0 else 0.0,
                    payment=-amt if amt < 0 else 0.0,
                    balance=float(_g(r, "Balance", "RunningBalance", default=0) or 0),
                )
            )
        return out

    def get_statements(self, unit_account_id):
        return [
            Document(
                id=str(_g(s, "StatementID", "Id", default="")),
                title=_g(s, "Name", "Title", default="Statement"),
                category="statement",
                date=str(_g(s, "StatementDate", "Date", default=""))[:10],
                url=_g(s, "Link", "Url", default="#"),
            )
            for s in _list(self.c.unit_account_statements(unit_account_id))
        ]

    def get_financial_snapshot(self, community_id):
        # Caliber exposes GL balances through chart of accounts; rolls up here.
        coa = _list(self.c.client_chart_of_accounts(community_id))
        cash = sum(float(_g(a, "Balance", default=0) or 0) for a in coa if "cash" in str(_g(a, "Name", default="")).lower() and "reserve" not in str(_g(a, "Name", default="")).lower())
        reserve = sum(float(_g(a, "Balance", default=0) or 0) for a in coa if "reserve" in str(_g(a, "Name", default="")).lower())
        delinq = _list(self.c.client_delinquencies(community_id))
        ar = sum(float(_g(d, "Balance", default=0) or 0) for d in delinq)
        pending = [i for i in _list(self.c.client_invoices(community_id)) if not _g(i, "APPosted", default=False)]
        return FinancialSnapshot(
            as_of="", operating_cash=cash, reserve_cash=reserve, ar_total=ar, ar_over_60=0.0,
            ap_pending=sum(float(_g(i, "Amount", default=0) or 0) for i in pending),
            ytd_income=0.0, ytd_expense=0.0, ytd_budget_income=0.0, ytd_budget_expense=0.0,
            recon_status="unknown", packet_ready=False, last_packet_date="",
        )

    def get_chart_of_accounts(self, community_id):
        return _list(self.c.client_chart_of_accounts(community_id))

    def list_invoices(self, community_id, status=None):
        out = []
        for i in _list(self.c.client_invoices(community_id)):
            st = "paid" if _g(i, "APPosted") else "rejected" if _g(i, "Rejected") else "approved" if _g(i, "BoardApproved") else "pending_board"
            if status and st != status:
                continue
            out.append(
                Invoice(
                    id=str(_g(i, "InvoiceID", default="")), community_id=str(community_id),
                    vendor=_g(i, "VendorName", "Vendor", default=""), number=_g(i, "InvoiceNumber", default=""),
                    amount=float(_g(i, "Amount", default=0) or 0), invoice_date=str(_g(i, "InvoiceDate", default=""))[:10],
                    due_date=str(_g(i, "DueDate", default=""))[:10], gl_account=_g(i, "ExpenseGLAccount", default=""),
                    description=_g(i, "VendorNotes", "Description", default=""), status=st,
                    approvals=int(_g(i, "ActualNumberOfApprovals", default=0) or 0),
                )
            )
        return out

    def act_on_invoice(self, invoice_id, actor_id, action, note=""):
        self.c.invoice_action(invoice_id, actor_id, action.capitalize(), note)
        d = self.c.invoice_details(invoice_id)
        return Invoice(
            id=str(invoice_id), community_id=str(_g(d, "ClientID", default="")), vendor=_g(d, "VendorName", default=""),
            number=_g(d, "InvoiceNumber", default=""), amount=float(_g(d, "Amount", default=0) or 0),
            invoice_date=str(_g(d, "InvoiceDate", default=""))[:10], due_date=str(_g(d, "DueDate", default=""))[:10],
            gl_account="", description="", status="approved" if action == "approve" else "rejected",
        )

    def list_delinquencies(self, community_id):
        return [
            Delinquency(
                unit_account_id=str(_g(d, "UnitAccountID", default="")), unit_label=_g(d, "UnitNumber", default=""),
                owner_name=_g(d, "OwnerName", "Name", default=""), balance=float(_g(d, "Balance", default=0) or 0),
                days_late=int(_g(d, "DaysLate", "Days", default=0) or 0), stage=_g(d, "Stage", "CollectionStatus", default="reminder"),
                last_action=_g(d, "LastAction", default=""), next_action=_g(d, "NextAction", default=""),
            )
            for d in _list(self.c.client_delinquencies(community_id))
        ]

    def list_service_requests(self, community_id, unit_account_id=None):
        rows = _list(self.c.unit_account_maintenance(unit_account_id, "all")) if unit_account_id else _list(self.c.client_maintenance(community_id, all_=True))
        return [
            ServiceRequest(
                id=str(_g(r, "ProblemID", default="")), community_id=str(community_id), unit_label=_g(r, "UnitNumber", "Location", default=""),
                category=_g(r, "Category", "KBItem", default=""), summary=_g(r, "Notes", "Description", default=""),
                status=_g(r, "Status", default="open"), created=str(_g(r, "DateCreated", default=""))[:10],
                assigned_vendor=_g(r, "VendorName"),
            )
            for r in rows
        ]

    def create_service_request(self, community_id, unit_account_id, category, summary):
        ua = self.c.unit_account(unit_account_id)
        unit_id = _g(ua, "UnitID", default=unit_account_id)
        res = self.c.unit_service_request(unit_id, {"RefType": "UnitAccount", "RefID": unit_account_id, "Location": "", "Notes": f"[{category}] {summary}"})
        return ServiceRequest(id=str(_g(res, "ProblemID", default="")), community_id=str(community_id), unit_label=_g(ua, "UnitNumber", default=""), category=category, summary=summary, status="open", created="")

    def list_arc_requests(self, community_id, unit_account_id=None):
        rows = _list(self.c.unit_account_architectural(unit_account_id, "all")) if unit_account_id else _list(self.c.client_architectural_items(community_id))
        return [
            ArcRequest(
                id=str(_g(r, "ArchitecturalID", default="")), community_id=str(community_id), unit_label=_g(r, "Address", default=""),
                owner_name=_g(r, "Owner", default=""), request_type=_g(r, "RequestType", default=""), submitted=str(_g(r, "StartDate", default=""))[:10],
                status=str(_g(r, "PrimaryStatus", "Status", default="submitted")).lower().replace(" ", "_"),
                approvals=int(_g(r, "ActualNumberOfApprovals", default=0) or 0), approvals_required=int(_g(r, "RequiredNumberOfApprovers", default=3) or 3),
            )
            for r in rows
        ]

    def act_on_arc(self, arc_id, actor_id, action, note=""):
        item = self.c.architectural_item(arc_id)
        self.c.architectural_board_approve({"ArcItemID": arc_id, "CContactID": actor_id, "StepID": _g(item, "ApprovalStepID"), "ApprovalType": 1 if action == "approve" else 2, "RejectionReason": note})
        return self.list_arc_requests(_g(item, "ClientID", default=""))[0] if item else None

    def list_documents(self, community_id, board=False):
        return [
            Document(id=str(_g(d, "DocumentID", default="")), title=_g(d, "DocTitle", default="Document"), category=_g(d, "DocType", default="general"),
                     date=str(_g(d, "UploadDate", default=""))[:10], url=_g(d, "DocPath", default="#"), board_only=not _g(d, "DisplayOnWeb", default=True))
            for d in _list(self.c.client_documents(community_id))
            if board or _g(d, "DisplayOnWeb", default=True)
        ]

    def list_vendors(self, community_id):
        return [
            Vendor(id=str(_g(v, "VendorID", default="")), name=_g(v, "CompanyName", default=""), category=_g(v, "VendorType", default=""),
                   phone=_g(v, "Phone", default=""), email=_g(v, "Email", default=""), coi_expires="", w9_on_file=bool(_g(v, "EIN")), ytd_paid=0.0)
            for v in _list(self.c.client_vendors(community_id))
        ]

    def list_violations(self, community_id):
        return [
            Violation(id=str(_g(v, "ViolationID", default="")), unit_label=_g(v, "UnitNumber", default=""), category=_g(v, "Category", default=""),
                      opened=str(_g(v, "ViolationDate", default=""))[:10], stage=_g(v, "Stage", default=""), status=_g(v, "Status", default="open"))
            for v in _list(self.c.client_violations(community_id, "open"))
        ]

    def post_payment(self, unit_account_id, amount, method):
        # Real card/ACH payments go through the configured payment provider
        # (GET /api/v2/paymentproviders) which returns a hosted redirect URL.
        providers = self.c.payment_providers()
        return {"redirect": _g(providers, "RedirectUrl", default=None), "amount": amount, "method": method}
