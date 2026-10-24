from flask import abort, current_app, flash, redirect, render_template, request, session, url_for

import datetime as dt
import os

from ...agents import runtime
from ...ai.assistant import draft_announcement, draft_delinquency_notice
from ...channels import email as email_channel
from ...extensions import db
from ...integrations.registry import get_provider
from ...models import Announcement, AuditLog, InvoiceFlag, Message, ReserveComponent, StoredDocument, WorkItem
from ...services import decisions
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


@bp.route("/invoices")
@role_required("board")
def invoices():
    p, me, community = _ctx()
    status = request.args.get("status")
    flags = {f.invoice_id: f for f in InvoiceFlag.query.filter_by(community_id=community.id).all()}
    return render_template("board/invoices.html", community=community, invoices=p.list_invoices(community.id, status=status), status=status, flags=flags)


@bp.route("/decisions")
@role_required("board")
def decisions_page():
    p, me, community = _ctx()
    return render_template("board/decisions.html", community=community, pending=decisions.pending(community.id), done=decisions.history(community.id), invoices=p.list_invoices(community.id, status="pending_board"), types=decisions.DECISION_TYPES, spec=decisions.spec)


@bp.route("/decisions/new", methods=["POST"])
@role_required("board")
def decision_new():
    p, me, community = _ctx()
    f = request.form
    amount = float(f.get("amount") or 0) or None
    d = decisions.create(community.id, f.get("decision_type", "other"), f.get("title", ""), f.get("body", ""), amount=amount, requested_by=me["name"], shadow=True)
    flash(f"Decision #{d.id} is on the board's list ({decisions.spec(d.category)['approvals']} approvals needed).")
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
    flash(f"{item.subject}: {item.state} ({sum(1 for v in item.remote_ids['votes'] if v['vote'] == 'approve')}/{decisions.spec(item.category)['approvals']} approvals).")
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


@bp.route("/reserves", methods=["GET", "POST"])
@role_required("board")
def reserves():
    p, me, community = _ctx()
    if request.method == "POST":
        f = request.form
        if f.get("intent") == "seed_demo":
            seed_reserve_components(community.id)
            flash("Demo components loaded from the sample study.")
        else:
            c = ReserveComponent(community_id=community.id, name=f.get("name"), category=f.get("category", "other"), quantity=f.get("quantity"), useful_life=int(f.get("useful_life") or 0) or None,
                                 remaining_life=int(f.get("remaining_life") or 0), replacement_cost=float(f.get("replacement_cost") or 0), next_year=int(f.get("next_year") or 0) or None, notes=f.get("notes"), source=f.get("source") or "board entry")
            db.session.add(c)
            db.session.commit()
            _audit(me["name"], "reserve.component.add", f"rc:{c.id}", c.name)
        return redirect(url_for("board.reserves"))
    comps = ReserveComponent.query.filter_by(community_id=community.id).order_by(ReserveComponent.next_year).all()
    snap = p.get_financial_snapshot(community.id)
    total_cost = sum(float(c.replacement_cost or 0) for c in comps)
    fully_funded = sum(c.accrued for c in comps)
    pct = round(snap.reserve_cash / fully_funded * 100) if fully_funded else None
    annual = sum(c.annual_contribution for c in comps)
    years = {}
    for c in comps:
        if c.next_year:
            years[c.next_year] = years.get(c.next_year, 0) + float(c.replacement_cost or 0)
    horizon = sorted(years.items())[:10]
    return render_template("board/reserves.html", community=community, comps=comps, snap=snap, total_cost=total_cost, fully_funded=fully_funded, pct=pct, annual=annual, horizon=horizon, this_year=dt.date.today().year,
                           studies=StoredDocument.query.filter_by(community_id=community.id, category="reserve_study").all())


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
            db.session.add(Announcement(community_id=community.id, title=request.form.get("title"), body=request.form.get("body"), channel=request.form.get("channel", "email"), author=me["name"]))
            db.session.commit()
            flash("Announcement queued. Email goes out within 10 minutes; texts go to owners who opted in.")
            return redirect(url_for("board.announcements"))
    items = Announcement.query.filter_by(community_id=community.id).order_by(Announcement.created_at.desc()).all()
    return render_template("board/announcements.html", community=community, items=items, draft=draft)


@bp.route("/meetings")
@role_required("board")
def meetings():
    p, me, community = _ctx()
    return render_template("board/meetings.html", community=community)


@bp.route("/budget")
@role_required("board")
def budget():
    p, me, community = _ctx()
    snap = p.get_financial_snapshot(community.id)
    return render_template("board/budget.html", community=community, snap=snap)


@bp.route("/settings")
@role_required("board")
def settings():
    p, me, community = _ctx()
    return render_template("board/settings.html", community=community)


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
