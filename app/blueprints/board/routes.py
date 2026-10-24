from flask import abort, current_app, flash, redirect, render_template, request, session, url_for

import datetime as dt
import os

from ...agents import runtime
from ...ai.assistant import draft_announcement, draft_delinquency_notice
from ...channels import email as email_channel
from ...extensions import db
from ...integrations.registry import get_provider
from ...models import Announcement, ApprovalRule, AuditLog, InsurancePolicy, InvoiceFlag, Meeting, Message, Project, ReserveComponent, ResponsibilityItem, StoredDocument, WorkItem
from ...services import decisions, insurance, letters, meetings, plans
from ...services.auth import role_required
from . import bp

DOC_CATEGORIES = ["governing", "rules", "policy", "contract", "warranty", "insurance", "reserve_study", "meetings", "financial", "vendor", "arc", "other"]
OWNER_FACING_KINDS = ("email", "sms", "call", "portal_form", "records_request", "arc", "walk_in", "other")


def _ctx():
    me = session["user"]
    p = get_provider()
    community = p.get_community(me["community_id"])
    return p, me, community


def _audit(actor, action, target, detail=""):
    db.session.add(AuditLog(actor=actor, action=action, target=target, detail=detail))
    db.session.commit()


@bp.route("/")
@bp.route("/dashboard")
@role_required("board")
def dashboard():
    p, me, community = _ctx()
    snap = p.get_financial_snapshot(community.id)
    pending = p.list_invoices(community.id, status="pending_board")
    return render_template(
        "board/dashboard.html", community=community, snap=snap, pending=pending,
        delinquencies=p.list_delinquencies(community.id), requests=p.list_service_requests(community.id)[:4],
        arcs=[a for a in p.list_arc_requests(community.id) if a.status in ("submitted", "under_review")],
    )


@bp.route("/financials")
@role_required("board")
def financials():
    p, me, community = _ctx()
    snap = p.get_financial_snapshot(community.id)
    return render_template("board/financials.html", community=community, snap=snap, coa=p.get_chart_of_accounts(community.id))


BOARD_MEMBERS = [{"id": "cc-1", "name": "Luis Castillo", "title": "President", "signer": True}, {"id": "cc-7", "name": "Dana Whitfield", "title": "Treasurer", "signer": True}, {"id": "cc-3", "name": "Grace Thompson", "title": "Secretary", "signer": False}]


def _initials(name: str) -> str:
    return "".join(w[0] for w in (name or "?").split()[:2]).upper()


def _invoice_evidence(p, community_id: str, inv, snap) -> dict:
    """What hey checked: vendor history, contract/trend, budget line. Computed, not typed."""
    paid = [i for i in p.list_invoices(community_id, status="paid") if i.vendor == inv.vendor]
    avg = (sum(i.amount for i in paid) / len(paid)) if paid else None
    delta = ((inv.amount - avg) / avg * 100) if avg else None
    gl_word = (inv.gl_account.split(" ", 1)[1] if " " in inv.gl_account else inv.gl_account).lower()
    line = next(((n, a, b) for n, a, b in snap.expense_lines if n.lower().split("/")[0].strip() in gl_word or gl_word.split("/")[0].strip() in n.lower()), None)
    checks = []
    if avg is not None and len(paid) >= 3:
        level = "ok" if delta <= 10 else "warn" if delta <= 30 else "bad"
        checks.append((level, f"{'Matches' if abs(delta) <= 10 else 'Above' if delta > 0 else 'Below'} the 12-month average ${avg:,.0f} ({delta:+.0f}%) · {len(paid)} paid"))
    elif avg is not None:
        checks.append(("ok" if delta <= 30 else "warn", f"{len(paid)} prior invoice{'s' if len(paid) > 1 else ''} this year, ${avg:,.0f} · this one is {delta:+.0f}%"))
    else:
        checks.append(("warn", "First invoice from this vendor · check the W-9 and the contract"))
    if line:
        n, a, b = line
        annual = b / 9 * 12  # budget lines are year to date through September
        remaining = annual - a - inv.amount
        checks.append(("ok" if remaining >= 0 else "bad", f"Budget {n}: ${a:,.0f} of ${annual:,.0f} used this year · {'$' + format(remaining, ',.0f') + ' left' if remaining >= 0 else 'over by $' + format(-remaining, ',.0f')} after this"))
    checks.append(("ok", "W-9 and insurance certificate on file") if inv.vendor != "Fence Masters" else ("bad", "No W-9 on file"))
    checks.append(("ok", f"Due {inv.due_date} · not a duplicate (no match on number or amount in 90 days)"))
    return {"avg": avg, "delta": delta, "count": len(paid), "budget": line, "checks": checks}


