import hmac
import os
import time
from collections import defaultdict

from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from routes.admin import admin, login_required

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "betacode")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

if not (ADMIN_PASSWORD or ADMIN_PASSWORD_HASH):
    ADMIN_PASSWORD = "ali1234"
    print("[SECURITY] ADMIN_PASSWORD غير مضبوط، يتم استخدام كلمة المرور القديمة. "
          "غيّرها فورًا من متغيرات البيئة.", flush=True)

MAX_ATTEMPTS = 5
LOCK_SECONDS = 300
_failures = defaultdict(list)


def _ip():
    return (request.remote_addr or "unknown")


def _locked(ip):
    now = time.time()
    _failures[ip] = [t for t in _failures[ip] if now - t < LOCK_SECONDS]
    return len(_failures[ip]) >= MAX_ATTEMPTS


def _credentials_ok(username, password):
    user_ok = hmac.compare_digest(username.encode(), ADMIN_USERNAME.encode())
    if ADMIN_PASSWORD_HASH:
        pass_ok = check_password_hash(ADMIN_PASSWORD_HASH, password)
    else:
        pass_ok = hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())
    return user_ok and pass_ok


@admin.route("/")
def admin_home():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("admin.login"))


@admin.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        ip = _ip()
        if _locked(ip):
            flash("محاولات كثيرة خاطئة. انتظر 5 دقائق ثم حاول مرة أخرى.", "error")
            return render_template("admin/admin_login.html"), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if _credentials_ok(username, password):
            _failures.pop(ip, None)
            session.clear()
            session.permanent = True
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin.dashboard"))

        _failures[ip].append(time.time())
        flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "error")

    return render_template("admin/admin_login.html")


@admin.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("admin.login"))
