from ..extensions import db
from ..models import Announcement, Lead


def seed_demo():
    if not Lead.query.first():
        db.session.add(
            Lead(
                community_name="Willow Creek Townhomes",
                community_type="townhome",
                units=48,
                state="AZ",
                city="Mesa",
                current_setup="self",
                pain_points="late financials,volunteer burnout",
                contact_name="Dana Whitfield",
                contact_role="treasurer",
                email="treasurer@willowcreek.example",
                score=85,
                status="won",
            )
        )
    if not Announcement.query.first():
        db.session.add(
            Announcement(
                community_id="1001",
                title="Pool opens May 1",
                body="Gate codes reset on April 30. New codes go out by text and email the morning of the 30th.",
                channel="email",
                author="Board of Directors",
            )
        )
    db.session.commit()
    from . import plans

    plans.seed_demo("1001")
    from . import insurance

    insurance.seed_demo("1001")
