"""hey ops: the admin console. Humans review what agents propose."""
import datetime as dt

from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func

from ...agents import runtime
from ...agents.lanes import AGENTS
from ...extensions import db
from ...integrations.registry import get_provider
from ...models import AgentRun, AuditLog, Message, WorkItem
from ...services.auth import role_required
from . import bp

LANES = list(AGENTS.keys())
STATES = ["new", "working", "proposed", "approved", "escalated", "done", "rejected", "failed"]


def _communities():
    return {c.id: c for c in get_provider().list_communities()}


@bp.route("/")
@bp.route("/dashboard")
@role_required("ops")
def dashboard():
    return review()


@bp.route("/queue")
@role_required("ops")
def queue():
    q = WorkItem.query
    lane, state, cid = request.args.get("lane"), request.args.get("state"), request.args.get("community")
    if lane:
        q = q.filter_by(lane=lane)
    if state == "open":
        q = q.filter(WorkItem.state.in_(["new", "working", "proposed", "approved", "escalated"]))
    elif state:
        q = q.filter_by(state=state)
    if cid:
        q = q.filter_by(community_id=cid)
    items = q.order_by(WorkItem.updated_at.desc()).limit(200).all()
    return render_template("ops/queue.html", items=items, lanes=LANES, states=STATES, lane=lane, state=state or "", cid=cid, communities=_communities())


@bp.route("/review")
@role_required("ops")
def review():
    """Home. Everything hey proposes, waiting on a person, with the four numbers that matter."""
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    items = WorkItem.query.filter(WorkItem.state.in_(["proposed", "escalated"])).order_by(WorkItem.priority.desc(), WorkItem.sla_due).all()
    open_q = WorkItem.query.filter(WorkItem.state.in_(["new", "working", "proposed", "approved", "escalated"])).all()
    done = WorkItem.query.filter(WorkItem.state == "done")
    total_done = done.count()
    stats = {"waiting": len(items), "overdue": sum(1 for w in open_q if w.sla_due and w.sla_due < now), "done_today": done.filter(WorkItem.updated_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)).count(),
             "auto_rate": round(done.filter(WorkItem.reviewer.is_(None)).count() / max(total_done, 1) * 100)}
    return render_template("ops/review.html", items=items, communities=_communities(), now=now, stats=stats, shadow=current_app.config.get("SHADOW_MODE", True))


@bp.route("/item/<int:item_id>")
@role_required("ops")
def item(item_id):
    w = db.get_or_404(WorkItem, item_id)
    return render_template("ops/item.html", w=w, agent=AGENTS.get(w.lane), communities=_communities(), lanes=LANES)


@bp.route("/item/<int:item_id>/approve", methods=["POST"])
@role_required("ops")
def approve(item_id):
    w = db.get_or_404(WorkItem, item_id)
    edits = {}
    if request.form.get("body") and request.form.get("body") != ((w.proposal or {}).get("payload") or {}).get("body"):
        edits["body"] = request.form["body"]
    res = runtime.approve(w, session["user"]["name"], edits=edits, note=request.form.get("note", ""))
    flash(("Approved and executed." if res.get("ok") else f"Approved but execution failed: {res.get('error')}") + (" (simulated send: no transport configured)" if res.get("simulated") or (res.get("sent") or {}).get("simulated") else ""), "" if res.get("ok") else "error")
    return redirect(url_for("ops.review"))


@bp.route("/item/<int:item_id>/reject", methods=["POST"])
@role_required("ops")
def reject(item_id):
    w = db.get_or_404(WorkItem, item_id)
    runtime.reject(w, session["user"]["name"], note=request.form.get("note", ""))
    flash("Rejected. Nothing was sent.")
    return redirect(url_for("ops.review"))


@bp.route("/item/<int:item_id>/rerun", methods=["POST"])
@role_required("ops")
def rerun(item_id):
    w = db.get_or_404(WorkItem, item_id)
    lane = request.form.get("lane")
    if lane in LANES:
        w.lane = lane
    w.state = "new"
    runtime.run(w)
    flash(f"Re-run in the {w.lane} lane: {w.state}.")
    return redirect(url_for("ops.item", item_id=w.id))


@bp.route("/item/<int:item_id>/note", methods=["POST"])
@role_required("ops")
def note(item_id):
    w = db.get_or_404(WorkItem, item_id)
    db.session.add(Message(work_item_id=w.id, direction="out", channel="note", body=request.form.get("body", ""), author=session["user"].get("title", "staff").lower(), delivered=True))
    db.session.commit()
    return redirect(url_for("ops.item", item_id=w.id))


@bp.route("/new", methods=["GET", "POST"])
@role_required("ops")
def new_item():
    """Manual intake: a call, a walk-in, a Caliber alert someone noticed."""
    if request.method == "POST":
        f = request.form
        w = runtime.inbound_portal(community_id=f.get("community_id") or "1001", unit_account_id=f.get("unit_account_id") or None, kind=f.get("kind", "call"), subject=f.get("subject", ""), body=f.get("body", ""), email=f.get("email") or None, name=f.get("name") or None, lane=f.get("lane", "cs"))
        flash(f"Logged #{w.id} in the {w.lane} lane: {w.state}.")
        return redirect(url_for("ops.item", item_id=w.id))
    return render_template("ops/new.html", lanes=LANES, communities=_communities())


