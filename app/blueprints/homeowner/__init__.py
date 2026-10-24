from flask import Blueprint

bp = Blueprint("homeowner", __name__)

from . import routes  # noqa: E402,F401
