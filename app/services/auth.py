from functools import wraps

from flask import abort, redirect, session, url_for


def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            role = session.get("role")
            if not role:
                return redirect(url_for("auth.login", next=1))
            if roles and role not in roles:
                abort(403)
            return fn(*a, **kw)

        return wrapper

    return deco
