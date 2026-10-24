"""Demo authentication.

Phase 2 replaces this with magic-link email auth (and FrontSteps
`/api/v2/login` validation when the provider is frontsteps). For mock-ups we
let a visitor pick a role and sign in as a demo persona.
"""
from flask import abort, redirect, render_template, request, session, url_for

from ...integrations.mock import DEMO_BOARD, DEMO_HOMEOWNER
from . import bp

PERSONAS = {"homeowner": DEMO_HOMEOWNER, "board": DEMO_BOARD}


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
        return redirect(url_for("homeowner.dashboard" if role == "homeowner" else "board.dashboard"))
    return render_template("auth/login_role.html", role=role, persona=PERSONAS[role])


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("marketing.index"))
