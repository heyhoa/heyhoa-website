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

    # Help Scout (shared inbox + tickets) and Slack
    HELPSCOUT_APP_ID = os.environ.get("HELPSCOUT_APP_ID", "")
    HELPSCOUT_APP_SECRET = os.environ.get("HELPSCOUT_APP_SECRET", "")
    HELPSCOUT_WEBHOOK_SECRET = os.environ.get("HELPSCOUT_WEBHOOK_SECRET", "")
    HELPSCOUT_MAILBOX_ID_SUPPORT = os.environ.get("HELPSCOUT_MAILBOX_ID_SUPPORT", "")
    HELPSCOUT_MAILBOX_ID_SALES = os.environ.get("HELPSCOUT_MAILBOX_ID_SALES", "")
    HELPSCOUT_ASSIGNEE_COORDINATOR = os.environ.get("HELPSCOUT_ASSIGNEE_COORDINATOR", "")
    HELPSCOUT_ASSIGNEE_ACCOUNTANT = os.environ.get("HELPSCOUT_ASSIGNEE_ACCOUNTANT", "")
    HELPSCOUT_ASSIGNEE_BOARD = os.environ.get("HELPSCOUT_ASSIGNEE_BOARD", "")
    SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
    # "alias@heyhoa.com=1001,other@heyhoa.com=1002"
    COMMUNITY_ALIASES = dict(p.split("=", 1) for p in os.environ.get("COMMUNITY_ALIASES", "").split(",") if "=" in p)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ACCOUNTING_PROVIDER = "mock"
    WTF_CSRF_ENABLED = False
