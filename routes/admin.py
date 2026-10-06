# routes/admin.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Admin


# ============================================================
# Admin Blueprint
# ============================================================

admin = Blueprint(
    "admin",
    __name__
)


# ============================================================
# Admin Login
# URL:
# /admin/login
# ============================================================

@admin.route("/login", methods=["GET", "POST"])
def login():

    # إذا كان المدير مسجل دخول مسبقًا
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # التحقق من البيانات
        if not username or not password:
            flash("يرجى إدخال اسم المستخدم وكلمة المرور.", "error")
            return render_template("admin/admin_login.html")

        # البحث عن المدير
        admin_user = Admin.query.filter_by(
            username=username
        ).first()

        # التحقق من كلمة المرور
        if admin_user and admin_user.password == password:

            # إنشاء جلسة المدير
            session["admin_logged_in"] = True
            session["admin_id"] = admin_user.id
            session["admin_username"] = admin_user.username

            # الانتقال إلى لوحة التحكم
            return redirect(url_for("admin.dashboard"))

        # بيانات الدخول غير صحيحة
        flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "error")

    return render_template("admin/admin_login.html")


# ============================================================
# Admin Dashboard
# URL:
# /admin/dashboard
# ============================================================

@admin.route("/dashboard")
def dashboard():

    # التأكد من تسجيل دخول المدير
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.login"))

    return render_template(
        "admin/admin_dashboard.html"
    )


# ============================================================
# Admin Uploads
# URL:
# /admin/uploads
# ============================================================

@admin.route("/uploads", methods=["GET", "POST"])
def uploads():

    # التأكد من تسجيل دخول المدير
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        # ====================================================
        # هنا نضع منطق رفع الملفات الموجود لديك حاليًا
        # ====================================================

        flash("تم استقبال طلب رفع الملف.", "success")

        return redirect(
            url_for("admin.uploads")
        )

    return render_template(
        "admin/admin_uploads.html"
    )


# ============================================================
# Admin Logout
# URL:
# /admin/logout
# ============================================================

@admin.route("/logout")
def logout():

    # حذف بيانات جلسة المدير
    session.pop("admin_logged_in", None)
    session.pop("admin_id", None)
    session.pop("admin_username", None)

    flash("تم تسجيل الخروج بنجاح.", "success")

    return redirect(
        url_for("admin.login")
    )
