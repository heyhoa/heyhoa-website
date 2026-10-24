"""Provider-agnostic accounting interface.

Every portal page talks to this interface, never to a vendor SDK directly, so
we can start on FrontSteps/Caliber and add Vantaca, AppFolio, Buildium or our
own ledger later without touching the UI.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Community:
    id: str
    name: str
    kind: str
    units: int
    city: str
    state: str
    fiscal_year_end: str = "12/31"
    dues_frequency: str = "monthly"
    logo_url: str | None = None


@dataclass
class UnitAccount:
    id: str
    community_id: str
    unit_label: str
    address: str
    owner_name: str
    email: str
    phone: str
    balance: float
    autopay: bool
    next_due_date: str
    next_due_amount: float
    status: str = "current"  # current | late | collections


@dataclass
class LedgerLine:
    date: str
    description: str
    charge: float = 0.0
    payment: float = 0.0
    balance: float = 0.0


@dataclass
class Invoice:
    id: str
    community_id: str
    vendor: str
    number: str
    amount: float
    invoice_date: str
    due_date: str
    gl_account: str
    description: str
    status: str  # pending_board | approved | paid | rejected
    ai_note: str | None = None
    approvals: int = 0
    approvals_required: int = 2


@dataclass
class Delinquency:
    unit_account_id: str
    unit_label: str
    owner_name: str
    balance: float
    days_late: int
    stage: str  # reminder | late_notice | demand | lien_warning | attorney
    last_action: str
    next_action: str


@dataclass
class ServiceRequest:
    id: str
    community_id: str
    unit_label: str
    category: str
    summary: str
    status: str
    created: str
    assigned_vendor: str | None = None


@dataclass
class ArcRequest:
    id: str
    community_id: str
    unit_label: str
    owner_name: str
    request_type: str
    submitted: str
    status: str  # submitted | under_review | approved | denied | more_info
    approvals: int = 0
    approvals_required: int = 3
    notes: str = ""


@dataclass
class Document:
    id: str
    title: str
    category: str
    date: str
    url: str = "#"
    board_only: bool = False


@dataclass
class Vendor:
    id: str
    name: str
    category: str
    phone: str
    email: str
    coi_expires: str
    w9_on_file: bool
    ytd_paid: float


@dataclass
class Violation:
    id: str
    unit_label: str
    category: str
    opened: str
    stage: str
    status: str


@dataclass
class FinancialSnapshot:
    as_of: str
    operating_cash: float
    reserve_cash: float
    ar_total: float
    ar_over_60: float
    ap_pending: float
    ytd_income: float
    ytd_expense: float
    ytd_budget_income: float
    ytd_budget_expense: float
    recon_status: str
    packet_ready: bool
    last_packet_date: str
    income_lines: list = field(default_factory=list)   # (name, actual, budget)
    expense_lines: list = field(default_factory=list)
    monthly_cash: list = field(default_factory=list)   # (month, operating, reserve)


class AccountingProvider(ABC):
    name = "base"

    @abstractmethod
    def list_communities(self) -> list[Community]: ...

    @abstractmethod
    def get_community(self, community_id: str) -> Community: ...

    @abstractmethod
    def list_unit_accounts(self, community_id: str) -> list[UnitAccount]: ...

    @abstractmethod
    def get_unit_account(self, unit_account_id: str) -> UnitAccount: ...

    @abstractmethod
    def get_ledger(self, unit_account_id: str, since: str | None = None) -> list[LedgerLine]: ...

    @abstractmethod
    def get_statements(self, unit_account_id: str) -> list[Document]: ...

    @abstractmethod
    def get_financial_snapshot(self, community_id: str) -> FinancialSnapshot: ...

    @abstractmethod
    def get_chart_of_accounts(self, community_id: str) -> list[dict]: ...

    @abstractmethod
    def list_invoices(self, community_id: str, status: str | None = None) -> list[Invoice]: ...

    @abstractmethod
    def act_on_invoice(self, invoice_id: str, actor_id: str, action: str, note: str = "") -> Invoice: ...

    @abstractmethod
    def list_delinquencies(self, community_id: str) -> list[Delinquency]: ...

    @abstractmethod
    def list_service_requests(self, community_id: str, unit_account_id: str | None = None) -> list[ServiceRequest]: ...

    @abstractmethod
    def create_service_request(self, community_id: str, unit_account_id: str, category: str, summary: str) -> ServiceRequest: ...

    @abstractmethod
    def list_arc_requests(self, community_id: str, unit_account_id: str | None = None) -> list[ArcRequest]: ...

    @abstractmethod
    def act_on_arc(self, arc_id: str, actor_id: str, action: str, note: str = "") -> ArcRequest: ...

    @abstractmethod
    def list_documents(self, community_id: str, board: bool = False) -> list[Document]: ...

    @abstractmethod
    def list_vendors(self, community_id: str) -> list[Vendor]: ...

    @abstractmethod
    def list_violations(self, community_id: str) -> list[Violation]: ...

    @abstractmethod
    def post_payment(self, unit_account_id: str, amount: float, method: str) -> dict: ...
