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
    status = db.Column(db.String(30), default="new")  # new|contacted|replied|later|proposal|accepted|won|lost
    replied_at = db.Column(db.DateTime)  # first inbound reply; the sequence stops here
    review = db.Column(db.JSON)  # free books review: {"months","findings":[{"area","finding","impact","fix"}],"summary","delivered_at"}

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


class Project(db.Model):
    """One line on the community's project list. The reserve plan is the same list, by year, with the money under it."""

    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)  # what it is, in the board's words
    priority = db.Column(db.Integer, default=2)  # 1 now, 2 next, 3 someday
    status = db.Column(db.String(30), default="planned")  # planned|in_progress|under_review|scoping|completed
    cost_low = db.Column(db.Numeric(14, 2))
    cost_high = db.Column(db.Numeric(14, 2))
    year = db.Column(db.Integer)
    fund = db.Column(db.String(20), default="reserve")  # reserve|operating|special
    notes = db.Column(db.Text)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc), onupdate=lambda: dt.datetime.now(dt.timezone.utc))

    @property
    def cost(self) -> float:
        return float(self.cost_high or self.cost_low or 0)


class ReserveFunding(db.Model):
    """Money into reserves per year: the contribution from dues and any special assessment."""

    __tablename__ = "reserve_funding"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    year = db.Column(db.Integer)
    contribution = db.Column(db.Numeric(14, 2), default=0)
    special_assessment = db.Column(db.Numeric(14, 2), default=0)
    note = db.Column(db.String(200))
    __table_args__ = (db.UniqueConstraint("community_id", "year", name="uq_reserve_funding_year"),)


class ResponsibilityItem(db.Model):
    """Who fixes what: one row per building part, owner or association, with the resolution it came from."""

    __tablename__ = "responsibility_items"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    item = db.Column(db.String(200))
    party = db.Column(db.String(20), default="association")  # owner|association|shared
    note = db.Column(db.String(200))  # "2012 resolution", "CC&R 7.2"
    sort = db.Column(db.Integer, default=0)


class CommunityProfile(db.Model):
    """A community as hey knows it, from signup through go-live. Mirrors Caliber's client once live
    (provider_client_id); until then it is the only record. Structured like the Caliber client so the
    go-live export is a copy, not a translation."""

    __tablename__ = "community_profiles"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    provider_client_id = db.Column(db.String(40), index=True)  # Caliber ClientID once live
    slug = db.Column(db.String(80), unique=True)
    name = db.Column(db.String(200))  # display name, e.g. Willow Creek Townhomes
    legal_name = db.Column(db.String(300))  # as incorporated, e.g. Willow Creek Townhomes Association, Inc.
    kind = db.Column(db.String(30))  # hoa|condo|townhome|mixed|commercial
    structure = db.Column(db.String(20), default="standalone")  # standalone|master|sub
    master_name = db.Column(db.String(200))  # for a sub association: the master it belongs to
    units = db.Column(db.Integer)
    unit_kind = db.Column(db.String(10), default="units")  # units|lots
    address1 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip = db.Column(db.String(12))
    county = db.Column(db.String(100))
    incorporation_state = db.Column(db.String(2))
    ein_last4 = db.Column(db.String(4))  # never the full EIN here; the bank and Caliber hold it
    fiscal_year_end = db.Column(db.String(5), default="12/31")
    dues_amount = db.Column(db.Numeric(10, 2))
    dues_frequency = db.Column(db.String(20), default="monthly")  # monthly|quarterly|semiannual|annual
    plan = db.Column(db.String(30))  # books|back-office|board-plus
    monthly_price = db.Column(db.Integer)
    contact = db.Column(db.JSON)  # {"name","title","email","phone"} the board member who signed up
    board = db.Column(db.JSON)  # [{"name","title","email","phone","signer":bool}]
    prior = db.Column(db.JSON)  # {"setup": self|management_co|accountant, "manager","bank","software"}
    agreement = db.Column(db.JSON)  # {"version","sha256","signed_by","title","signed_at","ip","user_agent","plan","monthly_price"}
    bank = db.Column(db.JSON)  # {"accounts_opened","startup_amount","startup_check_mailed","startup_check_received","final_transfer_mailed","final_transfer_received","signers"}
    checklist = db.Column(db.JSON)  # {"intake": bool, "roster": bool, "documents": bool, "rules": bool, "bank": bool}
    status = db.Column(db.String(20), default="signup")  # signup|signed|onboarding|parallel|live|churned
    go_live_on = db.Column(db.Date)
    lead_id = db.Column(db.Integer)

    @property
    def community_id(self) -> str:
        """The id the rest of the app keys on: the Caliber client id once live, else a local one."""
        return self.provider_client_id or f"new-{self.id}"


