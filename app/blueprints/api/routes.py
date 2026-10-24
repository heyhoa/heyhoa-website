"""JSON endpoints used by the front end and by outreach automation."""
from flask import current_app, jsonify, request, session

from ...ai.assistant import ask as ai_ask
from ...integrations.registry import get_provider
from ...services.leads import create_lead
from . import bp


@bp.get("/health")
def health():
    return jsonify(ok=True, provider=current_app.config["ACCOUNTING_PROVIDER"], ai="live" if current_app.config.get("ANTHROPIC_API_KEY") else "demo")


@bp.get("/provider/ping")
def provider_ping():
    p = get_provider()
    try:
        communities = p.list_communities()
        return jsonify(ok=True, provider=p.name, communities=[c.name for c in communities])
    except Exception as e:  # noqa: BLE001
        return jsonify(ok=False, provider=p.name, error=str(e)), 502


@bp.post("/ask")
def ask():
    data = request.get_json(silent=True) or {}
    q = (data.get("q") or "").strip()
    if not q:
        return jsonify(error="empty question"), 400
    role = session.get("role", "visitor")
    user = session.get("user") or {}
    answer = ai_ask(q, role=role, context=data.get("context", ""), user=user)
    return jsonify(answer=answer)


@bp.post("/webhooks/postmark")
def postmark_inbound():
    """Postmark inbound email → work item → agent. The URL carries a shared token."""
    from ...agents import runtime

    expected = current_app.config.get("POSTMARK_INBOUND_TOKEN", "")
    if not expected or request.args.get("token") != expected:
        return jsonify(error="bad token"), 401
    payload = request.get_json(silent=True) or {}
    item = runtime.inbound_email(payload)
    return jsonify(work_item=item.id, lane=item.lane, state=item.state, action=(item.proposal or {}).get("action"))


@bp.post("/agents/daily")
def agents_daily():
    """Cron hook: POST with the inbound token to run the scheduled agents."""
    from ...agents import runtime

    expected = current_app.config.get("POSTMARK_INBOUND_TOKEN", "")
    if not expected or request.args.get("token") != expected:
        return jsonify(error="bad token"), 401
    return jsonify(runtime.daily(request.args.get("community")))


@bp.post("/leads")
def leads():
    data = request.get_json(silent=True) or request.form
    lead = create_lead(data, source=data.get("source") or "api")
    return jsonify(id=lead.id, score=lead.score), 201
