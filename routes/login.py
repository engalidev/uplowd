# ============================================================
# login.py
# Devspark ERP - Admin Authentication
# ============================================================

import os
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


# ============================================================
# Blueprint
# ============================================================

login_bp = Blueprint(
    "login",
    __name__
)


# ============================================================
# Admin credentials
# ============================================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "beatacode"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "ali199782"
)


# ============================================================
# Authentication decorator
# ============================================================

def admin_required(view):
    """
    حماية صفحات الإدارة.

    إذا لم يكن الأدمن مسجل الدخول:
        يتم تحويله إلى صفحة تسجيل الدخول.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get(
            "admin_logged_in",
            False
        ):
            return redirect(
                url_for("login.login")
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped


# ============================================================
# Login
# ============================================================

@login_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if session.get(
        "admin_logged_in",
        False
    ):
        return redirect(
            url_for("admin.dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session.clear()

            session["admin_logged_in"] = True
            session["admin_username"] = username

            return redirect(
                url_for("admin.dashboard")
            )

        flash(
            "❌ اسم المستخدم أو كلمة المرور غير صحيحة."
        )

    return render_template(
        "admin_login.html"
    )


# ============================================================
# Logout
# ============================================================

@login_bp.route("/logout")
def logout():

    session.clear()

    flash(
        "تم تسجيل الخروج بنجاح."
    )

    return redirect(
        url_for("login.login")
    )
