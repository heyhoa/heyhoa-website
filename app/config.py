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


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ACCOUNTING_PROVIDER = "mock"
    WTF_CSRF_ENABLED = False
