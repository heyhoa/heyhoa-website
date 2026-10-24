import time
from collections import defaultdict, deque

from flask import Response, abort, current_app, flash, redirect, render_template, request, session, url_for

from ...extensions import db
from ...models import ContactMessage
from ...services.leads import create_lead
from . import bp
from .content import FAQS, POSTS, REVIEWS, SERVICES

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
    return render_template("marketing/index.html", reviews=REVIEWS[:3], faqs=FAQS[:4])


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
    return render_template("marketing/reviews.html", reviews=REVIEWS)


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
        db.session.add(ContactMessage(name=request.form.get("name"), email=request.form.get("email"), topic=request.form.get("topic"), message=request.form.get("message")))
        db.session.commit()
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


PUBLIC_ENDPOINTS = [
    ("marketing.index", {}, "weekly", "1.0"), ("marketing.pricing_page", {}, "weekly", "0.9"), ("marketing.services", {}, "monthly", "0.8"),
    ("marketing.service_detail", {"slug": "accounting"}, "monthly", "0.8"), ("marketing.service_detail", {"slug": "back-office"}, "monthly", "0.8"),
    ("marketing.service_detail", {"slug": "collections"}, "monthly", "0.8"), ("marketing.how_it_works", {}, "monthly", "0.8"),
    ("marketing.self_managed", {}, "monthly", "0.8"), ("marketing.compare", {}, "monthly", "0.8"), ("marketing.reviews", {}, "monthly", "0.5"),
    ("marketing.about", {}, "monthly", "0.5"), ("marketing.faq", {}, "monthly", "0.6"), ("marketing.blog", {}, "weekly", "0.6"),
    ("marketing.homeowners", {}, "monthly", "0.6"), ("marketing.realtors", {}, "monthly", "0.6"), ("marketing.quote", {}, "monthly", "0.9"),
    ("marketing.contact", {}, "yearly", "0.3"), ("marketing.privacy", {}, "yearly", "0.1"), ("marketing.terms", {}, "yearly", "0.1"),
]


@bp.route("/sitemap.xml")
def sitemap():
    urls = [(url_for(ep, _external=True, **kw), freq, pri) for ep, kw, freq, pri in PUBLIC_ENDPOINTS]
    urls += [(url_for("marketing.post", slug=s, _external=True), "monthly", "0.6") for s in POSTS]
    body = "".join(f"<url><loc>{u}</loc><changefreq>{f}</changefreq><priority>{p}</priority></url>" for u, f, p in urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'
    return Response(xml, mimetype="application/xml")


@bp.route("/robots.txt")
def robots():
    txt = f"User-agent: *\nAllow: /\nDisallow: /me/\nDisallow: /board/\nDisallow: /api/\nDisallow: /login\nDisallow: /brand\nSitemap: {url_for('marketing.sitemap', _external=True)}\n"
    return Response(txt, mimetype="text/plain")
