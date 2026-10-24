import time
from collections import defaultdict, deque

from flask import Response, abort, current_app, flash, redirect, render_template, request, session, url_for

from ...extensions import db
from ...models import ContactMessage
from ...services.leads import create_lead
from . import bp
from .content import FAQS, POSTS, REVIEWS, SERVICES, TRUST

_RATE: dict[str, deque] = defaultdict(deque)
RATE_LIMIT = (5, 3600)  # 5 submissions per IP per hour

UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign")


def _rate_limited(key: str) -> bool:
    n, window = RATE_LIMIT
    now = time.time()
    q = _RATE[key]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= n:
        return True
    q.append(now)
    return False


def _is_bot(form) -> bool:
    """Honeypot: real people never fill the hidden 'website' field."""
    return bool(form.get("website"))


@bp.before_app_request
def remember_utm():
    """First-touch attribution: stash UTM params and referrer in the session."""
    if request.endpoint and request.endpoint.startswith("static"):
        return
    if any(k in request.args for k in UTM_KEYS) and "utm" not in session:
        session["utm"] = {k: request.args.get(k, "")[:120] for k in UTM_KEYS}
    if "referrer" not in session and request.referrer and request.host not in request.referrer:
        session["referrer"] = request.referrer[:300]


@bp.route("/")
def index():
    return render_template("marketing/index.html", reviews=REVIEWS[:3], trust=TRUST, faqs=FAQS[:4])


@bp.route("/pricing")
def pricing_page():
    return render_template("marketing/pricing.html", faqs=FAQS)


@bp.route("/services")
def services():
    return render_template("marketing/services.html", services=SERVICES)


@bp.route("/services/<slug>")
def service_detail(slug):
    svc = SERVICES.get(slug)
    if not svc:
        abort(404)
    return render_template("marketing/service_detail.html", svc=svc, slug=slug, services=SERVICES)


@bp.route("/how-it-works")
def how_it_works():
    return render_template("marketing/how_it_works.html")


@bp.route("/self-managed")
def self_managed():
    return render_template("marketing/self_managed.html")


@bp.route("/compare")
def compare():
    return render_template("marketing/compare.html")


@bp.route("/reviews")
def reviews():
    return render_template("marketing/reviews.html", reviews=REVIEWS, trust=TRUST)


@bp.route("/proposal/<token>", methods=["GET", "POST"])
def proposal(token):
    from ...agents import runtime
    from ...models import Lead
    from ...services import sales

    lead_id = sales.lead_id_from_token(token)
    lead = db.session.get(Lead, lead_id) if lead_id else None
    if not lead:
        abort(404)
    q = sales.quote(lead)
    if request.method == "POST":
        lead.status = "accepted"
        db.session.commit()
        runtime.inbound_portal(community_id=None, unit_account_id=None, kind="lead_accepted", subject=f"Proposal accepted: {lead.community_name}", body=f"{lead.contact_name} accepted {q['tier']['name']} at ${q['monthly']:,}/mo. Send the agreement and the onboarding document list.", email=lead.email, name=lead.contact_name, lane="sales")
        flash("Thank you. We will send the agreement and the onboarding checklist within one business day.")
        return redirect(url_for("marketing.proposal", token=token))
    return render_template("marketing/proposal.html", lead=lead, q=q, calendar=sales.onboarding_calendar(), token=token)


@bp.route("/books-review", methods=["GET", "POST"])
def books_review():
    """Free books review: three statements in, a one-page findings memo out within two business days."""
    if request.method == "POST":
        if _is_bot(request.form) or _rate_limited(request.remote_addr or "?"):
            return redirect(url_for("marketing.books_review"))
        import os

        from ...agents import runtime

        data = request.form.to_dict()
        data["pain_points"] = "books review"
        data["current_setup"] = data.get("current_setup") or "self"
        lead = create_lead(data, source="books-review")
        names = []
        updir = os.path.join(current_app.instance_path, "uploads", f"lead-{lead.id}")
        os.makedirs(updir, exist_ok=True)
        for f in request.files.getlist("files"):
            if f and f.filename:
                safe = "".join(ch for ch in f.filename if ch.isalnum() or ch in "._- ")[:120]
                f.save(os.path.join(updir, safe))
                names.append(safe)
        runtime.inbound_portal(community_id=None, unit_account_id=None, kind="books_review", subject=f"Free books review: {lead.community_name} · {lead.units} doors", body=f"Files: {', '.join(names) or 'none uploaded (will email)'}\nNotes: {data.get('notes') or '-'}", email=lead.email, name=lead.contact_name, lane="sales")
        return redirect(url_for("marketing.quote_thanks", review=1))
    return render_template("marketing/books_review.html")


