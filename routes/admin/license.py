"""Admin licensing approval/rejection. Independent blueprint under /admin/licenses."""
import secrets
from datetime import date
from flask import Blueprint, abort, current_app, flash, make_response, redirect, render_template, request, session, url_for
from services import license_store as store
from services.license_crypto import generate_legacy_license
from routes.user.license import no_cache

license_admin = Blueprint("license_admin", __name__, url_prefix="/admin/licenses")


def _admin_guard():
    if not session.get("admin_logged_in") or not session.get("admin_username"):
        return redirect(url_for("admin.login", next=request.path))
    return None


def _verify_csrf():
    # app.py globally validates _csrf for /admin/ POST requests already.
    # Keep this check for defense in depth; the template includes both fields.
    expected = session.get("betacode_license_csrf", "")
    supplied = request.form.get("_license_csrf", "") or request.headers.get("X-License-CSRF", "")
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        abort(400, description="License admin CSRF verification failed")


def _csrf():
    if not session.get("betacode_license_csrf"):
        session["betacode_license_csrf"] = secrets.token_urlsafe(32)
    return session["betacode_license_csrf"]


@license_admin.route("", methods=["GET"])
def index():
    guard = _admin_guard()
    if guard is not None:
        return guard
    return no_cache(make_response(render_template(
        "admin/admin_licenses.html", requests=store.list_requests(), license_csrf=_csrf()
    )))


@license_admin.route("/<int:request_id>/approve", methods=["POST"])
def approve(request_id):
    guard = _admin_guard()
    if guard is not None:
        return guard
    _verify_csrf()
    try:
        # Validate secret setup before irreversible approval; does not persist a key.
        generate_legacy_license("CONFIGURATION-CHECK", store.LICENSE_TYPE, store.LICENSE_EXPIRY)
        store.decide(request_id, "approve", str(session["admin_username"]))
        flash("تمت الموافقة. بدأت مهلة عرض المفتاح لمدة 60 ثانية من وقت الموافقة.", "success")
    except (ValueError, RuntimeError) as exc:
        flash(str(exc), "error")
    except Exception:
        current_app.logger.exception("Failed approving license request #%s", request_id)
        flash("تعذر تسجيل الموافقة. راجع سجل الخادم.", "error")
    return no_cache(redirect(url_for("license_admin.index"), code=303))


@license_admin.route("/<int:request_id>/reject", methods=["POST"])
def reject(request_id):
    guard = _admin_guard()
    if guard is not None:
        return guard
    _verify_csrf()
    try:
        store.decide(request_id, "reject", str(session["admin_username"]), request.form.get("reason", ""))
        flash("تم رفض الطلب.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    except Exception:
        current_app.logger.exception("Failed rejecting license request #%s", request_id)
        flash("تعذر تسجيل الرفض. راجع سجل الخادم.", "error")
    return no_cache(redirect(url_for("license_admin.index"), code=303))
