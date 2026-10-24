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


class WorkItem(db.Model):
    """The unit of work for hey ops. Every inbound (email, text, call, portal
    form, scheduled job, Caliber signal) becomes one. An agent lane owns it,
    proposes an action, and a person approves it unless policy lets the agent
    execute on its own."""

    __tablename__ = "work_items"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc), onupdate=lambda: dt.datetime.now(dt.timezone.utc))
    community_id = db.Column(db.String(40), index=True)
    unit_account_id = db.Column(db.String(40), index=True)
    counterpart_email = db.Column(db.String(200))
    counterpart_name = db.Column(db.String(160))
    kind = db.Column(db.String(30), index=True)  # email|sms|call|portal_form|delinquency|invoice|close|onboarding|decision|other
    lane = db.Column(db.String(20), index=True)  # cs|ar|ap|board|close|onboarding
    state = db.Column(db.String(20), index=True, default="new")  # new|working|proposed|approved|rejected|done|escalated|failed
    priority = db.Column(db.String(10), default="normal")  # low|normal|high|urgent
    sla_due = db.Column(db.DateTime)
    subject = db.Column(db.String(300))
    summary = db.Column(db.Text)
    category = db.Column(db.String(40))
    evidence = db.Column(db.JSON)  # [{"label":..., "ref":..., "text":...}]
    proposal = db.Column(db.JSON)  # {"action","payload","preview","confidence","sources","reason","needs_review"}
    needs_review = db.Column(db.Boolean, default=True)
    reviewer = db.Column(db.String(120))
    reviewed_at = db.Column(db.DateTime)
    review_note = db.Column(db.Text)
    outcome = db.Column(db.Text)
    remote_ids = db.Column(db.JSON)  # ids in Caliber / Postmark / Twilio
    shadow = db.Column(db.Boolean, default=True)

    messages = db.relationship("Message", backref="work_item", order_by="Message.created_at", cascade="all, delete-orphan")
    runs = db.relationship("AgentRun", backref="work_item", order_by="AgentRun.created_at", cascade="all, delete-orphan")

    @property
    def is_open(self):
        return self.state in ("new", "working", "proposed", "approved", "escalated")


class Message(db.Model):
    """A message in a work item's thread, any channel, any direction."""

    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    work_item_id = db.Column(db.Integer, db.ForeignKey("work_items.id"), index=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    direction = db.Column(db.String(5))  # in|out
    channel = db.Column(db.String(10))  # email|sms|voice|portal|note
    sender = db.Column(db.String(200))
    recipient = db.Column(db.String(200))
    subject = db.Column(db.String(300))
    body = db.Column(db.Text)
    author = db.Column(db.String(30))  # owner|vendor|hey|coordinator|accountant|board|system
    meta = db.Column(db.JSON)
    delivered = db.Column(db.Boolean, default=False)


class AgentRun(db.Model):
    """One step of an agent working an item: what it saw, what it did."""

    __tablename__ = "agent_runs"
    id = db.Column(db.Integer, primary_key=True)
    work_item_id = db.Column(db.Integer, db.ForeignKey("work_items.id"), index=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    lane = db.Column(db.String(20))
    mode = db.Column(db.String(10))  # demo|live
    step = db.Column(db.Integer, default=0)
    tool = db.Column(db.String(60))
    input = db.Column(db.Text)
    output = db.Column(db.Text)
    tokens_in = db.Column(db.Integer, default=0)
    tokens_out = db.Column(db.Integer, default=0)
    ms = db.Column(db.Integer, default=0)


class StoredDocument(db.Model):
    """The board's system of record for files: governing docs, contracts,
    warranties, insurance, reserve studies, meeting records, vendor files."""

    __tablename__ = "stored_documents"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    community_id = db.Column(db.String(40), index=True)
    title = db.Column(db.String(300))
    category = db.Column(db.String(40), index=True)  # governing|rules|policy|contract|warranty|insurance|reserve_study|meetings|financial|vendor|arc|other
    visibility = db.Column(db.String(20), default="board")  # board | owners
    filename = db.Column(db.String(300))
    path = db.Column(db.String(500))
    size = db.Column(db.Integer)
    uploaded_by = db.Column(db.String(120))
    vendor = db.Column(db.String(200))
    effective_on = db.Column(db.Date)
    expires_on = db.Column(db.Date, index=True)
    notes = db.Column(db.Text)

    @property
    def days_to_expiry(self):
        return (self.expires_on - dt.date.today()).days if self.expires_on else None


class ReserveComponent(db.Model):
    """A line in the digital reserve plan, built from the reserve study."""

    __tablename__ = "reserve_components"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    name = db.Column(db.String(200))
    category = db.Column(db.String(60))  # roofing|paving|pool|fencing|lighting|painting|mechanical|landscape|other
    quantity = db.Column(db.String(60))
    useful_life = db.Column(db.Integer)
    remaining_life = db.Column(db.Integer)
    replacement_cost = db.Column(db.Numeric(14, 2))
    next_year = db.Column(db.Integer)
    notes = db.Column(db.Text)
    source = db.Column(db.String(200))  # study title / page

    @property
    def accrued(self):
        """Straight-line share of the cost that should be funded by now."""
        if not self.useful_life or self.replacement_cost is None:
            return 0
        used = max(0, min(self.useful_life, self.useful_life - (self.remaining_life or 0)))
        return float(self.replacement_cost) * used / self.useful_life

    @property
    def annual_contribution(self):
        if not self.remaining_life or self.replacement_cost is None:
            return float(self.replacement_cost or 0)
        return float(self.replacement_cost) / max(self.remaining_life, 1)


class InvoiceFlag(db.Model):
    """Board-set flags on provider invoices, e.g. hide from owners (legal bills)."""

    __tablename__ = "invoice_flags"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    invoice_id = db.Column(db.String(60), index=True)
    confidential = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(200))
    set_by = db.Column(db.String(120))
    __table_args__ = (db.UniqueConstraint("community_id", "invoice_id", name="uq_invoice_flag"),)


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    actor = db.Column(db.String(120))
    action = db.Column(db.String(80))
    target = db.Column(db.String(120))
    detail = db.Column(db.Text)
