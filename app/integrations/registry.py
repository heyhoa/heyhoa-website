from flask import current_app, g

from .base import AccountingProvider


def get_provider() -> AccountingProvider:
    """Per-request provider instance, selected by ACCOUNTING_PROVIDER."""
    if "provider" not in g:
        kind = current_app.config.get("ACCOUNTING_PROVIDER", "mock")
        if kind == "frontsteps":
            from .frontsteps import FrontStepsProvider

            g.provider = FrontStepsProvider(
                base_url=current_app.config["FRONTSTEPS_BASE_URL"],
                api_key=current_app.config["FRONTSTEPS_API_KEY"],
                username=current_app.config.get("FRONTSTEPS_USERNAME") or None,
                password=current_app.config.get("FRONTSTEPS_PASSWORD") or None,
            )
        else:
            from .mock import MockProvider

            g.provider = MockProvider()
    return g.provider
