"""Period financials derived from COA snapshots (Caliber exposes no GL-by-period)."""
import datetime as dt
from decimal import Decimal

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import BudgetLine, CoaSnapshot
from app.services import financials


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.test_request_context():
        yield app


def test_snapshot_from_mock_provider(app):
    n = financials.snapshot_coa("1001", dt.date(2026, 10, 1))
    assert n == 15
    assert financials.snapshot_coa("1001", dt.date(2026, 10, 1)) == 15  # idempotent per day
    assert CoaSnapshot.query.filter_by(community_id="1001").count() == 15


def test_period_activity_is_delta_of_fy_balance(app):
    financials.snapshot_coa("1001", dt.date(2026, 9, 1))
    # simulate October activity: landscaping +1,850 by the Oct 31 snapshot
    for row in CoaSnapshot.query.filter_by(as_of=dt.date(2026, 9, 1)).all():
        db.session.add(CoaSnapshot(community_id="1001", as_of=dt.date(2026, 9, 30), account_number=row.account_number, name=row.name, type=row.type, fund=row.fund,
                                   balance=row.balance, fy_balance=(row.fy_balance or 0) + (Decimal("1850") if row.account_number == "6210" else 0)))
    db.session.commit()
    act = {r["account_number"]: r["activity"] for r in financials.period_activity("1001", dt.date(2026, 9, 1), dt.date(2026, 9, 30))}
    assert act["6210"] == Decimal("1850") and act["4010"] == 0
    assert "1010" not in act  # balance sheet accounts excluded


def test_budget_vs_actual_and_balance_sheet(app):
    financials.snapshot_coa("1001", dt.date(2026, 9, 30))
    db.session.add(BudgetLine(community_id="1001", fiscal_year=2026, account_number="6210", name="Landscaping", type="Expense", annual_amount=Decimal("24000")))
    db.session.commit()
    bva = financials.budget_vs_actual("1001", 2026, dt.date(2026, 9, 30))
    assert len(bva) == 1 and bva[0]["ytd_budget"] == Decimal("18000") and bva[0]["actual"] == Decimal("18500.00") and bva[0]["variance"] == Decimal("500.00")
    bs = financials.balance_sheet("1001", dt.date(2026, 9, 30))
    assert bs["totals"]["Asset"] > 0 and len(bs["Asset"]) == 3