@bp.route("/agents")
@role_required("ops")
def agents():
    stats = {}
    for lane in LANES:
        total = WorkItem.query.filter_by(lane=lane).count()
        done = WorkItem.query.filter_by(lane=lane, state="done").count()
        auto = WorkItem.query.filter_by(lane=lane, state="done").filter(WorkItem.reviewer.is_(None)).count()
        waiting = WorkItem.query.filter_by(lane=lane).filter(WorkItem.state.in_(["proposed", "escalated"])).count()
        stats[lane] = {"total": total, "done": done, "auto": auto, "waiting": waiting}
    return render_template("ops/agents.html", agents=AGENTS, stats=stats, shadow=current_app.config.get("SHADOW_MODE", True))


@bp.route("/threads")
@role_required("ops")
def threads():
    msgs = Message.query.order_by(Message.created_at.desc()).limit(100).all()
    return render_template("ops/threads.html", msgs=msgs)


@bp.route("/run-daily", methods=["POST"])
@role_required("ops")
def run_daily():
    counts = runtime.daily()
    flash("Daily agents ran: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return redirect(url_for("ops.review"))


@bp.route("/activity")
@role_required("ops")
def activity():
    return render_template("ops/activity.html", log=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all(), runs=AgentRun.query.order_by(AgentRun.created_at.desc()).limit(100).all())


@bp.route("/leads")
@role_required("ops")
def leads():
    from ...models import Lead
    from ...services import sales

    status = request.args.get("status")
    q = Lead.query.order_by(Lead.created_at.desc())
    if status:
        q = q.filter_by(status=status)
    rows = q.limit(200).all()
    return render_template("ops/leads.html", leads=rows, status=status or "", quote=sales.quote, proposal_url=sales.proposal_url)


@bp.route("/leads/<int:lead_id>/status", methods=["POST"])
@role_required("ops")
def lead_status(lead_id):
    from ...models import Lead

    lead = db.get_or_404(Lead, lead_id)
    lead.status = request.form.get("status", lead.status)
    db.session.commit()
    flash(f"{lead.community_name}: {lead.status}.")
    return redirect(url_for("ops.leads"))


@bp.route("/leads/<int:lead_id>/review", methods=["GET", "POST"])
@role_required("ops")
def lead_review(lead_id):
    """Free books review: the accountant's findings memo. GET edits, ?print=1 renders the one-pager, POST saves."""
    from ...models import Lead
    from ...services import sales
    from ...services.books_review import CHECKLIST, blank_review, review_from_form

    lead = db.get_or_404(Lead, lead_id)
    if request.method == "POST":
        lead.review = review_from_form(request.form, lead.review)
        if request.form.get("deliver"):
            lead.review["delivered_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
            if lead.status in ("new", "contacted", "replied"):
                lead.status = "proposal"
        db.session.commit()
        flash("Books review saved." + (" Marked delivered." if request.form.get("deliver") else ""))
        return redirect(url_for("ops.lead_review", lead_id=lead.id))
    review = lead.review or blank_review()
    if request.args.get("print"):
        return render_template("ops/books_review_memo.html", lead=lead, review=review, q=sales.quote(lead), proposal_url=sales.proposal_url(lead), booking_url=sales.booking_url())
    return render_template("ops/books_review.html", lead=lead, review=review, checklist=CHECKLIST, q=sales.quote(lead))


@bp.route("/onboarding", methods=["GET", "POST"])
@role_required("ops")
def onboarding_list():
    """Every community between signup and live, with the bank steps a person confirms."""
    from ...models import CommunityProfile
    from ...services import onboarding

    if request.method == "POST":
        prof = db.get_or_404(CommunityProfile, int(request.form.get("id")))
        intent = request.form.get("intent")
        if intent in ("accounts_opened", "startup_check_received", "final_transfer_received"):
            onboarding.bank_step(prof, intent, True, **({"confirmed_by": session["user"]["name"]}))
            flash(f"{prof.name}: {intent.replace('_', ' ')}.")
        elif intent == "go_live" and request.form.get("provider_client_id"):
            onboarding.go_live(prof, request.form["provider_client_id"].strip())
            flash(f"{prof.name} is live as Caliber client {prof.provider_client_id}.")
        return redirect(url_for("ops.onboarding_list"))
    rows = CommunityProfile.query.order_by(CommunityProfile.created_at.desc()).all()
    return render_template("ops/onboarding.html", rows=rows, progress=onboarding.progress, onboarding_url=onboarding.onboarding_url, startup_amount=onboarding.startup_amount)


@bp.route("/settings")
@role_required("ops")
def settings():
    cfg = current_app.config
    return render_template("ops/settings.html", cfg=cfg, communities=_communities(), lanes=AGENTS)
