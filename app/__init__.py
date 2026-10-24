import datetime as dt

from flask import Flask, session

from .brand import ADD_ONS, ASSOCIATION_FEES, BRAND, COLLECTION_STAGES, LIEN_THRESHOLD, OWNER_FEES, PRICING
from .config import Config
from .extensions import db


def create_app(config_object=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object or Config)

    db.init_app(app)

    from .blueprints.marketing import bp as marketing_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.homeowner import bp as homeowner_bp
    from .blueprints.board import bp as board_bp
    from .blueprints.api import bp as api_bp

    app.register_blueprint(marketing_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(homeowner_bp, url_prefix="/me")
    app.register_blueprint(board_bp, url_prefix="/board")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_globals():
        return {
            "brand": BRAND,
            "pricing": PRICING,
            "add_ons": ADD_ONS,
            "association_fees": ASSOCIATION_FEES,
            "owner_fees": OWNER_FEES,
            "collection_stages": COLLECTION_STAGES,
            "lien_threshold": LIEN_THRESHOLD,
            "current_year": dt.date.today().year,
            "role": session.get("role"),
            "me": session.get("user"),
            "provider_name": app.config["ACCOUNTING_PROVIDER"],
        }

    @app.template_filter("money")
    def money(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return value
        sign = "-" if value < 0 else ""
        return f"{sign}${abs(value):,.2f}"

    @app.template_filter("money0")
    def money0(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return value
        sign = "-" if value < 0 else ""
        return f"{sign}${abs(value):,.0f}"

    @app.template_filter("datefmt")
    def datefmt(value, fmt="%b %d, %Y"):
        if isinstance(value, str):
            try:
                value = dt.date.fromisoformat(value[:10])
            except ValueError:
                return value
        if isinstance(value, (dt.date, dt.datetime)):
            return value.strftime(fmt)
        return value

    @app.cli.command("snapshot-coa")
    def snapshot_coa_cmd():
        """Nightly: copy each community's chart of accounts into coa_snapshots."""
        from .integrations.registry import get_provider
        from .services.financials import snapshot_coa

        with app.test_request_context():
            for c in get_provider().list_communities():
                print(c.name, snapshot_coa(c.id), "accounts")

    @app.cli.command("seed")
    def seed():
        """Create tables and seed demo rows."""
        from .services.seed import seed_demo

        db.create_all()
        seed_demo()
        print("seeded")

    with app.app_context():
        db.create_all()

    return app
