from flask import flash, redirect, render_template, request, session, url_for

from ...agents import runtime
from ...ai.assistant import classify_request
from ...extensions import db
from ...integrations.registry import get_provider
from ...models import Announcement, PortalRequest
from ...services.auth import role_required
from . import bp


def _ctx():
    me = session["user"]
    p = get_provider()
    ua = p.get_unit_account(me["unit_account_id"])
    community = p.get_community(me["community_id"])
    return p, me, ua, community


@bp.route("/")
@bp.route("/dashboard")
@role_required("homeowner")
def dashboard():
    p, me, ua, community = _ctx()
    announcements = Announcement.query.filter_by(community_id=community.id).order_by(Announcement.created_at.desc()).limit(3).all()
    return render_template(
        "homeowner/dashboard.html", ua=ua, community=community,
        requests=p.list_service_requests(community.id, ua.id)[:3], arcs=p.list_arc_requests(community.id, ua.id)[:2],
        announcements=announcements, ledger=p.get_ledger(ua.id)[:4],
    )


@bp.route("/pay", methods=["GET", "POST"])
@role_required("homeowner")
def pay():
    p, me, ua, community = _ctx()
    if request.method == "POST":
        amount = float(request.form.get("amount") or 0)
        method = request.form.get("method", "ach")
        res = p.post_payment(ua.id, amount, method)
        flash(f"Payment of ${amount:,.2f} received. Confirmation {res.get('confirmation', '—')}.")
        return redirect(url_for("homeowner.ledger"))
    return render_template("homeowner/pay.html", ua=ua, community=community)


@bp.route("/ledger")
@role_required("homeowner")
def ledger():
    p, me, ua, community = _ctx()
    return render_template("homeowner/ledger.html", ua=ua, community=community, ledger=p.get_ledger(ua.id), statements=p.get_statements(ua.id))


@bp.route("/requests")
@role_required("homeowner")
def requests_list():
    p, me, ua, community = _ctx()
    return render_template("homeowner/requests.html", ua=ua, community=community, requests=p.list_service_requests(community.id, ua.id))


@bp.route("/requests/new", methods=["GET", "POST"])
@role_required("homeowner")
def request_new():
    p, me, ua, community = _ctx()
    if request.method == "POST":
        summary = request.form.get("summary", "").strip()
        category = request.form.get("category") or classify_request(summary)["category"]
        sr = p.create_service_request(community.id, ua.id, category, summary)
        db.session.add(PortalRequest(community_id=community.id, unit_account_id=ua.id, kind="maintenance", title=category, body=summary, remote_id=sr.id, ai_category=category))
        db.session.commit()
        runtime.inbound_portal(community_id=community.id, unit_account_id=ua.id, kind="portal_form", subject=f"Maintenance: {category}", body=f"Request {sr.id} filed from the portal: {summary}", email=me.get("email"), name=me.get("name"), lane="cs")
        flash(f"Request {sr.id} logged. We will confirm by text within one business hour.")
        return redirect(url_for("homeowner.requests_list"))
    return render_template("homeowner/request_new.html", ua=ua, community=community)


@bp.route("/arc")
@role_required("homeowner")
def arc_list():
    p, me, ua, community = _ctx()
    return render_template("homeowner/arc.html", ua=ua, community=community, arcs=p.list_arc_requests(community.id, ua.id))


@bp.route("/arc/new", methods=["GET", "POST"])
@role_required("homeowner")
def arc_new():
    p, me, ua, community = _ctx()
    if request.method == "POST":
        arc = p.create_arc_request(community.id, ua.id, request.form.get("request_type", "Other"), request.form.get("notes", ""))
        db.session.add(PortalRequest(community_id=community.id, unit_account_id=ua.id, kind="arc", title=arc.request_type, body=arc.notes, remote_id=arc.id))
        db.session.commit()
        flash(f"ARC application {arc.id} submitted. The committee has 30 days under your CC&Rs; most decisions come back in under 10.")
        return redirect(url_for("homeowner.arc_list"))
    return render_template("homeowner/arc_new.html", ua=ua, community=community)


@bp.route("/documents")
@role_required("homeowner")
def documents():
    p, me, ua, community = _ctx()
    return render_template("homeowner/documents.html", ua=ua, community=community, documents=p.list_documents(community.id))


@bp.route("/directory")
@role_required("homeowner")
def directory():
    p, me, ua, community = _ctx()
    return render_template("homeowner/directory.html", ua=ua, community=community)


@bp.route("/profile", methods=["GET", "POST"])
@role_required("homeowner")
def profile():
    p, me, ua, community = _ctx()
    if request.method == "POST":
        flash("Contact preferences saved.")
        return redirect(url_for("homeowner.profile"))
    return render_template("homeowner/profile.html", ua=ua, community=community)


@bp.route("/ask")
@role_required("homeowner")
def ask():
    p, me, ua, community = _ctx()
    return render_template("homeowner/ask.html", ua=ua, community=community)