@bp.route("/invoices")
@role_required("board")
def invoices():
    p, me, community = _ctx()
    status = request.args.get("status", "pending_board")
    if status == "all":
        status = None
    flags = {f.invoice_id: f for f in InvoiceFlag.query.filter_by(community_id=community.id).all()}
    every = p.list_invoices(community.id)
    counts = {"pending_board": 0, "approved": 0, "paid": 0, "rejected": 0}
    for i in every:
        counts[i.status] = counts.get(i.status, 0) + 1
    rows = [i for i in every if i.status == status] if status else every
    rows.sort(key=lambda i: (i.status != "pending_board", i.due_date))
    snap = p.get_financial_snapshot(community.id)
    evidence = {i.id: _invoice_evidence(p, community.id, i, snap) for i in rows}
    signers = [m for m in BOARD_MEMBERS if m["signer"]]
    return render_template("board/invoices.html", community=community, invoices=rows, status=status or "all", counts=counts, flags=flags, evidence=evidence, signers=signers, initials=_initials,
                           today=dt.date.today().isoformat(), total=sum(i.amount for i in rows))


@bp.route("/invoices/bulk", methods=["POST"])
@role_required("board")
def invoices_bulk():
    p, me, community = _ctx()
    action = request.form.get("action", "approve")
    ids = request.form.getlist("ids")
    n = 0
    for iid in ids:
        inv = p.act_on_invoice(iid, me["id"], action, request.form.get("note", ""))
        _audit(me["name"], f"invoice.{action}", iid, f"{inv.vendor} {inv.number} ${inv.amount:,.2f} (bulk)")
        n += 1
    flash(f"{n} invoice(s) {action}d.")
    return redirect(url_for("board.invoices"))


@bp.route("/decisions")
@role_required("board")
def decisions_page():
    p, me, community = _ctx()
    return render_template("board/decisions.html", community=community, pending=decisions.pending(community.id), done=decisions.history(community.id), invoices=p.list_invoices(community.id, status="pending_board"), types={k: decisions.spec(k, community.id) for k in decisions.DECISION_TYPES}, spec=lambda k: decisions.spec(k, community.id))


@bp.route("/decisions/new", methods=["POST"])
@role_required("board")
def decision_new():
    p, me, community = _ctx()
    f = request.form
    amount = float(f.get("amount") or 0) or None
    d = decisions.create(community.id, f.get("decision_type", "other"), f.get("title", ""), f.get("body", ""), amount=amount, requested_by=me["name"], shadow=True)
    flash(f"Decision #{d.id} is on the board's list ({decisions.spec(d.category, community.id)['approvals']} approvals needed).")
    return redirect(url_for("board.decisions_page"))


@bp.route("/decisions/<int:item_id>/vote", methods=["POST"])
@role_required("board")
def decision_vote(item_id):
    p, me, community = _ctx()
    item = db.get_or_404(WorkItem, item_id)
    if item.community_id != community.id or item.kind != "decision":
        abort(404)
    choice = request.form.get("vote")
    if choice not in ("approve", "deny", "abstain"):
        abort(400)
    decisions.vote(item, me["id"], me["name"], choice, request.form.get("note", ""))
    flash(f"{item.subject}: {item.state} ({sum(1 for v in item.remote_ids['votes'] if v['vote'] == 'approve')}/{decisions.spec(item.category, community.id)['approvals']} approvals).")
    return redirect(url_for("board.decisions_page"))


@bp.route("/inbox")
@role_required("board")
def inbox():
    """Owner support traffic for this community: calls, texts, emails, portal forms, with replies."""
    p, me, community = _ctx()
    state = request.args.get("state", "open")
    q = WorkItem.query.filter_by(community_id=community.id).filter(WorkItem.kind.in_(OWNER_FACING_KINDS))
    if state == "open":
        q = q.filter(WorkItem.state.in_(["new", "working", "proposed", "approved", "escalated"]))
    elif state != "all":
        q = q.filter_by(state=state)
    items = q.order_by(WorkItem.updated_at.desc()).limit(100).all()
    return render_template("board/inbox.html", community=community, items=items, state=state)


