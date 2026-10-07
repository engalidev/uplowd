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
# STARTUP DIAGNOSTIC
# ============================================================

print("")
print("=" * 70)
print("DEVSPARK ADMIN LOGIN MODULE")
print("=" * 70)

print("")
print("[LOGIN] login.py loaded successfully.")

print("")
print("[LOGIN] Module information:")
print("   Module name:")
print(__name__)

print("")
print("[LOGIN] Admin blueprint:")
print("   Blueprint name:")
print(admin.name)

print("")
print("=" * 70)
print("DEVSPARK ADMIN LOGIN ROUTES READY")
print("=" * 70)
print("")


# ============================================================
# Admin Home
# /admin
# ============================================================

@admin.route("/")
def admin_home():

    print("")
    print("=" * 70)
    print("ADMIN HOME REQUEST")
    print("=" * 70)

    print("")
    print("[ADMIN HOME] Request received.")

    print("")
    print("[ADMIN HOME] Session:")
    print(
        "   admin_logged_in =",
        session.get("admin_logged_in")
    )

    # --------------------------------------------------------
    # إذا كان المدير مسجل دخول
    # --------------------------------------------------------

    if session.get("admin_logged_in"):

        print("")
        print(
            "[ADMIN HOME] Admin is already logged in."
        )

        print(
            "[ADMIN HOME] Redirecting to dashboard..."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    # --------------------------------------------------------
    # إذا لم يكن مسجل دخول
    # --------------------------------------------------------

    print("")
    print(
        "[ADMIN HOME] Admin is not logged in."
    )

    print(
        "[ADMIN HOME] Redirecting to login..."
    )

    return redirect(
        url_for("admin.login")
    )


# ============================================================
# Admin Login
# /admin/login
# ============================================================

@admin.route("/login", methods=["GET", "POST"])
def login():

    print("")
    print("=" * 70)
    print("ADMIN LOGIN REQUEST")
    print("=" * 70)

    print("")
    print("[LOGIN] HTTP Method:")
    print("   ", request.method)

    print("")
    print("[LOGIN] Request Path:")
    print("   ", request.path)

    print("")
    print("[LOGIN] Session:")
    print(
        "   admin_logged_in =",
        session.get("admin_logged_in")
    )

    print(
        "   admin_username =",
        session.get("admin_username")
    )

    # --------------------------------------------------------
    # إذا كان المدير مسجل دخول بالفعل
    # --------------------------------------------------------

    if session.get("admin_logged_in"):

        print("")
        print(
            "[LOGIN] Admin is already logged in."
        )

        print(
            "[LOGIN] Redirecting to dashboard..."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    # --------------------------------------------------------
    # معالجة تسجيل الدخول
    # --------------------------------------------------------

    if request.method == "POST":

        print("")
        print("=" * 70)
        print("ADMIN LOGIN POST")
        print("=" * 70)

        print("")
        print("[LOGIN] POST request received.")

        # ----------------------------------------------------
        # قراءة اسم المستخدم
        # ----------------------------------------------------

        username = request.form.get(
            "username",
            ""
        ).strip()

        # ----------------------------------------------------
        # قراءة كلمة المرور
        # ----------------------------------------------------

        password = request.form.get(
            "password",
            ""
        )

        print("")
        print("[LOGIN] Submitted username:")
        print(
            "   ",
            username
        )

        # لا نطبع كلمة المرور لأسباب أمنية
        print("")
        print("[LOGIN] Password received:")
        print(
            "   ",
            "YES" if password else "NO"
        )

        print("")
        print("[LOGIN] Password length:")
        print(
            "   ",
            len(password)
        )

        # ====================================================
        # Admin Credentials
        # ====================================================

        ADMIN_USERNAME = "betacode"
        ADMIN_PASSWORD = "ali1234"

        print("")
        print("[LOGIN] Configured admin username:")
        print(
            "   ",
            ADMIN_USERNAME
        )

        print("")
        print("[LOGIN] Checking credentials...")

        # ====================================================
        # Check Login
        # ====================================================

        username_valid = (
            username == ADMIN_USERNAME
        )

        password_valid = (
            password == ADMIN_PASSWORD
        )

        print("")
        print("[LOGIN] Username valid:")
        print(
            "   ",
            username_valid
        )

        print("")
        print("[LOGIN] Password valid:")
        print(
            "   ",
            password_valid
        )

        if (
            username_valid
            and password_valid
        ):

            print("")
            print("=" * 70)
            print("ADMIN LOGIN SUCCESS")
            print("=" * 70)

            # ------------------------------------------------
            # إنشاء جلسة المدير
            # ------------------------------------------------

            session["admin_logged_in"] = True

            session["admin_username"] = (
                username
            )

            print("")
            print(
                "[LOGIN] Session created successfully."
            )

            print("")
            print(
                "[LOGIN] admin_logged_in =",
                session.get(
                    "admin_logged_in"
                )
            )

            print(
                "[LOGIN] admin_username =",
                session.get(
                    "admin_username"
                )
            )

            print("")
            print(
                "[LOGIN] Redirecting to dashboard..."
            )

            return redirect(
                url_for("admin.dashboard")
            )

        # ====================================================
        # Invalid Login
        # ====================================================

        print("")
        print("=" * 70)
        print("ADMIN LOGIN FAILED")
        print("=" * 70)

        print("")
        print(
            "[LOGIN] Invalid username or password."
        )

        print("")
        print(
            "[LOGIN] Sending error message to login page."
        )

        flash(
            "اسم المستخدم أو كلمة المرور غير صحيحة.",
            "error"
        )

    # ========================================================
    # Login Page
    # ========================================================

    print("")
    print("=" * 70)
    print("RENDERING ADMIN LOGIN PAGE")
    print("=" * 70)

    print("")
    print("[LOGIN] Template requested:")
    print(
        "   admin/admin_login.html"
    )

    print("")
    print("[LOGIN] Calling render_template()...")

    try:

        response = render_template(
            "admin/admin_login.html"
        )

        print("")
        print(
            "[LOGIN] SUCCESS: Template rendered successfully."
        )

        print("")
        print(
            "[LOGIN] Rendered HTML length:"
        )

        print(
            "   ",
            len(response)
        )

        print("")
        print("=" * 70)
        print("ADMIN LOGIN PAGE READY")
        print("=" * 70)

        return response

    except Exception as ex:

        print("")
        print("=" * 70)
        print("ADMIN LOGIN TEMPLATE ERROR")
        print("=" * 70)

        print("")
        print(
            "[LOGIN] ERROR: Failed to render template."
        )

        print("")
        print(
            "[LOGIN] Requested template:"
        )

        print(
            "   admin/admin_login.html"
        )

        print("")
        print(
            "[LOGIN] Exception type:"
        )

        print(
            "   ",
            type(ex).__name__
        )

        print("")
        print(
            "[LOGIN] Exception message:"
        )

        print(
            "   ",
            str(ex)
        )

        print("")
        print(
            "[LOGIN] Full exception:"
        )

        print(
            repr(ex)
        )

        print("")
        print("=" * 70)
        print(
            "ADMIN LOGIN TEMPLATE ERROR END"
        )
        print("=" * 70)

        raise


# ============================================================
# Admin Logout
# /admin/logout
# ============================================================

@admin.route("/logout")
def logout():

    print("")
    print("=" * 70)
    print("ADMIN LOGOUT REQUEST")
    print("=" * 70)

    print("")
    print(
        "[LOGOUT] Current admin username:"
    )

    print(
        "   ",
        session.get("admin_username")
    )

    # --------------------------------------------------------
    # حذف حالة تسجيل الدخول
    # --------------------------------------------------------

    session.pop(
        "admin_logged_in",
        None
    )

    print("")
    print(
        "[LOGOUT] admin_logged_in removed."
    )

    # --------------------------------------------------------
    # حذف اسم المستخدم
    # --------------------------------------------------------

    session.pop(
        "admin_username",
        None
    )

    print("")
    print(
        "[LOGOUT] admin_username removed."
    )

    print("")
    print(
        "[LOGOUT] Session after logout:"
    )

    print(
        "   admin_logged_in =",
        session.get(
            "admin_logged_in"
        )
    )

    print(
        "   admin_username =",
        session.get(
            "admin_username"
        )
    )

    print("")
    print(
        "[LOGOUT] Redirecting to login..."
    )

    return redirect(
        url_for("admin.login")
    )
