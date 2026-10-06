
from flask import render_template, redirect, url_for, session

from routes.admin import admin


# ============================================================
# Admin Dashboard
# ============================================================

@admin.route("/dashboard")
def dashboard():

    # منع الدخول بدون تسجيل دخول
    if not session.get("admin_logged_in"):
        return redirect(
            url_for("admin.login")
        )

    return render_template(
        "admin/admin_dashboard.html"
    )
