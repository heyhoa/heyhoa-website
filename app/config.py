import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    _db_url = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'heyhoa.db'}")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
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
    # Sales identity: sequence A and proposals go out as the founder, replies come back to the founder.
    FOUNDER_NAME = os.environ.get("FOUNDER_NAME", "Austin Heywood")
    FOUNDER_FIRST = os.environ.get("FOUNDER_FIRST", "Austin")
    FOUNDER_TITLE = os.environ.get("FOUNDER_TITLE", "founder, hey hoa")
    FOUNDER_EMAIL = os.environ.get("FOUNDER_EMAIL", "austin@heyhoa.com")
    BOOKING_URL = os.environ.get("BOOKING_URL", "https://cal.com/heyhoa/15min")  # 15-minute board walkthrough

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
    MCP_PUBLIC_URL = os.environ.get("MCP_PUBLIC_URL", "https://mcp.heyhoa.com/mcp")
    # Partner bank. Money moves ONLY here, by a person. Boards use it for signature cards and statements.
    BANK_NAME = os.environ.get("BANK_NAME", "First Citizens Bank")
    BANK_PORTAL_NAME = os.environ.get("BANK_PORTAL_NAME", "Client Connect")
    BANK_PORTAL_URL = os.environ.get("BANK_PORTAL_URL", "https://www.firstcitizens.com/cab")
    STARTUP_CHECK_MIN = int(os.environ.get("STARTUP_CHECK_MIN", "2500"))  # opening deposit floor for the new operating account
    LOCKBOX_ADDRESS = os.environ.get("LOCKBOX_ADDRESS", "hey hoa · PO Box 00000 · Phoenix, AZ 85000")
    # Physical mail (Lob). Unset = letters are recorded and printed by a person.
    LOB_API_KEY = os.environ.get("LOB_API_KEY", "")
    LOB_FROM_ADDRESS = os.environ.get("LOB_FROM_ADDRESS", "")  # Lob address id for the return address
    LETTER_COST = float(os.environ.get("LETTER_COST", "1.45"))  # pass-through per first-class letter
    # Where boards buy a cyber policy. Our terms say account access and actions are theirs.
    CYBER_INSURANCE_URL = os.environ.get("CYBER_INSURANCE_URL", "https://www.coalitioninc.com/")
    AGREEMENT_VERSION = os.environ.get("AGREEMENT_VERSION", "2026-10")
    # "alias@heyhoa.com=1001,other@heyhoa.com=1002"
    COMMUNITY_ALIASES = dict(p.split("=", 1) for p in os.environ.get("COMMUNITY_ALIASES", "").split(",") if "=" in p)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ACCOUNTING_PROVIDER = "mock"
    WTF_CSRF_ENABLED = False