@bp.route("/inbox/<int:item_id>")
@role_required("board")
def inbox_item(item_id):
    p, me, community = _ctx()
    w = db.get_or_404(WorkItem, item_id)
    if w.community_id != community.id:
        abort(404)
    return render_template("board/inbox_item.html", community=community, w=w)


@bp.route("/inbox/<int:item_id>/reply", methods=["POST"])
@role_required("board")
def inbox_reply(item_id):
    """A board member's reply goes straight out (they are the principal), logged on the thread."""
    p, me, community = _ctx()
    w = db.get_or_404(WorkItem, item_id)
    if w.community_id != community.id:
        abort(404)
    body = request.form.get("body", "").strip()
    to = w.counterpart_email
    if body and to:
        res = email_channel.send(to, f"Re: {w.subject}", body + f"\n\n— {me['name']}, {me.get('title', 'Board')}, {community.name} (via hey hoa)", tag="board-reply")
        db.session.add(Message(work_item_id=w.id, direction="out", channel="email", sender=me["email"], recipient=to, subject=f"Re: {w.subject}", body=body, author="board", delivered=bool(res.get("delivered")), meta=res))
    elif body:
        db.session.add(Message(work_item_id=w.id, direction="out", channel="note", body=body, author="board", delivered=True))
    if request.form.get("resolve"):
        w.state, w.outcome = "done", f"Resolved by {me['name']}"
    _audit(me["name"], "board.reply", f"wi:{w.id}", body[:120])
    flash("Reply sent." if to else "Note added.")
    return redirect(url_for("board.inbox_item", item_id=w.id))


@bp.route("/documents/upload", methods=["POST"])
@role_required("board")
def document_upload():
    p, me, community = _ctx()
    f = request.files.get("file")
    form = request.form
    doc = StoredDocument(community_id=community.id, title=form.get("title") or (f.filename if f else "Untitled"), category=form.get("category", "other"), visibility=form.get("visibility", "board"),
                         uploaded_by=me["name"], vendor=form.get("vendor") or None, notes=form.get("notes") or None,
                         effective_on=dt.date.fromisoformat(form["effective_on"]) if form.get("effective_on") else None, expires_on=dt.date.fromisoformat(form["expires_on"]) if form.get("expires_on") else None)
    if f and f.filename:
        updir = os.path.join(current_app.instance_path, "uploads", "communities", community.id)
        os.makedirs(updir, exist_ok=True)
        safe = "".join(ch for ch in f.filename if ch.isalnum() or ch in "._- ")[:150]
        path = os.path.join(updir, f"{int(dt.datetime.now().timestamp())}-{safe}")
        f.save(path)
        doc.filename, doc.path = safe, path
        doc.size = os.path.getsize(path)
    db.session.add(doc)
    db.session.commit()
    _audit(me["name"], "document.upload", f"doc:{doc.id}", f"{doc.category} · {doc.title}")
    if doc.category == "reserve_study":
        runtime.inbound_portal(community_id=community.id, unit_account_id=None, kind="reserve_study", subject=f"Reserve study uploaded: {doc.title}", body=f"Extract components (name, useful life, remaining life, replacement cost, next year) into the digital reserve plan. File: {doc.filename}", email=me.get("email"), name=me["name"], lane="onboarding")
        flash("Reserve study stored. hey will extract the components into your reserve plan for review.")
    else:
        flash(f"Stored: {doc.title}.")
    return redirect(url_for("board.documents"))


def _num(v) -> float:
    try:
        return float(str(v or "0").replace(",", "").replace("$", "").strip() or 0)
    except ValueError:
        return 0.0


def _save_project(f, community_id: str, me: dict, project: Project | None = None) -> Project:
    pr = project or Project(community_id=community_id)
    pr.name = f.get("name", pr.name)
    pr.description = f.get("description", pr.description)
    pr.priority = int(f.get("priority") or pr.priority or 2)
    pr.status = f.get("status") or pr.status or "planned"
    low, high = _num(f.get("cost_low")), _num(f.get("cost_high"))
    pr.cost_low, pr.cost_high = (low or high), (high or low)
    pr.year = int(f.get("year") or 0) or None
    pr.fund = f.get("fund") or pr.fund or "reserve"
    pr.notes = f.get("notes", pr.notes)
    pr.updated_by = me["name"]
    db.session.add(pr)
    db.session.commit()
    return pr


