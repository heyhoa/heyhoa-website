"""Demo authentication.

Phase 2 replaces this with magic-link email auth (and FrontSteps
`/api/v2/login` validation when the provider is frontsteps). For mock-ups we
let a visitor pick a role and sign in as a demo persona.
"""
from flask import abort, flash, redirect, render_template, request, session, url_for

from ...extensions import db
from ...models import AuditLog, BoardMember

from ...integrations.mock import DEMO_BOARD, DEMO_HOMEOWNER, DEMO_OPS
from . import bp

PERSONAS = {"homeowner": DEMO_HOMEOWNER, "board": DEMO_BOARD, "ops": DEMO_OPS}
HOME = {"homeowner": "homeowner.dashboard", "board": "board.dashboard", "ops": "ops.dashboard"}


@bp.route("/login")
def login():
    return render_template("auth/login.html")


@bp.route("/login/<role>", methods=["GET", "POST"])
def login_role(role):
    if role not in PERSONAS:
        abort(404)
    if request.method == "POST" or request.args.get("demo"):
        session["role"] = role
        session["user"] = PERSONAS[role]
        return redirect(url_for(HOME[role]))
    return render_template("auth/login_role.html", role=role, persona=PERSONAS[role])


@bp.route("/login/email", methods=["POST"])
def login_email():
    """Email me a link. Same reply whether or not the address is on a roster."""
    from ...services import board_mail

    email = (request.form.get("email") or "").strip().lower()
    m = BoardMember.query.filter(db.func.lower(BoardMember.email) == email, BoardMember.active.is_(True)).first() if email else None
    if m:
        board_mail.send_login_link(m)
    flash("If that address is on a board roster, a link is on its way. It works for 7 days.")
    return redirect(url_for("auth.login"))


@bp.route("/login/magic/<token>")
def magic_login(token):
    from ...services import magic

    m = magic.read_login(token)
    if not m:
        flash("That link has expired or is not valid. Ask for a new one.", "error")
        return redirect(url_for("auth.login"))
    session["role"] = "board"
    session["user"] = magic.session_user(m)
    return redirect(url_for("board.dashboard"))


@bp.route("/go/<token>")
def magic_action(token):
    """One click from the email: approve or reject a bill, approve or deny a vote. Idempotent."""
    from ...integrations.registry import get_provider
    from ...models import WorkItem
    from ...services import decisions, magic

    d, m, err = magic.read_action(token)
    if err:
        return render_template("auth/acted.html", ok=False, message=err, login_url=None), 400
    user = magic.session_user(m)
    kind, obj_id, action = d["k"], d["i"], d["a"]
    result = ""
    if kind == "invoice":
        p = get_provider()
        inv = next((i for i in p.list_invoices(m.community_id) if i.id == obj_id), None)
        if not inv:
            return render_template("auth/acted.html", ok=False, message="That bill is no longer in the queue.", login_url=magic.login_url(m))
        already = AuditLog.query.filter_by(actor=m.name, target=obj_id).filter(AuditLog.action.like("invoice.%")).first()
        if inv.status != "pending_board" or already:
            result = f"{inv.vendor} #{inv.number} is already {inv.status.replace('_', ' ')}{' and your action is recorded' if already else ''}. Nothing changed."
        else:
            inv = p.act_on_invoice(obj_id, user["id"], action, "via email link")
            db.session.add(AuditLog(actor=m.name, action=f"invoice.{action}", target=obj_id, detail=f"{inv.vendor} {inv.number} ${inv.amount:,.2f} (email link)"))
            db.session.commit()
            result = f"{'Approved' if action == 'approve' else 'Rejected'}: {inv.vendor} #{inv.number} ${inv.amount:,.2f}. Now {inv.approvals} of {inv.approvals_required} approvals."
    elif kind == "decision":
        item = db.session.get(WorkItem, int(obj_id))
        if not item or item.community_id != m.community_id or item.kind != "decision":
            return render_template("auth/acted.html", ok=False, message="That vote is no longer open.", login_url=magic.login_url(m))
        if item.state != "proposed":
            result = f"{item.subject}: already {'approved' if item.state == 'done' else item.state}. Your click changed nothing."
        else:
            prior = next((v for v in (item.remote_ids or {}).get("votes", []) if v.get("member_id") == user["id"]), None)
            item = decisions.vote(item, user["id"], m.name, action, "via email link")
            yes = sum(1 for v in item.remote_ids["votes"] if v["vote"] == "approve")
            result = f"{'Updated' if prior else 'Recorded'}: you voted {action} on {item.subject}. {yes} of {decisions.spec(item.category, m.community_id)['approvals']} approvals; the decision is {item.state.replace('_', ' ')}."
    else:
        return render_template("auth/acted.html", ok=False, message="Unknown link.", login_url=None), 400
    return render_template("auth/acted.html", ok=True, message=result, login_url=magic.login_url(m), member=m)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("marketing.index"))
