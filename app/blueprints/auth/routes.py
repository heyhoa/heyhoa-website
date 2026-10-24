"""Sign in.

Board members: email + password, then a 6-digit code by email (skipped on a device trusted within
MFA_TRUST_DAYS). Set-password links for invites and resets. One-click email actions finish after
sign-in. The pick-a-role demo login stays available while DEMO_LOGIN is on.
"""
import datetime as dt

from flask import abort, current_app, flash, redirect, render_template, request, session, url_for

from ...extensions import db
from ...integrations.mock import DEMO_BOARD, DEMO_HOMEOWNER, DEMO_OPS
from ...models import AuditLog, BoardMember, WorkItem
from ...services import accounts
from . import bp

PERSONAS = {"homeowner": DEMO_HOMEOWNER, "board": DEMO_BOARD, "ops": DEMO_OPS}
HOME = {"homeowner": "homeowner.dashboard", "board": "board.dashboard", "ops": "ops.dashboard"}


def _after_login():
    """Finish a parked one-click action, or go home."""
    token = session.pop("pending_action", None)
    if token:
        return redirect(url_for("auth.magic_action", token=token))
    return redirect(url_for("board.dashboard"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        m = accounts.find(request.form.get("email"))
        ok, err = accounts.check_password(m, request.form.get("password")) if m else (False, None)
        if not ok:
            flash(err or "No account with that email and password.", "error")
            return redirect(url_for("auth.login"))
        if accounts.device_trusted() and session.get("user", {}).get("member_id") == m.id:
            accounts.sign_in(m, mfa_done=False)
            return _after_login()
        accounts.send_code(m)
        session["pending_member_id"] = m.id
        return redirect(url_for("auth.login_code"))
    return render_template("auth/login.html", demo=current_app.config.get("DEMO_LOGIN", True))


@bp.route("/login/code", methods=["GET", "POST"])
def login_code():
    mid = session.get("pending_member_id")
    m = db.session.get(BoardMember, mid) if mid else None
    if not m:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        if request.form.get("resend"):
            accounts.send_code(m)
            flash("New code sent.")
            return redirect(url_for("auth.login_code"))
        ok, err = accounts.verify_code(m, request.form.get("code", ""))
        if not ok:
            if err and "expired" in err:
                accounts.send_code(m)
            flash(err, "error")
            return redirect(url_for("auth.login_code"))
        session.pop("pending_member_id", None)
        accounts.sign_in(m, mfa_done=True)
        db.session.add(AuditLog(actor=m.name, action="login", target=m.email, detail=request.headers.get("User-Agent", "")[:120]))
        db.session.commit()
        return _after_login()
    return render_template("auth/login_code.html", email=m.email)


@bp.route("/login/forgot", methods=["POST"])
def forgot():
    m = accounts.find(request.form.get("email"))
    if m:
        accounts.send_setup(m, reason="reset")
    flash("If that address is on a board roster, a reset link is on its way.")
    return redirect(url_for("auth.login"))


@bp.route("/set-password/<token>", methods=["GET", "POST"])
def set_password(token):
    m = accounts.read_setup(token)
    if not m:
        flash("That link has expired or was already used. Ask for a new one.", "error")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        pw, again = request.form.get("password", ""), request.form.get("again", "")
        if pw != again:
            flash("The two passwords do not match.", "error")
        else:
            try:
                accounts.set_password(m, pw)
            except ValueError as e:
                flash(str(e), "error")
            else:
                db.session.add(AuditLog(actor=m.name, action="password.set", target=m.email, detail=""))
                db.session.commit()
                flash("Password set. Sign in with it; we will email you a code.")
                return redirect(url_for("auth.login"))
    return render_template("auth/set_password.html", member=m, token=token)


@bp.route("/login/<role>", methods=["GET", "POST"])
def login_role(role):
    """Demo personas. Off in production (DEMO_LOGIN=false)."""
    if role not in PERSONAS or not current_app.config.get("DEMO_LOGIN", True):
        abort(404)
    if request.method == "POST" or request.args.get("demo"):
        session["role"] = role
        session["user"] = PERSONAS[role]
        return redirect(url_for(HOME[role]))
    return render_template("auth/login_role.html", role=role, persona=PERSONAS[role])


@bp.route("/go/<token>")
def magic_action(token):
    """One click from the email. Acts only for the signed-in member the link was sent to; otherwise sign in first, then it finishes."""
    from ...integrations.registry import get_provider
    from ...services import decisions, magic

    d, m, err = magic.read_action(token)
    if err:
        return render_template("auth/acted.html", ok=False, message=err), 400
    user = session.get("user") or {}
    if session.get("role") != "board" or user.get("member_id") != m.id:
        session["pending_action"] = token
        flash(f"Sign in as {m.name} to finish that.", "info")
        return redirect(url_for("auth.login"))
    kind, obj_id, action = d["k"], d["i"], d["a"]
    result = ""
    if kind == "invoice":
        p = get_provider()
        inv = next((i for i in p.list_invoices(m.community_id) if i.id == obj_id), None)
        if not inv:
            return render_template("auth/acted.html", ok=False, message="That bill is no longer in the queue.")
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
            return render_template("auth/acted.html", ok=False, message="That vote is no longer open.")
        if item.state != "proposed":
            result = f"{item.subject}: already {'approved' if item.state == 'done' else item.state}. Your click changed nothing."
        else:
            prior = next((v for v in (item.remote_ids or {}).get("votes", []) if v.get("member_id") == user["id"]), None)
            item = decisions.vote(item, user["id"], m.name, action, "via email link")
            yes = sum(1 for v in item.remote_ids["votes"] if v["vote"] == "approve")
            result = f"{'Updated' if prior else 'Recorded'}: you voted {action} on {item.subject}. {yes} of {decisions.spec(item.category, m.community_id)['approvals']} approvals; the decision is {item.state.replace('_', ' ')}."
    else:
        return render_template("auth/acted.html", ok=False, message="Unknown link."), 400
    return render_template("auth/acted.html", ok=True, message=result, member=m)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("marketing.index"))