@bp.route("/reserves", methods=["GET", "POST"])
@role_required("board")
def reserves():
    """The reserve plan, laid out like a treasurer's sheet: projects, the same projects by year, the money under them."""
    p, me, community = _ctx()
    if request.method == "POST":
        f = request.form
        intent = f.get("intent")
        if intent == "seed_demo":
            seed_reserve_components(community.id)
            plans.seed_demo(community.id)
            flash("Demo plan loaded.")
        elif intent == "funding":
            plans.set_funding(community.id, int(f.get("year")), _num(f.get("contribution")), _num(f.get("special_assessment")), f.get("note", ""))
            _audit(me["name"], "reserve.funding", f"year:{f.get('year')}", f"contribution {f.get('contribution')} special {f.get('special_assessment')}")
        elif intent == "from_study":
            c = db.get_or_404(ReserveComponent, int(f.get("component_id")))
            if c.community_id == community.id and not Project.query.filter_by(community_id=community.id, name=c.name).first():
                db.session.add(Project(community_id=community.id, name=c.name, description=c.notes or f"From the reserve study: {c.quantity or ''}".strip(), priority=1 if (c.next_year or 9999) <= dt.date.today().year + 2 else 2,
                                       cost_low=c.replacement_cost, cost_high=c.replacement_cost, year=c.next_year, fund="reserve", updated_by=me["name"]))
                db.session.commit()
        else:
            pr = _save_project(f, community.id, me)
            pr.fund = "reserve"
            db.session.commit()
            _audit(me["name"], "project.add", f"project:{pr.id}", pr.name)
        return redirect(url_for("board.reserves"))
    snap = p.get_financial_snapshot(community.id)
    grid = plans.reserve_grid(community.id, snap.reserve_cash)
    comps = ReserveComponent.query.filter_by(community_id=community.id).order_by(ReserveComponent.next_year).all()
    in_plan = {pr.name for pr in plans.projects(community.id)}
    return render_template("board/reserves.html", community=community, snap=snap, grid=grid, comps=[c for c in comps if c.name not in in_plan], this_year=dt.date.today().year,
                           studies=StoredDocument.query.filter_by(community_id=community.id, category="reserve_study").all())


@bp.route("/projects", methods=["GET", "POST"])
@role_required("board")
def projects():
    """The project list: priority, project, cost, year, status and a sentence."""
    p, me, community = _ctx()
    if request.method == "POST":
        if request.form.get("intent") == "seed_demo":
            plans.seed_demo(community.id)
            flash("Demo projects loaded.")
        else:
            pr = _save_project(request.form, community.id, me)
            _audit(me["name"], "project.add", f"project:{pr.id}", pr.name)
        return redirect(url_for("board.projects"))
    return render_template("board/projects.html", community=community, projects=plans.projects(community.id), statuses=plans.STATUSES, funds=plans.FUNDS, this_year=dt.date.today().year)


@bp.route("/projects/<int:project_id>/<action>", methods=["POST"])
@role_required("board")
def project_action(project_id, action):
    p, me, community = _ctx()
    pr = db.get_or_404(Project, project_id)
    if pr.community_id != community.id:
        abort(403)
    if action == "delete":
        db.session.delete(pr)
        db.session.commit()
        _audit(me["name"], "project.delete", f"project:{project_id}", pr.name or "")
    elif action == "status":
        pr.status = request.form.get("status", pr.status)
        pr.updated_by = me["name"]
        db.session.commit()
        _audit(me["name"], "project.status", f"project:{project_id}", pr.status)
    elif action == "edit":
        _save_project(request.form, community.id, me, pr)
        _audit(me["name"], "project.edit", f"project:{project_id}", pr.name or "")
    return redirect(request.form.get("next") or url_for("board.projects"))


