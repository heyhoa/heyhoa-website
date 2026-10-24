"""Projects, reserve plan and who-fixes-what: the three sheets."""
import datetime as dt

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Project, ResponsibilityItem, WorkItem
from app.services import plans


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as c:
        yield c


def test_reserve_grid_math_is_the_spreadsheet(client):
    with client.application.app_context():
        y = dt.date.today().year
        db.session.add(Project(community_id="1001", name="Gate system", cost_high=32000, year=y + 2, fund="reserve", status="planned"))
        db.session.add(Project(community_id="1001", name="Painting", cost_high=5000, year=y, fund="reserve", status="planned"))
        db.session.add(Project(community_id="1001", name="Done thing", cost_high=99999, year=y, fund="reserve", status="completed"))
        db.session.commit()
        plans.set_funding("1001", y + 1, 2500, 18950, "")
        g = plans.reserve_grid("1001", 9260.0, years=3, this_year=y)
        m = g["money"]
        assert [x["spend"] for x in m] == [5000, 0, 32000]  # completed projects are not spend
        assert m[0]["end"] == 4260 and m[1]["starting"] == 4260 and m[1]["available"] == 4260 + 2500 + 18950
        assert m[2]["end"] == m[1]["end"] - 32000 and m[2]["end"] < 0


def test_board_adds_project_and_sees_it_on_reserve_plan(client):
    client.post("/login/board")
    client.post("/board/projects", data={"name": "Asphalt seal and stripe", "priority": "1", "cost_low": "16,500", "cost_high": "18,500", "year": str(dt.date.today().year + 1), "status": "planned", "fund": "reserve", "description": "Crack fill, seal coat, restripe"})
    p = Project.query.filter_by(name="Asphalt seal and stripe").first()
    assert p and float(p.cost_low) == 16500 and p.cost == 18500
    r = client.get("/board/reserves")
    assert b"Asphalt seal and stripe" in r.data and b"Year end balance" in r.data and b"$18,500" in r.data
    client.post(f"/board/projects/{p.id}/status", data={"status": "completed"})
    assert db.session.get(Project, p.id).status == "completed"
    assert client.get("/board/projects").status_code == 200


def test_who_fixes_what_board_edits_owner_reads_agent_cites(client):
    client.post("/login/board")
    client.post("/board/who-fixes-what", data={"item": "Atrium wrought iron gate", "party": "owner", "note": "2012 resolution"})
    client.post("/board/who-fixes-what", data={"item": "Atrium wooden beams", "party": "association", "note": ""})
    assert ResponsibilityItem.query.count() == 2
    client.get("/logout")
    client.post("/login/homeowner")
    r = client.get("/me/community")
    assert r.status_code == 200 and b"Atrium wrought iron gate" in r.data and b"2012 resolution" in r.data
    assert b"delinquen" not in r.data.lower()
    with client.application.test_request_context():
        hits = plans.who_fixes("1001", "who fixes my iron gate?")
        assert [h.item for h in hits] == ["Atrium wrought iron gate"]
        from app.agents.tools import TOOLS
        out = TOOLS["who_fixes_what"].fn(WorkItem(community_id="1001"), query="gate")
    assert out["items"][0]["who"] == "owner" and out["items"][0]["note"] == "2012 resolution"


def test_demo_seed_and_public_json(client):
    with client.application.test_request_context():
        n = plans.seed_demo("1001")
        assert n["projects"] >= 8 and n["responsibilities"] >= 15
        from app.services.public_data import community_public
        pub = community_public("willow-creek")
        assert pub and any(r["item"].startswith("Roof") for r in pub["who_fixes_what"])
        assert all(p["status"] != "completed" for p in pub["projects"])
