import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'heyhoa.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ACCOUNTING_PROVIDER = os.environ.get("ACCOUNTING_PROVIDER", "mock")
    FRONTSTEPS_BASE_URL = os.environ.get(
        "FRONTSTEPS_BASE_URL", "https://frontsteps.cloud/CAPI2_APISandbox"
    )
    FRONTSTEPS_API_KEY = os.environ.get("FRONTSTEPS_API_KEY", "")
    FRONTSTEPS_USERNAME = os.environ.get("FRONTSTEPS_USERNAME", "")
    FRONTSTEPS_PASSWORD = os.environ.get("FRONTSTEPS_PASSWORD", "")

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    HEY_AI_MODEL = os.environ.get("HEY_AI_MODEL", "claude-opus-5-5")

    LEAD_NOTIFY_EMAIL = os.environ.get("LEAD_NOTIFY_EMAIL", "hello@heyhoa.com")

    # Transports: Postmark (email), Twilio (SMS), Slack (internal pings)
    POSTMARK_SERVER_TOKEN = os.environ.get("POSTMARK_SERVER_TOKEN", "")
    POSTMARK_INBOUND_TOKEN = os.environ.get("POSTMARK_INBOUND_TOKEN", "")  # shared secret in the inbound webhook URL
    POSTMARK_FROM = os.environ.get("POSTMARK_FROM", "hey@heyhoa.com")
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM = os.environ.get("TWILIO_FROM", "")
    SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

    # Agent policy. Shadow mode: every proposal waits for a person.
    SHADOW_MODE = os.environ.get("SHADOW_MODE", "true").lower() != "false"
    LIVE_COMMUNITIES = [c for c in os.environ.get("LIVE_COMMUNITIES", "").split(",") if c]
    AUTO_CONFIDENCE = float(os.environ.get("AUTO_CONFIDENCE", "0.8"))
    # "alias@heyhoa.com=1001,other@heyhoa.com=1002"
    COMMUNITY_ALIASES = dict(p.split("=", 1) for p in os.environ.get("COMMUNITY_ALIASES", "").split(",") if "=" in p)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ACCOUNTING_PROVIDER = "mock"
    WTF_CSRF_ENABLED = False