class OnboardingUnit(db.Model):
    """The owner roster as imported at signup (CSV). Becomes Caliber units and contacts at go-live."""

    __tablename__ = "onboarding_units"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, index=True)
    unit_label = db.Column(db.String(60))
    address = db.Column(db.String(300))
    owner_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(40))
    mailing_address = db.Column(db.String(300))
    balance = db.Column(db.Numeric(12, 2))
    notes = db.Column(db.String(300))


class ApprovalRule(db.Model):
    """Board rules: how many approvals a decision type needs in this community."""

    __tablename__ = "approval_rules"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    decision_type = db.Column(db.String(40))
    approvals = db.Column(db.Integer, default=2)
    note = db.Column(db.String(200))
    __table_args__ = (db.UniqueConstraint("community_id", "decision_type", name="uq_approval_rule"),)


class Meeting(db.Model):
    """A board, annual, budget or special meeting: notice, agenda, minutes."""

    __tablename__ = "meetings"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    kind = db.Column(db.String(20), default="board")  # board|annual|budget|special|executive
    date = db.Column(db.Date)
    time = db.Column(db.String(20))
    where = db.Column(db.String(200))
    notice_days = db.Column(db.Integer, default=10)
    notice_sent_at = db.Column(db.DateTime)
    notice_channels = db.Column(db.String(60))  # "email,portal,mail"
    agenda = db.Column(db.JSON)  # ["Call to order", ...]
    minutes = db.Column(db.Text)
    status = db.Column(db.String(20), default="scheduled")  # scheduled|held|cancelled
    created_by = db.Column(db.String(120))


class Letter(db.Model):
    """A physical letter: queued to the mail API or printed and mailed by a person. One row per recipient."""

    __tablename__ = "letters"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))
    community_id = db.Column(db.String(40), index=True)
    kind = db.Column(db.String(40))  # meeting_notice|collection|violation|budget|general|...
    unit_account_id = db.Column(db.String(40))
    to_name = db.Column(db.String(200))
    to_address = db.Column(db.String(400))
    subject = db.Column(db.String(300))
    body = db.Column(db.Text)
    status = db.Column(db.String(20), default="queued")  # queued|sent|simulated|failed
    provider = db.Column(db.String(20))  # lob|manual
    provider_id = db.Column(db.String(80))
    cost = db.Column(db.Numeric(8, 2))
    sent_at = db.Column(db.DateTime)
    certified = db.Column(db.Boolean, default=False)
    meeting_id = db.Column(db.Integer)
    announcement_id = db.Column(db.Integer)
    requested_by = db.Column(db.String(120))


class InsurancePolicy(db.Model):
    """The association's policies, renewal dates and agent. Mirrors Caliber's Insurance record."""

    __tablename__ = "insurance_policies"
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.String(40), index=True)
    kind = db.Column(db.String(30))  # property|liability|do|fidelity|umbrella|workers_comp|cyber|flood|other
    carrier = db.Column(db.String(200))
    policy_number = db.Column(db.String(80))
    coverage = db.Column(db.Numeric(14, 2))
    deductible = db.Column(db.Numeric(12, 2))
    premium = db.Column(db.Numeric(12, 2))
    begins = db.Column(db.Date)
    expires = db.Column(db.Date, index=True)
    agent_name = db.Column(db.String(200))
    agent_phone = db.Column(db.String(40))
    agent_email = db.Column(db.String(200))
    document_id = db.Column(db.Integer)  # StoredDocument with the declarations page
    notes = db.Column(db.Text)

    @property
    def days_to_expiry(self):
        return (self.expires - dt.date.today()).days if self.expires else None


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