@bp.route("/about")
def about():
    return render_template("marketing/about.html")


@bp.route("/faq")
def faq():
    return render_template("marketing/faq.html", faqs=FAQS)


@bp.route("/blog")
def blog():
    posts = sorted(POSTS.items(), key=lambda kv: kv[1]["date"], reverse=True)
    return render_template("marketing/blog.html", posts=posts)


@bp.route("/blog/<slug>")
def post(slug):
    p = POSTS.get(slug)
    if not p:
        abort(404)
    return render_template("marketing/post.html", post=p, slug=slug)


@bp.route("/homeowners")
def homeowners():
    return render_template("marketing/homeowners.html")


@bp.route("/realtors")
def realtors():
    return render_template("marketing/realtors.html")


@bp.route("/quote", methods=["GET", "POST"])
def quote():
    if request.method == "POST":
        if _is_bot(request.form):
            return redirect(url_for("marketing.quote_thanks"))  # silently drop
        if _rate_limited(request.remote_addr or "?"):
            flash("Too many submissions from this network. Email us instead: " + current_app.config["LEAD_NOTIFY_EMAIL"], "error")
            return redirect(url_for("marketing.quote"))
        data = request.form.to_dict(flat=False)
        data = {k: (v if k == "pain_points" else v[0]) for k, v in data.items()}
        data["pain_points"] = ",".join(request.form.getlist("pain_points"))
        utm = session.get("utm", {})
        data.update({k: utm.get(k) for k in UTM_KEYS})
        data["referrer"] = session.get("referrer")
        lead = create_lead(data, source=utm.get("utm_source") or session.get("referrer") or "direct")
        return redirect(url_for("marketing.quote_thanks", lead_id=lead.id))
    return render_template("marketing/quote.html", plan=request.args.get("plan", ""))


@bp.route("/quote/thanks")
def quote_thanks():
    return render_template("marketing/quote_thanks.html")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        if _is_bot(request.form):
            return redirect(url_for("marketing.contact"))
        if _rate_limited(request.remote_addr or "?"):
            flash("Too many messages from this network. Email us instead: " + current_app.config["LEAD_NOTIFY_EMAIL"], "error")
            return redirect(url_for("marketing.contact"))
        msg = ContactMessage(name=request.form.get("name"), email=request.form.get("email"), topic=request.form.get("topic"), message=request.form.get("message"))
        db.session.add(msg)
        db.session.commit()
        try:
            from ...services.notify import deliver_contact_message

            deliver_contact_message(msg)
        except Exception as e:  # noqa: BLE001
            current_app.logger.warning("contact delivery failed: %s", e)
        flash("Got it. A person will reply within one business day.")
        return redirect(url_for("marketing.contact"))
    return render_template("marketing/contact.html")


@bp.route("/privacy")
def privacy():
    return render_template("marketing/legal.html", title="Privacy policy", kind="privacy")


@bp.route("/terms")
def terms():
    return render_template("marketing/legal.html", title="Terms of service", kind="terms")


@bp.route("/brand")
def brand_page():
    return render_template("marketing/brand.html")


@bp.route("/sample-packet")
def sample_packet():
    """HTML source of the sample financial packet; scripts/build_sample_packet.js prints it to PDF."""
    from ...integrations.mock import MockProvider

    p = MockProvider()
    return render_template(
        "marketing/sample_packet.html", community=p.get_community("1001"), snap=p.get_financial_snapshot("1001"),
        coa=p.get_chart_of_accounts("1001"), invoices=p.list_invoices("1001"), delinquencies=p.list_delinquencies("1001"),
    )