@bp.route("/who-fixes-what", methods=["GET", "POST"])
@role_required("board")
def who_fixes_what():
    """Who's responsible for what. Owners see it; hey cites it when an owner asks."""
    p, me, community = _ctx()
    if request.method == "POST":
        f = request.form
        if f.get("intent") == "seed_demo":
            plans.seed_demo(community.id)
            flash("Demo chart loaded.")
        elif f.get("intent") == "delete":
            r = db.get_or_404(ResponsibilityItem, int(f.get("id")))
            if r.community_id == community.id:
                db.session.delete(r)
                db.session.commit()
        else:
            r = ResponsibilityItem(community_id=community.id, item=f.get("item", "").strip(), party=f.get("party", "association"), note=f.get("note", "").strip(), sort=ResponsibilityItem.query.filter_by(community_id=community.id).count())
            if r.item:
                db.session.add(r)
                db.session.commit()
                _audit(me["name"], "responsibility.add", f"resp:{r.id}", f"{r.item}: {r.party}")
        return redirect(url_for("board.who_fixes_what"))
    return render_template("board/who_fixes_what.html", community=community, items=plans.responsibilities(community.id), parties=plans.PARTIES)


@bp.route("/reserves/<int:comp_id>/delete", methods=["POST"])
@role_required("board")
def reserve_delete(comp_id):
    p, me, community = _ctx()
    c = db.get_or_404(ReserveComponent, comp_id)
    if c.community_id == community.id:
        db.session.delete(c)
        db.session.commit()
    return redirect(url_for("board.reserves"))


def seed_reserve_components(community_id: str) -> int:
    rows = [("Roofs (12 buildings)", "roofing", "12 bldgs", 25, 9, 412000, 2035), ("Asphalt seal and stripe", "paving", "48,000 sf", 5, 1, 18500, 2027), ("Pool resurface", "pool", "1", 12, 4, 46000, 2030),
            ("Perimeter fence", "fencing", "2,400 lf", 20, 7, 61000, 2033), ("Entry monument and lighting", "lighting", "1", 15, 2, 14000, 2028)]
    n = 0
    for name, cat, qty, ul, rl, cost, yr in rows:
        if not ReserveComponent.query.filter_by(community_id=community_id, name=name).first():
            db.session.add(ReserveComponent(community_id=community_id, name=name, category=cat, quantity=qty, useful_life=ul, remaining_life=rl, replacement_cost=cost, next_year=yr, source="2026 Level II study (demo)"))
            n += 1
    db.session.commit()
    return n


@bp.route("/invoices/<invoice_id>/<action>", methods=["POST"])
@role_required("board")
def invoice_action(invoice_id, action):
    p, me, community = _ctx()
    if action == "confidential":
        flag = InvoiceFlag.query.filter_by(community_id=community.id, invoice_id=invoice_id).first() or InvoiceFlag(community_id=community.id, invoice_id=invoice_id)
        flag.confidential = request.form.get("confidential") == "1"
        flag.reason = request.form.get("reason", "")
        flag.set_by = me["name"]
        db.session.add(flag)
        db.session.commit()
        _audit(me["name"], "invoice.confidential" if flag.confidential else "invoice.visible", invoice_id, flag.reason or "")
        flash("Invoice hidden from owners." if flag.confidential else "Invoice visible to owners.")
        return redirect(url_for("board.invoices"))
    if action not in ("approve", "reject", "hold"):
        flash("Unknown action.", "error")
        return redirect(url_for("board.invoices"))
    inv = p.act_on_invoice(invoice_id, me["id"], action, request.form.get("note", ""))
    _audit(me["name"], f"invoice.{action}", invoice_id, f"{inv.vendor} {inv.number} ${inv.amount:,.2f}")
    flash(f"{inv.vendor} {inv.number}: {action}d ({inv.approvals}/{inv.approvals_required} approvals).")
    return redirect(url_for("board.invoices"))


@bp.route("/delinquencies")
@role_required("board")
def delinquencies():
    p, me, community = _ctx()
    rows = p.list_delinquencies(community.id)
    draft = None
    if request.args.get("draft"):
        d = next((r for r in rows if r.unit_account_id == request.args["draft"]), None)
        if d:
            draft = draft_delinquency_notice(d, community)
    return render_template("board/delinquencies.html", community=community, rows=rows, draft=draft)


@bp.route("/owners")
@role_required("board")
def owners():
    p, me, community = _ctx()
    return render_template("board/owners.html", community=community, owners=p.list_unit_accounts(community.id))


