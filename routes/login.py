# ============================================================
# routes/login.py
# Devspark ERP Update Server
#
# مسؤول عن:
#
# /login
# /logout
#
# ============================================================

from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)


# ============================================================
# Blueprint
# ============================================================

login_bp = Blueprint(
    "login",
    __name__
)


# ============================================================
# Admin Credentials
# ============================================================

ADMIN_USERNAME = "beatacode"

ADMIN_PASSWORD = "ali199782"


# ============================================================
# Authentication
# ============================================================

def is_admin_logged_in():
    """
    التحقق من تسجيل دخول المدير.
    """

    return (
        session.get(
            "admin_logged_in",
            False
        )
        is True
    )


def admin_required(view_function):
    """
    حماية Routes الإدارة.
    """

    @wraps(view_function)
    def wrapped_view(
        *args,
        **kwargs
    ):

        if not is_admin_logged_in():

            next_url = request.path

            return redirect(
                url_for(
                    "login.login",
                    next=next_url
                )
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


# ============================================================
# Login
# ============================================================

@login_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # --------------------------------------------------------
    # إذا كان مسجل الدخول مسبقًا
    # --------------------------------------------------------

    if is_admin_logged_in():

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        username = (
            request.form.get(
                "username",
                ""
            )
            .strip()
        )

        password = request.form.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # التحقق
        # ----------------------------------------------------

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            # ------------------------------------------------
            # تنظيف Session القديمة
            # ------------------------------------------------

            session.clear()

            # ------------------------------------------------
            # إنشاء جلسة الإدارة
            # ------------------------------------------------

            session["admin_logged_in"] = True

            session["admin_username"] = (
                ADMIN_USERNAME
            )

            # ------------------------------------------------
            # إعادة المستخدم للصفحة المطلوبة
            # ------------------------------------------------

            next_url = request.args.get(
                "next",
                ""
            )

            if (
                next_url
                and
                next_url.startswith("/")
                and
                not next_url.startswith("//")
            ):

                return redirect(
                    next_url
                )

            return redirect(
                url_for(
                    "admin.dashboard"
                )
            )

        # ----------------------------------------------------
        # فشل الدخول
        # ----------------------------------------------------

        flash(
            "❌ اسم المستخدم أو كلمة المرور غير صحيحة."
        )

        return render_template(
            "login.html"
        ), 401

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    return render_template(
        "login.html"
    )


# ============================================================
# Logout
# ============================================================

@login_bp.route(
    "/logout",
    methods=["GET", "POST"]
)
def logout():

    session.clear()

    flash(
        "👋 تم تسجيل الخروج من لوحة الإدارة."
    )

    return redirect(
        url_for(
            "login.login"
        )
    )
