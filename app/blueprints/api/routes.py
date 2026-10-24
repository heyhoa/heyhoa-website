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


def _twiml(*parts: str) -> "Response":
    from flask import Response

    return Response('<?xml version="1.0" encoding="UTF-8"?><Response>' + "".join(parts) + "</Response>", mimetype="application/xml")


@bp.route("/webhooks/twilio/voice", methods=["GET", "POST"])
def twilio_voice():
    """Simple phone intake: greet, get the caller's name, the reason, confirm the callback number,
    then create a work item for the board's inbox. Twilio sends SpeechResult between steps."""
    from flask import url_for

    from ...agents import runtime

    expected = current_app.config.get("POSTMARK_INBOUND_TOKEN", "")
    if not expected or request.args.get("token") != expected:
        return _twiml("<Say>This number is not configured.</Say><Hangup/>"), 401
    step = int(request.args.get("step", 0))
    community_id = request.args.get("community") or None
    speech = (request.values.get("SpeechResult") or "").strip()
    caller = request.values.get("From", "")
    name, reason = request.args.get("name", ""), ""
    nxt = lambda s, **kw: url_for("api.twilio_voice", token=expected, step=s, community=community_id, **kw)  # noqa: E731
    if step == 0:
        return _twiml(f'<Gather input="speech" action="{nxt(1)}" method="POST" speechTimeout="auto"><Say>Hey, thanks for calling. This is the back office for your community. What is your name and your unit or address?</Say></Gather><Say>Sorry, I did not catch that.</Say><Redirect>{nxt(0)}</Redirect>')
    if step == 1:
        return _twiml(f'<Gather input="speech" action="{nxt(2, name=speech[:120])}" method="POST" speechTimeout="auto"><Say>Thanks. In a sentence or two, what can we help with?</Say></Gather><Say>Sorry, I did not catch that.</Say><Redirect>{nxt(1)}</Redirect>')
    reason = speech
    item = runtime.inbound_portal(community_id=community_id, unit_account_id=None, kind="call", subject=f"Call from {name or caller}: {reason[:80]}", body=f"Caller: {name or 'unknown'} · callback {caller}\nReason: {reason}", email=None, name=name or caller, lane="cs")
    return _twiml(f'<Say>Got it. I have passed this to the board and the hey team. Someone will follow up at the number you called from, {" ".join(caller[-4:])} being the last four digits. Thanks for calling.</Say><Hangup/>') if item else _twiml("<Say>Thanks. Goodbye.</Say><Hangup/>")


@bp.post("/leads")
def leads():
    data = request.get_json(silent=True) or request.form
    lead = create_lead(data, source=data.get("source") or "api")
    return jsonify(id=lead.id, score=lead.score), 201
