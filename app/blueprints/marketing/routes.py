from flask import abort, current_app, flash, redirect, render_template, request, url_for

from ...extensions import db
from ...models import ContactMessage
from ...services.leads import create_lead
from . import bp
from .content import FAQS, POSTS, REVIEWS, SERVICES


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
        lead = create_lead(request.form, source=request.args.get("utm_source") or request.referrer)
        return redirect(url_for("marketing.quote_thanks", lead_id=lead.id))
    return render_template("marketing/quote.html")


@bp.route("/quote/thanks")
def quote_thanks():
    return render_template("marketing/quote_thanks.html")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
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
