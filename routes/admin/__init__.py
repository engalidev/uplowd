from functools import wraps

from flask import Blueprint, jsonify, redirect, request, session, url_for

admin = Blueprint("admin", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped


def ajax_redirect(url):
    """للرفع عبر XHR: نعيد JSON ليعيد المتصفح التوجيه ويظهر رسالة flash."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(redirect=url)
    return redirect(url)


from routes.admin import login, dashboard, programs  # noqa: E402,F401
