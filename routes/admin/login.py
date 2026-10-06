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
# Admin Login
# ============================================================

@admin.route("/login", methods=["GET", "POST"])
def login():

    # إذا كان المدير مسجل دخول بالفعل
    if session.get("admin_logged_in"):
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

            session["admin_logged_in"] = True
            session["admin_username"] = username

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

    return render_template(
        "admin/admin_login.html"
    )


# ============================================================
# Admin Logout
# ============================================================

@admin.route("/logout")
def logout():

    session.pop(
        "admin_logged_in",
        None
    )

    session.pop(
        "admin_username",
        None
    )

    return redirect(
        url_for("admin.login")
    )
