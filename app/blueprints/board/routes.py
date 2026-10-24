from flask import flash, redirect, render_template, request, session, url_for

from ...ai.assistant import draft_announcement, draft_delinquency_notice
from ...extensions import db
from ...integrations.registry import get_provider
from ...models import Announcement, AuditLog
from ...services.auth import role_required
from . import bp


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
    return render_template("board/invoices.html", community=community, invoices=p.list_invoices(community.id, status=status), status=status)


@bp.route("/invoices/<invoice_id>/<action>", methods=["POST"])
@role_required("board")
def invoice_action(invoice_id, action):
    p, me, community = _ctx()
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
    return render_template("board/documents.html", community=community, documents=p.list_documents(community.id, board=True))


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
