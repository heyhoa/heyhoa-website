import datetime as dt

from .extensions import db


class Lead(db.Model):
    """Quote requests from the marketing site."""

    __tablename__ = "leads"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    community_name = db.Column(db.String(200))
    community_type = db.Column(db.String(50))  # hoa | condo | townhome | mixed
    units = db.Column(db.Integer)
    state = db.Column(db.String(2))
    city = db.Column(db.String(100))
    current_setup = db.Column(db.String(50))  # self | management_co | accountant | none
    pain_points = db.Column(db.Text)  # comma separated
    accounting_system = db.Column(db.String(100))
    fiscal_year_end = db.Column(db.String(20))
    contact_name = db.Column(db.String(120))
    contact_role = db.Column(db.String(60))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(40))
    notes = db.Column(db.Text)
    source = db.Column(db.String(80))  # utm_source or referrer
    plan = db.Column(db.String(30))  # books | back-office | board-plus
    utm_source = db.Column(db.String(80))
    utm_medium = db.Column(db.String(80))
    utm_campaign = db.Column(db.String(120))
    referrer = db.Column(db.String(300))
    score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="new")  # new|contacted|proposal|won|lost

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    name = db.Column(db.String(120))
    email = db.Column(db.String(200))
    topic = db.Column(db.String(80))
    message = db.Column(db.Text)


class PortalRequest(db.Model):
    """Maintenance, ARC and general requests captured in the portals.

    In mock mode these persist locally. With FrontSteps configured the
    provider mirrors them into Caliber and stores the remote id here.
    """

    __tablename__ = "portal_requests"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    community_id = db.Column(db.String(40))
    unit_account_id = db.Column(db.String(40))
    kind = db.Column(db.String(30))  # maintenance | arc | question | statement
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    status = db.Column(db.String(30), default="open")
    remote_id = db.Column(db.String(60))
    ai_category = db.Column(db.String(80))
    ai_summary = db.Column(db.Text)


class Announcement(db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    community_id = db.Column(db.String(40))
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    channel = db.Column(db.String(30), default="email")  # email|sms|portal
    author = db.Column(db.String(120))


class CoaSnapshot(db.Model):
    """Nightly copy of Caliber's chart of accounts. Monthly activity = delta of
    fy_balance between two snapshots (Caliber exposes no GL-by-period endpoint)."""

    __tablename__ = "coa_snapshots"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    as_of = db.Column(db.Date, index=True)
    account_number = db.Column(db.String(20))
    name = db.Column(db.String(200))
    type = db.Column(db.String(30))  # Asset | Liability | Equity | Income | Expense
    fund = db.Column(db.String(30))  # operating | reserve | other
    balance = db.Column(db.Numeric(14, 2))
    fy_balance = db.Column(db.Numeric(14, 2))
    __table_args__ = (db.UniqueConstraint("community_id", "as_of", "account_number", name="uq_coa_snapshot"),)


class BudgetLine(db.Model):
    """Budgets do not exist in Caliber's API; we are the system of record."""

    __tablename__ = "budget_lines"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    fiscal_year = db.Column(db.Integer, index=True)
    account_number = db.Column(db.String(20))
    name = db.Column(db.String(200))
    type = db.Column(db.String(30))
    annual_amount = db.Column(db.Numeric(14, 2))
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(120))
    __table_args__ = (db.UniqueConstraint("community_id", "fiscal_year", "account_number", name="uq_budget_line"),)


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    actor = db.Column(db.String(120))
    action = db.Column(db.String(80))
    target = db.Column(db.String(120))
    detail = db.Column(db.Text)
