from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from routes.admin import admin


# ============================================================
# Admin Home
# /admin
# ============================================================

@admin.route("/")
def admin_home():

    # إذا كان المدير مسجل دخول
    if session.get("admin_logged_in"):
        return redirect(
            url_for("admin.dashboard")
        )

    # إذا لم يكن مسجل دخول
    return redirect(
        url_for("admin.login")
    )


# ============================================================
# Admin Login
# /admin/login
# ============================================================

@admin.route("/login", methods=["GET", "POST"])
def login():

    # --------------------------------------------------------
    # إذا كان المدير مسجل دخول بالفعل
    # --------------------------------------------------------

    if session.get("admin_logged_in"):
        return redirect(
            url_for("admin.dashboard")
        )

    # --------------------------------------------------------
    # معالجة تسجيل الدخول
    # --------------------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # ====================================================
        # Admin Credentials
        # ====================================================

        ADMIN_USERNAME = "betacode"
        ADMIN_PASSWORD = "ali1234"

        # ====================================================
        # Check Login
        # ====================================================

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            # إنشاء جلسة المدير
            session["admin_logged_in"] = True
            session["admin_username"] = username

            # الانتقال إلى لوحة التحكم
            return redirect(
                url_for("admin.dashboard")
            )

        # ====================================================
        # Invalid Login
        # ====================================================

        flash(
            "اسم المستخدم أو كلمة المرور غير صحيحة.",
            "error"
        )

    # ========================================================
    # Login Page
    # ========================================================

    return render_template(
        "admin/admin_login.html"
    )


# ============================================================
# Admin Logout
# /admin/logout
# ============================================================

@admin.route("/logout")
def logout():

    # حذف حالة تسجيل الدخول
    session.pop(
        "admin_logged_in",
        None
    )

    # حذف اسم المستخدم
    session.pop(
        "admin_username",
        None
    )

    # العودة إلى صفحة تسجيل الدخول
    return redirect(
        url_for("admin.login")
    )
