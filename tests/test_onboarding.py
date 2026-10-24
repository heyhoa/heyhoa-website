"""Self-serve signup, e-sign, intake, roster, rules, bank steps, go-live; board rules change quorums."""
import io

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import ApprovalRule, CommunityProfile, Lead, OnboardingUnit, WorkItem
from app.services import decisions, onboarding


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


SIGNUP = {"community_name": "Baraca Estates", "kind": "hoa", "structure": "standalone", "units": "16", "city": "Mesa", "state": "az", "dues_frequency": "monthly", "prior_setup": "self", "plan": "back-office",
          "contact_name": "Alex Hoyt", "contact_role": "Treasurer", "email": "alex@baraca.example", "phone": "480-555-0100"}

ROSTER = b"Unit,Address,Owner,Email,Phone,Balance\n1,100 Baraca Ln,Pat Lee,pat@example.com,480-555-0001,0\n2,102 Baraca Ln,Sam Ruiz,,480-555-0002,\"1,240.00\"\n3,104 Baraca Ln,Kim Park,kim@example.com,,\n"


def _signup(client):
    r = client.post("/start", data=SIGNUP)
    assert r.status_code == 302 and "/agreement" in r.headers["Location"]
    token = r.headers["Location"].split("/start/")[1].split("/agreement")[0]
    return token


def test_signup_sign_and_onboard(client):
    token = _signup(client)
    prof = CommunityProfile.query.first()
    assert prof.status == "signup" and prof.monthly_price == 349 and prof.unit_kind == "lots" and prof.state == "AZ"
    assert Lead.query.first().status == "accepted"
    # onboarding page redirects to the agreement until signed
    assert "/agreement" in client.get(f"/start/{token}").headers["Location"]
    r = client.post(f"/start/{token}/agreement", data={"signed_by": "Alex Hoyt", "title": "Treasurer", "agree": "on"})
    assert r.status_code == 302
    prof = db.session.get(CommunityProfile, prof.id)
    assert prof.status == "signed" and prof.agreement["signed_by"] == "Alex Hoyt" and len(prof.agreement["sha256"]) == 64 and prof.agreement["monthly_price"] == 349
    assert Lead.query.first().status == "won"
    assert WorkItem.query.filter_by(kind="signup", lane="onboarding").first()
    assert ApprovalRule.query.filter_by(community_id=prof.community_id, decision_type="transfer").first().approvals == 3
    # intake
    r = client.post(f"/start/{token}", data={"intent": "intake", "legal_name": "Baraca Estates Homeowners Association, Inc.", "incorporation_state": "az", "ein_last4": "4411", "address1": "100 Baraca Ln", "city": "Mesa", "state": "AZ", "zip": "85201", "county": "Maricopa",
                                             "fiscal_year_end": "12/31", "dues_amount": "175", "kind": "hoa", "structure": "sub", "master_name": "Las Sendas Master", "b0_name": "Alex Hoyt", "b0_title": "Treasurer", "b0_signer": "on", "b1_name": "Jo Chen", "b1_title": "President", "b1_signer": "on"})
    prof = db.session.get(CommunityProfile, prof.id)
    assert prof.checklist["intake"] and prof.structure == "sub" and prof.master_name == "Las Sendas Master" and len(prof.board) == 2 and prof.status == "onboarding"
    # roster
    client.post(f"/start/{token}", data={"intent": "roster", "roster": (io.BytesIO(ROSTER), "roster.csv")}, content_type="multipart/form-data")
    units = OnboardingUnit.query.filter_by(profile_id=prof.id).all()
    assert len(units) == 3 and float(next(u for u in units if u.unit_label == "2").balance) == 1240.0
    # rules
    client.post(f"/start/{token}", data={"intent": "rules", "rule_invoice": "2", "rule_transfer": "4", "rule_vendor_add": "1"})
    assert decisions.spec("transfer", prof.community_id)["approvals"] == 4 and decisions.spec("vendor_add", prof.community_id)["approvals"] == 1
    assert decisions.spec("transfer")["approvals"] == 2  # defaults untouched elsewhere
    # bank: one assessment cycle with the floor
    assert onboarding.startup_amount(prof) == 2800.0  # 16 lots × $175
    client.post(f"/start/{token}", data={"intent": "bank", "step": "startup_check_mailed"})
    prof = db.session.get(CommunityProfile, prof.id)
    assert prof.bank["startup_check_mailed"] and prof.bank["startup_amount"] == 2800.0 and not prof.checklist["bank"]
    r = client.get(f"/start/{token}")
    assert r.status_code == 200 and b"mailed, awaiting" in r.data and b"$2,800" in r.data
    # ops confirms and goes live; rules follow the Caliber id
    client.post("/login/ops")
    client.post("/ops/onboarding", data={"id": prof.id, "intent": "accounts_opened"})
    client.post("/ops/onboarding", data={"id": prof.id, "intent": "startup_check_received"})
    assert db.session.get(CommunityProfile, prof.id).checklist["bank"]
    client.post("/ops/onboarding", data={"id": prof.id, "intent": "go_live", "provider_client_id": "2045"})
    prof = db.session.get(CommunityProfile, prof.id)
    assert prof.status == "live" and prof.community_id == "2045" and decisions.spec("transfer", "2045")["approvals"] == 4
    assert client.get("/ops/onboarding").status_code == 200


def test_signature_requires_name_and_checkbox(client):
    token = _signup(client)
    client.post(f"/start/{token}/agreement", data={"signed_by": "", "agree": "on"})
    assert CommunityProfile.query.first().agreement is None
    client.post(f"/start/{token}/agreement", data={"signed_by": "Alex Hoyt"})
    assert CommunityProfile.query.first().agreement is None


def test_board_settings_rules_change_quorum(client):
    client.post("/login/board")
    client.post("/board/settings", data={"rule_transfer": "3", "rule_invoice": "2"})
    assert decisions.spec("transfer", "1001")["approvals"] == 3
    client.post("/board/decisions/new", data={"decision_type": "transfer", "title": "Move $5,000 to reserves", "amount": "5000", "body": "catch-up"})
    d = WorkItem.query.filter_by(kind="decision").first()
    client.post(f"/board/decisions/{d.id}/vote", data={"vote": "approve"})
    assert db.session.get(WorkItem, d.id).state == "proposed"  # 1 of 3 now, not 1 of 2
    r = client.get("/board/decisions")
    assert b"/3 approvals" in r.data


def test_terms_and_agreement_pages(client):
    r = client.get("/terms")
    assert r.status_code == 200 and b"Buy cyber insurance" in r.data and b"never initiates a transfer" in r.data and b"the association's actions" in r.data
    r = client.get("/agreement")
    assert r.status_code == 200 and b"PROFESSIONAL SERVICES AGREEMENT" in r.data
    assert client.get("/start").status_code == 200