@bp.route("/c/<slug>")
def community_page(slug):
    from ...services.public_data import community_public

    data = community_public(slug)
    if not data:
        abort(404)
    return render_template("marketing/community.html", c=data)


@bp.route("/c/<slug>.json")
def community_json(slug):
    from flask import jsonify

    from ...services.public_data import community_public

    data = community_public(slug)
    if not data:
        abort(404)
    return jsonify(data)


@bp.route("/c/<slug>/records-request", methods=["GET", "POST"])
def records_request(slug):
    from ...agents import runtime
    from ...services.public_data import community_public

    data = community_public(slug)
    if not data:
        abort(404)
    if request.method == "POST":
        if _is_bot(request.form) or _rate_limited(request.remote_addr or "?"):
            return redirect(url_for("marketing.records_request", slug=slug))
        f = request.form
        body = f"Records requested: {f.get('records')}\nPurpose: {f.get('purpose') or '—'}\nFormat: {f.get('format')}\nRequester states they are: {f.get('relationship')} of {f.get('unit') or 'unspecified unit'}"
        item = runtime.inbound_portal(community_id=data["id"], unit_account_id=None, kind="records_request", subject=f"Records request from {f.get('name')}", body=body, email=f.get("email"), name=f.get("name"), lane="cs")
        flash(f"Request #{item.id} received. Under {data['records_policy']['statute'] if data.get('records_policy') else 'the governing documents'}, the association has {data['records_policy']['business_days'] if data.get('records_policy') else 10} business days. We will confirm your membership and respond by email.")
        return redirect(url_for("marketing.community_page", slug=slug))
    return render_template("marketing/records_request.html", c=data)


@bp.route("/.well-known/hey-agent.json")
def agent_discovery():
    from flask import jsonify

    from ...services.public_data import discovery

    return jsonify(discovery())


PUBLIC_ENDPOINTS = [
    ("marketing.index", {}, "weekly", "1.0"), ("marketing.pricing_page", {}, "weekly", "0.9"), ("marketing.services", {}, "monthly", "0.8"),
    ("marketing.service_detail", {"slug": "accounting"}, "monthly", "0.8"), ("marketing.service_detail", {"slug": "back-office"}, "monthly", "0.8"),
    ("marketing.service_detail", {"slug": "collections"}, "monthly", "0.8"), ("marketing.how_it_works", {}, "monthly", "0.8"),
    ("marketing.self_managed", {}, "monthly", "0.8"), ("marketing.compare", {}, "monthly", "0.8"), ("marketing.reviews", {}, "monthly", "0.5"),
    ("marketing.about", {}, "monthly", "0.5"), ("marketing.faq", {}, "monthly", "0.6"), ("marketing.blog", {}, "weekly", "0.6"),
    ("marketing.homeowners", {}, "monthly", "0.6"), ("marketing.realtors", {}, "monthly", "0.6"), ("marketing.quote", {}, "monthly", "0.9"), ("marketing.books_review", {}, "monthly", "0.9"),
    ("marketing.contact", {}, "yearly", "0.3"), ("marketing.privacy", {}, "yearly", "0.1"), ("marketing.terms", {}, "yearly", "0.1"),
]


@bp.route("/sitemap.xml")
def sitemap():
    urls = [(url_for(ep, _external=True, **kw), freq, pri) for ep, kw, freq, pri in PUBLIC_ENDPOINTS]
    urls += [(url_for("marketing.post", slug=s, _external=True), "monthly", "0.6") for s in POSTS]
    from ...services.public_data import SLUGS

    urls += [(url_for("marketing.community_page", slug=s, _external=True), "weekly", "0.7") for s in SLUGS]
    body = "".join(f"<url><loc>{u}</loc><changefreq>{f}</changefreq><priority>{p}</priority></url>" for u, f, p in urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'
    return Response(xml, mimetype="application/xml")


@bp.route("/robots.txt")
def robots():
    txt = f"User-agent: *\nAllow: /\nDisallow: /me/\nDisallow: /board/\nDisallow: /api/\nDisallow: /login\nDisallow: /brand\nDisallow: /sample-packet\nSitemap: {url_for('marketing.sitemap', _external=True)}\n"
    return Response(txt, mimetype="text/plain")
