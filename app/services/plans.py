"""Projects, the reserve plan and who-fixes-what.

The bar is a treasurer's spreadsheet: a list of projects with a cost and a sentence, the same
projects by year with the money under them, and a chart of who fixes what. Nothing cleverer.
"""
from __future__ import annotations

import datetime as dt

from ..extensions import db
from ..models import Project, ReserveFunding, ResponsibilityItem

STATUSES = [("planned", "Planned"), ("in_progress", "In progress"), ("under_review", "Under review"), ("scoping", "Scoping"), ("completed", "Completed")]
FUNDS = [("reserve", "Reserves"), ("operating", "Operating"), ("special", "Special assessment")]
PARTIES = [("owner", "Homeowner"), ("association", "Association"), ("shared", "Shared")]


def projects(community_id: str) -> list[Project]:
    rows = Project.query.filter_by(community_id=community_id).all()
    return sorted(rows, key=lambda p: (p.status == "completed", p.priority or 9, p.year or 9999, p.name or ""))


def reserve_grid(community_id: str, starting_cash: float, years: int = 5, this_year: int | None = None) -> dict:
    """The Baraca sheet: columns are years, rows are projects, then the money."""
    y0 = this_year or dt.date.today().year
    cols = list(range(y0, y0 + years))
    rows = [p for p in projects(community_id) if p.fund == "reserve" and p.status != "completed"]
    funding = {f.year: f for f in ReserveFunding.query.filter_by(community_id=community_id).all()}
    grid = [{"project": p, "cells": [p.cost if p.year == y else None for y in cols]} for p in rows if p.year in cols]
    spend = [sum(p.cost for p in rows if p.year == y) for y in cols]
    money, start = [], float(starting_cash)
    for i, y in enumerate(cols):
        f = funding.get(y)
        contrib = float(f.contribution or 0) if f else 0.0
        special = float(f.special_assessment or 0) if f else 0.0
        available = start + contrib + special
        end = available - spend[i]
        money.append({"year": y, "starting": start, "contribution": contrib, "special": special, "available": available, "spend": spend[i], "end": end, "note": (f.note if f else "")})
        start = end
    unscheduled = [p for p in rows if not p.year or p.year not in cols]
    return {"years": cols, "rows": grid, "projects": rows, "spend": spend, "money": money, "unscheduled": unscheduled, "total_cost": sum(p.cost for p in rows)}


def set_funding(community_id: str, year: int, contribution: float, special: float, note: str = "") -> ReserveFunding:
    f = ReserveFunding.query.filter_by(community_id=community_id, year=year).first() or ReserveFunding(community_id=community_id, year=year)
    f.contribution, f.special_assessment, f.note = contribution, special, note
    db.session.add(f)
    db.session.commit()
    return f


def responsibilities(community_id: str) -> list[ResponsibilityItem]:
    return ResponsibilityItem.query.filter_by(community_id=community_id).order_by(ResponsibilityItem.sort, ResponsibilityItem.id).all()


def who_fixes(community_id: str, query: str) -> list[ResponsibilityItem]:
    words = [w for w in (query or "").lower().split() if len(w) > 2]
    return [r for r in responsibilities(community_id) if any(w in (r.item or "").lower() for w in words)]


# ---- demo data for Willow Creek ---------------------------------------------

DEMO_PROJECTS = [
    # name, description, priority, status, low, high, year, fund
    ("Asphalt seal and stripe", "Crack fill, seal coat, restripe, replace two speed bumps", 1, "planned", 16500, 18500, 2027, "reserve"),
    ("Entry monument and lighting", "Rebuild the Willow Creek Dr monument, new LED uplights", 2, "planned", 12000, 14000, 2028, "reserve"),
    ("Security cameras at pool and entry", "LPR camera at the entry, two at the pool; monitoring is a monthly cost on operating", 2, "under_review", 7500, 7500, 2029, "reserve"),
    ("Pool resurface", "Plaster, tile line, coping repairs; equipment was done in 2024", 1, "planned", 42000, 46000, 2030, "reserve"),
    ("Perimeter fence", "2,400 lf of block wall cap and iron sections on the wash side", 2, "planned", 55000, 61000, 2033, "reserve"),
    ("Roofs (12 buildings)", "Full replacement, 25-year shingle; last done 2010", 1, "planned", 380000, 412000, 2035, "reserve"),
    ("Clubhouse interior refresh", "Paint, flooring, kitchen cabinets, furniture", 3, "scoping", 15000, 30000, None, "operating"),
    ("Pool equipment overhaul", "Pump, filter, heater, automation", 1, "completed", 19800, 19800, 2024, "reserve"),
    ("Tree trimming, priority 1 trees", "Per the arborist's list; saves the second crew visit", 2, "completed", 6400, 6400, 2025, "operating"),
]

DEMO_FUNDING = [(2026, 36000, 0, "$3,000/mo from dues"), (2027, 36000, 0, ""), (2028, 39000, 0, "2027 budget draft: $3,250/mo"), (2029, 39000, 0, ""), (2030, 39000, 0, "")]

DEMO_RESPONSIBILITIES = [
    ("Roof and roof drains", "association", "CC&R 7.1"), ("Exterior paint and stucco", "association", "CC&R 7.1"), ("Front door and hardware", "owner", ""), ("Windows and screens", "owner", "2019 resolution"),
    ("Garage door and opener", "owner", ""), ("Patio wall and gate", "association", "2019 resolution"), ("Patio concrete and pavers", "owner", ""), ("Patio light fixture", "owner", ""),
    ("Building exterior lights", "association", ""), ("Water and sewer lines inside the unit", "owner", "to the meter"), ("Water and sewer main lines", "association", "from the meter"), ("Termites", "association", "annual contract"),
    ("Front yard landscaping", "association", ""), ("Back yard landscaping", "owner", ""), ("Driveway", "association", ""), ("Mailbox and unit number plaque", "association", ""), ("HVAC and water heater", "owner", ""), ("Dryer vent cleaning", "owner", "annually, per the fire marshal"),
]


def seed_demo(community_id: str = "1001") -> dict:
    n = {"projects": 0, "funding": 0, "responsibilities": 0}
    for name, desc, pri, status, low, high, year, fund in DEMO_PROJECTS:
        if not Project.query.filter_by(community_id=community_id, name=name).first():
            db.session.add(Project(community_id=community_id, name=name, description=desc, priority=pri, status=status, cost_low=low, cost_high=high, year=year, fund=fund, updated_by="demo"))
            n["projects"] += 1
    for year, contrib, special, note in DEMO_FUNDING:
        if not ReserveFunding.query.filter_by(community_id=community_id, year=year).first():
            db.session.add(ReserveFunding(community_id=community_id, year=year, contribution=contrib, special_assessment=special, note=note))
            n["funding"] += 1
    for i, (item, party, note) in enumerate(DEMO_RESPONSIBILITIES):
        if not ResponsibilityItem.query.filter_by(community_id=community_id, item=item).first():
            db.session.add(ResponsibilityItem(community_id=community_id, item=item, party=party, note=note, sort=i))
            n["responsibilities"] += 1
    db.session.commit()
    return n