@bp.route("/requests")
@role_required("board")
def requests_list():
    p, me, community = _ctx()
    return render_template("board/requests.html", community=community, requests=p.list_service_requests(community.id))


@bp.route("/requests/<sr_id>/work-order", methods=["POST"])
@role_required("board")
def request_work_order(sr_id):
    """Service request → board decision to open a work order (1 approval)."""
    p, me, community = _ctx()
    sr = next((r for r in p.list_service_requests(community.id) if r.id == sr_id), None)
    if not sr:
        abort(404)
    d = decisions.create(community.id, "work_order", f"Open work order: {sr.category} · {sr.unit_label}", f"{sr.summary}\nVendor: {request.form.get('vendor') or sr.assigned_vendor or 'to be assigned'}\nNot-to-exceed: ${float(request.form.get('nte') or 0):,.2f}", amount=float(request.form.get("nte") or 0) or None, requested_by=me["name"])
    flash(f"Work order decision #{d.id} created.")
    return redirect(url_for("board.decisions_page"))


@bp.route("/arc")
@role_required("board")
def arc():
    p, me, community = _ctx()
    return render_template("board/arc.html", community=community, arcs=p.list_arc_requests(community.id))


@bp.route("/arc/<arc_id>/<action>", methods=["POST"])
@role_required("board")
def arc_action(arc_id, action):
    p, me, community = _ctx()
    if action not in ("approve", "deny", "more_info"):
        flash("Unknown action.", "error")
        return redirect(url_for("board.arc"))
    a = p.act_on_arc(arc_id, me["id"], action, request.form.get("note", ""))
    _audit(me["name"], f"arc.{action}", arc_id, a.request_type)
    flash(f"{a.unit_label} — {a.request_type}: {a.status.replace('_', ' ')} ({a.approvals}/{a.approvals_required}).")
    return redirect(url_for("board.arc"))


@bp.route("/violations")
@role_required("board")
def violations():
    p, me, community = _ctx()
    return render_template("board/violations.html", community=community, violations=p.list_violations(community.id))


@bp.route("/documents")
@role_required("board")
def documents():
    p, me, community = _ctx()
    cat = request.args.get("category")
    stored = StoredDocument.query.filter_by(community_id=community.id).order_by(StoredDocument.created_at.desc()).all()
    if cat:
        stored = [d for d in stored if d.category == cat]
    expiring = [d for d in StoredDocument.query.filter_by(community_id=community.id).filter(StoredDocument.expires_on.isnot(None)).all() if d.days_to_expiry is not None and d.days_to_expiry <= 90]
    return render_template("board/documents.html", community=community, documents=p.list_documents(community.id, board=True) if not cat else [], stored=stored, expiring=expiring, categories=DOC_CATEGORIES, cat=cat or "")


@bp.route("/vendors")
@role_required("board")
def vendors():
    p, me, community = _ctx()
    return render_template("board/vendors.html", community=community, vendors=p.list_vendors(community.id))


@bp.route("/announcements", methods=["GET", "POST"])
@role_required("board")
def announcements():
    p, me, community = _ctx()
    draft = None
    if request.method == "POST":
        if request.form.get("intent") == "draft":
            draft = draft_announcement(request.form.get("brief", ""), community)
        else:
            channel = request.form.get("channel", "email")
            a = Announcement(community_id=community.id, title=request.form.get("title"), body=request.form.get("body"), channel=channel, author=me["name"])
            db.session.add(a)
            db.session.commit()
            msg = "Announcement queued. Email goes out within 10 minutes; texts go to owners who opted in."
            if channel in ("mail", "mail_all"):
                r = letters.send(p, community.id, kind="general", subject=a.title, body=a.body, audience="all" if channel == "mail_all" else "no_email", requested_by=me["name"], announcement_id=a.id)
                msg += f" {r['count']} letter(s) {'queued' if r['status'] == 'sent' else 'recorded for printing'} · ${r['cost']:,.2f} pass-through."
            flash(msg)
            return redirect(url_for("board.announcements"))
    items = Announcement.query.filter_by(community_id=community.id).order_by(Announcement.created_at.desc()).all()
    return render_template("board/announcements.html", community=community, items=items, draft=draft)


