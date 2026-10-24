"""Derive period financials from chart-of-accounts snapshots plus our budget.

Strict cash basis: income when received, expense when paid. The balance
sheet is bank balances and fund balances; receivables and payables are memo
schedules (delinquencies, unpaid bills) and never balance-sheet lines.

Caliber's API returns a lifetime Balance and a fiscal-year FYBalance per
account but no activity by period, so:
  month activity = FYBalance(end) - FYBalance(start)      (same fiscal year)
  balance sheet  = Balance at the snapshot date
  budget vs actual = FY-to-date FYBalance vs BudgetLine.annual_amount * elapsed share
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from ..extensions import db
from ..integrations.registry import get_provider
from ..models import BudgetLine, CoaSnapshot


def _fund_for(name: str, type_: str) -> str:
    n = (name or "").lower()
    if "reserve" in n:
        return "reserve"
    return "operating"


def snapshot_coa(community_id: str, as_of: dt.date | None = None) -> int:
    """Copy today's chart of accounts into coa_snapshots. Idempotent per day."""
    as_of = as_of or dt.date.today()
    rows = get_provider().get_chart_of_accounts(community_id)
    n = 0
    for a in rows:
        number = str(a.get("number") or a.get("AccountNumber") or a.get("GLAccountNumber") or a.get("GLAccountID") or "")
        name = a.get("name") or a.get("Name") or a.get("Description") or ""
        type_ = a.get("type") or a.get("AccountType") or a.get("Type") or ""
        bal = Decimal(str(a.get("balance") if a.get("balance") is not None else a.get("Balance") or 0))
        fy = Decimal(str(a.get("fy_balance") if a.get("fy_balance") is not None else a.get("FYBalance") if a.get("FYBalance") is not None else bal))
        existing = CoaSnapshot.query.filter_by(community_id=str(community_id), as_of=as_of, account_number=number).first()
        if existing:
            existing.balance, existing.fy_balance, existing.name, existing.type = bal, fy, name, type_
        else:
            db.session.add(CoaSnapshot(community_id=str(community_id), as_of=as_of, account_number=number, name=name, type=type_, fund=_fund_for(name, type_), balance=bal, fy_balance=fy))
        n += 1
    db.session.commit()
    return n


def _snapshot(community_id: str, as_of: dt.date) -> dict[str, CoaSnapshot]:
    """Latest snapshot on or before as_of, keyed by account number."""
    latest = db.session.query(db.func.max(CoaSnapshot.as_of)).filter(CoaSnapshot.community_id == str(community_id), CoaSnapshot.as_of <= as_of).scalar()
    if not latest:
        return {}
    return {r.account_number: r for r in CoaSnapshot.query.filter_by(community_id=str(community_id), as_of=latest).all()}


def period_activity(community_id: str, start: dt.date, end: dt.date) -> list[dict]:
    """Income/expense activity between two snapshot dates (same fiscal year)."""
    a, b = _snapshot(community_id, start), _snapshot(community_id, end)
    out = []
    for num, row in b.items():
        if row.type not in ("Income", "Expense"):
            continue
        before = a.get(num)
        activity = (row.fy_balance or 0) - ((before.fy_balance or 0) if before else 0)
        out.append({"account_number": num, "name": row.name, "type": row.type, "fund": row.fund, "activity": activity})
    return out


def budget_vs_actual(community_id: str, fiscal_year: int, as_of: dt.date, fy_start_month: int = 1) -> list[dict]:
    snap = _snapshot(community_id, as_of)
    months_elapsed = ((as_of.year - fiscal_year) * 12 + as_of.month - fy_start_month + 1) if snap else 0
    share = Decimal(max(min(months_elapsed, 12), 0)) / Decimal(12)
    out = []
    for bl in BudgetLine.query.filter_by(community_id=str(community_id), fiscal_year=fiscal_year).all():
        actual = (snap.get(bl.account_number).fy_balance if snap.get(bl.account_number) else Decimal(0)) or Decimal(0)
        ytd_budget = (bl.annual_amount or 0) * share
        out.append({"account_number": bl.account_number, "name": bl.name, "type": bl.type, "actual": actual, "ytd_budget": ytd_budget, "annual_budget": bl.annual_amount, "variance": actual - ytd_budget})
    return out


def balance_sheet(community_id: str, as_of: dt.date) -> dict:
    snap = _snapshot(community_id, as_of)
    groups: dict[str, list] = {"Asset": [], "Liability": [], "Equity": []}
    for r in snap.values():
        if r.type in groups:
            groups[r.type].append(r)
    return {k: v for k, v in groups.items()} | {"totals": {k: sum((r.balance or 0) for r in v) for k, v in groups.items()}}
