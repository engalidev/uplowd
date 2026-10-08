import hmac
import os
import secrets
from datetime import datetime, timedelta

from flask import Flask, abort, render_template, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from routes.admin import admin
from routes.user import main as main_bp

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ---------------------------------------------------------------- Config
secret = os.environ.get("SECRET_KEY")
if not secret:
    secret = secrets.token_hex(32)
    print("[SECURITY] SECRET_KEY غير مضبوط. اضبطه في متغيرات البيئة "
          "وإلا ستنتهي الجلسات عند كل إعادة تشغيل.", flush=True)

app.config.update(
    SECRET_KEY=secret,
    MAX_CONTENT_LENGTH=int(os.environ.get("MAX_UPLOAD_MB", "1024")) * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get(
        "COOKIE_SECURE", "1" if os.environ.get("RAILWAY_ENVIRONMENT") else "0"
    ) == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)
app.json.ensure_ascii = False

SITE_NAME = os.environ.get("SITE_NAME", "Devspark")


# ---------------------------------------------------------------- CSRF
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(24)
    return session["_csrf"]


@app.before_request
def csrf_protect():
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.path.startswith("/admin"):
        sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token") or ""
        expected = session.get("_csrf", "")
        if not sent or not expected or not hmac.compare_digest(sent, expected):
            abort(400)


# ---------------------------------------------------------------- Templates
app.jinja_env.globals["csrf_token"] = csrf_token


@app.context_processor
def inject_globals():
    return {"site_name": SITE_NAME, "current_year": datetime.now().year}


@app.template_filter("fsize")
def fsize(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


@app.template_filter("fdate")
def fdate(value):
    return str(value or "")[:10] or "—"


# ---------------------------------------------------------------- Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(admin, url_prefix="/admin")


# ---------------------------------------------------------------- Security headers
@app.after_request
def security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return resp


# ---------------------------------------------------------------- Errors
ERRORS = {
    400: ("طلب غير صالح", "انتهت صلاحية الصفحة أو الطلب غير مكتمل. أعد تحميل الصفحة وحاول مرة أخرى."),
    404: ("الصفحة غير موجودة", "الرابط الذي فتحته غير صحيح أو أن المحتوى حُذف."),
    413: ("الملف كبير جدًا", "حجم الملف يتجاوز الحد المسموح به على الخادم."),
    500: ("خطأ في الخادم", "حدث خطأ غير متوقع. حاول مرة أخرى بعد قليل."),
}


def _make_handler(code, title, message):
    def handler(_e):
        return render_template("error.html", code=code, title=title, message=message), code
    return handler


for _code, (_title, _msg) in ERRORS.items():
    app.register_error_handler(_code, _make_handler(_code, _title, _msg))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