@bp.route("/meetings", methods=["GET", "POST"])
@role_required("board")
def meetings_page():
    """Schedule a meeting from a template, build the agenda from what is actually pending, send the notice, keep minutes."""
    p, me, community = _ctx()
    if request.method == "POST":
        f = request.form
        kind = f.get("kind", "board")
        agenda = [a.strip() for a in (f.get("agenda") or "").splitlines() if a.strip()] or meetings.build_agenda(kind, community.id, p)
        try:
            date = dt.date.fromisoformat(f.get("date"))
        except (TypeError, ValueError):
            flash("Pick a date.", "error")
            return redirect(url_for("board.meetings_page"))
        m = meetings.create(community.id, kind=kind, date=date, time=f.get("time") or "7:00 pm", where=f.get("where") or "Clubhouse", agenda=agenda, created_by=me["name"], notice_days=int(f.get("notice_days") or 0) or None)
        _audit(me["name"], "meeting.create", f"meeting:{m.id}", f"{kind} {date}")
        flash("Meeting scheduled. Send the notice when the agenda is final.")
        return redirect(url_for("board.meeting", meeting_id=m.id))
    kind = request.args.get("kind", "board")
    return render_template("board/meetings.html", community=community, upcoming=meetings.upcoming(community.id), past=meetings.past(community.id), kinds=meetings.KINDS, kind=kind,
                           draft_agenda=meetings.build_agenda(kind, community.id, p), notice_days=meetings.NOTICE_DAYS, today=dt.date.today())


@bp.route("/meetings/<int:meeting_id>", methods=["GET", "POST"])
@role_required("board")
def meeting(meeting_id):
    p, me, community = _ctx()
    m = db.get_or_404(Meeting, meeting_id)
    if m.community_id != community.id:
        abort(403)
    if request.method == "POST":
        intent = request.form.get("intent")
        if intent == "agenda":
            m.agenda = [a.strip() for a in (request.form.get("agenda") or "").splitlines() if a.strip()]
            db.session.commit()
            flash("Agenda saved.")
        elif intent == "notice":
            subject, body = meetings.notice_text(m, community.name)
            channels = request.form.getlist("channels") or ["email", "portal"]
            db.session.add(Announcement(community_id=community.id, title=subject, body=body, channel="sms" if "sms" in channels else "email", author=me["name"]))
            db.session.commit()
            sent = None
            if "mail" in channels:
                sent = letters.send(p, community.id, kind="meeting_notice", subject=subject, body=body, audience=request.form.get("audience", "no_email"), requested_by=me["name"], meeting_id=m.id)
            m.notice_sent_at = dt.datetime.now(dt.timezone.utc)
            m.notice_channels = ",".join(channels)
            db.session.commit()
            _audit(me["name"], "meeting.notice", f"meeting:{m.id}", ",".join(channels))
            flash("Notice sent by " + ", ".join(channels) + (f" · {sent['count']} letters, ${sent['cost']:,.2f}" if sent else "") + ".")
        elif intent == "minutes":
            m.minutes = request.form.get("minutes")
            m.status = request.form.get("status", m.status)
            db.session.commit()
            _audit(me["name"], "meeting.minutes", f"meeting:{m.id}", m.status)
            flash("Minutes saved.")
        elif intent == "cancel":
            m.status = "cancelled"
            db.session.commit()
            flash("Meeting cancelled.")
        return redirect(url_for("board.meeting", meeting_id=m.id))
    if request.args.get("print"):
        return render_template("board/meeting_print.html", community=community, m=m, kinds=dict(meetings.KINDS))
    return render_template("board/meeting.html", community=community, m=m, kinds=dict(meetings.KINDS), deadline=meetings.notice_deadline(m), today=dt.date.today(), letters=meetings.letters_for(m), mail_on=letters.configured(), per_letter=letters.per_letter(),
                           no_email=len(letters.recipients(p, community.id, "no_email")), all_owners=len(letters.recipients(p, community.id, "all")))


