from flask import Blueprint

bp = Blueprint("marketing", __name__)

from . import routes  # noqa: E402,F401
