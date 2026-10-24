import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.blueprints.marketing import routes

    routes._RATE.clear()
    yield
    routes._RATE.clear()
