
from flask import render_template, request, redirect, url_for, session, flash

from models import Admin

from routes.admin import admin


# ============================================================
# Admin Login
# ============================================================

@admin.route("/login", methods=["GET", "POST"])
def login():

    # إذا كان المدير مسجل دخول بالفعل
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # التحقق من الحقول
        if not username or not password:
            flash(
                "يرجى إدخال اسم المستخدم وكلمة المرور.",
                "error"
            )

            return render_template(
                "admin/admin_login.html"
            )

        # البحث عن المدير
        admin_user = Admin.query.filter_by(
            username=username
        ).first()

        # التحقق من بيانات الدخول
        if admin_user and admin_user.password == password:

            session["admin_logged_in"] = True
            session["admin_id"] = admin_user.id
            session["admin_username"] = admin_user.username

            return redirect(
                url_for("admin.dashboard")
            )

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

    session.pop("admin_logged_in", None)
    session.pop("admin_id", None)
    session.pop("admin_username", None)

    flash(
        "تم تسجيل الخروج بنجاح.",
        "success"
    )

    return redirect(
        url_for("admin.login")
    )
