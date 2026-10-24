"""The monthly package has the founders' sections, in order; owners get the first four."""
import re

import pytest

from app import create_app
from app.config import TestConfig
from app.services.packet import BOARD_SECTIONS, HOMEOWNER_SECTIONS


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


def test_sections_definition():
    assert [k for k, _ in BOARD_SECTIONS] == ["cover", "update", "budget", "balance", "aged", "collections", "prepaid", "register", "recon", "statements"]
    assert HOMEOWNER_SECTIONS == BOARD_SECTIONS[:4]


def test_board_package_has_all_ten_in_order(client):
    html = client.get("/sample-packet").data.decode()
    heads = re.findall(r"<h2>([^<]+)", html)
    for needle in ["Monthly update and change summary", "Budget comparison / P&L", "Balance sheet", "Aged owner balance report", "Collection report", "Prepaid report", "Check register / AP distributions", "Bank reconciliation(s)", "Bank statement(s)"]:
        assert any(h.strip().startswith(needle) for h in heads), needle
    idx = [next(i for i, h in enumerate(heads) if h.strip().startswith(n)) for n in ["Monthly update", "Budget comparison", "Balance sheet", "Aged owner", "Collection report", "Prepaid report", "Check register", "Bank reconciliation", "Bank statement"]]
    assert idx == sorted(idx)
    assert "ACH-0912" in html and "Client Connect" in html and "Prepaid" in html and "Unit 7" in html


def test_homeowner_package_is_first_four_only(client):
    html = client.get("/sample-packet?audience=homeowner").data.decode()
    assert "Budget comparison" in html and "Balance sheet" in html
    for forbidden in ["Aged owner balance report", "Collection report", "Prepaid report", "Check register", "Okafor", "Unit 3"]:
        assert forbidden not in html, forbidden