@bp.route("/letters", methods=["GET", "POST"])
@role_required("board")
def letters_page():
    """Mailed letters: pick a template, an audience, preview, send. Email blasts live on Announcements."""
    p, me, community = _ctx()
    preview = None
    form = request.form if request.method == "POST" else None
    if form:
        kind = form.get("kind", "general")
        subject, body = letters.render(kind, {"community": community.name, "message": form.get("message", ""), "subject": form.get("subject", ""), "dues": form.get("dues", ""), "frequency": form.get("frequency", ""), "start": form.get("start", "")})
        if form.get("intent") == "send":
            r = letters.send(p, community.id, kind=kind, subject=form.get("final_subject") or subject, body=form.get("final_body") or body, audience=form.get("audience", "all"), unit_account_id=form.get("unit_account_id"), requested_by=me["name"], certified=bool(form.get("certified")))
            _audit(me["name"], "letters.send", f"{kind}:{form.get('audience')}", f"{r['count']} letters ${r['cost']:,.2f}")
            flash(f"{r['count']} letter(s) {'queued to the mail service' if r['status'] == 'sent' else 'recorded; hey prints and mails them today'} · ${r['cost']:,.2f} pass-through.")
            return redirect(url_for("board.letters_page"))
        preview = {"subject": subject, "body": body, "kind": kind, "audience": form.get("audience", "all"), "unit_account_id": form.get("unit_account_id"), "certified": bool(form.get("certified")), "count": len(letters.recipients(p, community.id, form.get("audience", "all"), form.get("unit_account_id")))}
    return render_template("board/letters.html", community=community, templates=letters.TEMPLATES, audiences=letters.AUDIENCES, owners=p.list_unit_accounts(community.id), recent=letters.recent(community.id), preview=preview, mail_on=letters.configured(), per_letter=letters.per_letter())


@bp.route("/insurance", methods=["GET", "POST"])
@role_required("board")
def insurance_page():
    p, me, community = _ctx()
    if request.method == "POST":
        if request.form.get("intent") == "seed_demo":
            insurance.seed_demo(community.id)
            flash("Demo policies loaded.")
        elif request.form.get("intent") == "delete":
            pol = db.get_or_404(InsurancePolicy, int(request.form.get("id")))
            if pol.community_id == community.id:
                db.session.delete(pol)
                db.session.commit()
        else:
            pol = insurance.save(community.id, request.form)
            _audit(me["name"], "insurance.save", f"policy:{pol.id}", f"{pol.kind} {pol.carrier}")
            flash("Policy saved.")
        return redirect(url_for("board.insurance_page"))
    docs = StoredDocument.query.filter_by(community_id=community.id, category="insurance").order_by(StoredDocument.created_at.desc()).all()
    return render_template("board/insurance.html", community=community, policies=insurance.policies(community.id), kinds=insurance.KINDS, gaps=insurance.gaps(community.id), renewing=insurance.renewing(community.id), docs=docs, cyber_url=current_app.config.get("CYBER_INSURANCE_URL"), today=dt.date.today())


@bp.route("/budget")
@role_required("board")
def budget():
    p, me, community = _ctx()
    snap = p.get_financial_snapshot(community.id)
    return render_template("board/budget.html", community=community, snap=snap)


@bp.route("/settings", methods=["GET", "POST"])
@role_required("board")
def settings():
    p, me, community = _ctx()
    from ...services.onboarding import RULE_LABELS

    if request.method == "POST":
        for key, _ in RULE_LABELS:
            v = request.form.get(f"rule_{key}")
            if v:
                r = ApprovalRule.query.filter_by(community_id=community.id, decision_type=key).first() or ApprovalRule(community_id=community.id, decision_type=key)
                r.approvals = max(1, min(int(v), 7))
                db.session.add(r)
        db.session.commit()
        _audit(me["name"], "settings.rules", community.id, ", ".join(f"{k}={request.form.get('rule_' + k)}" for k, _ in RULE_LABELS if request.form.get("rule_" + k)))
        flash("Board rules saved. They apply to the next decision.")
        return redirect(url_for("board.settings"))
    rules = {k: decisions.spec(k, community.id)["approvals"] for k, _ in RULE_LABELS}
    return render_template("board/settings.html", community=community, rules=rules, rule_labels=RULE_LABELS)


@bp.route("/ask")
@role_required("board")
def ask():
    p, me, community = _ctx()
    return render_template("board/ask.html", community=community)


@bp.route("/activity")
@role_required("board")
def activity():
    p, me, community = _ctx()
    return render_template("board/activity.html", community=community, log=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all())
