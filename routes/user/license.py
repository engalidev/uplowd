"""Public BETACODE licensing pages; client manually copies the key."""
import secrets
from flask import Blueprint, abort, current_app, jsonify, make_response, redirect, render_template, request, session, url_for
from services import license_store as store
from services.license_crypto import generate_legacy_license

license_public = Blueprint("license_public", __name__)


def no_cache(response):
    response.headers["Cache-Control"] = "no-store, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _csrf():
    if not session.get("betacode_license_csrf"):
        session["betacode_license_csrf"] = secrets.token_urlsafe(32)
    return session["betacode_license_csrf"]


def _verify_csrf():
    expected = session.get("betacode_license_csrf", "")
    supplied = request.form.get("_license_csrf", "") or request.headers.get("X-License-CSRF", "")
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        current_app.logger.warning("Public license CSRF rejected: session_present=%s supplied_present=%s", bool(expected), bool(supplied))
        abort(400, description="License CSRF verification failed")


@license_public.route("/licenses/request", methods=["GET", "POST"])
def request_license():
    error = None
    if request.method == "POST":
        _verify_csrf()
        try:
            _, token = store.submit(request.form.get("customer_name"), request.form.get("device_id"))
            return no_cache(redirect(url_for("license_public.license_status", token=token), code=303))
        except ValueError as exc:
            error = str(exc)
    return no_cache(make_response(render_template(
        "user/license_request.html", error=error, license_csrf=_csrf()
    )))


@license_public.route("/licenses/status/<token>", methods=["GET"])
def license_status(token):
    item = store.status(token)
    if not item:
        abort(404)
    return no_cache(make_response(render_template(
        "user/license_status.html", item=item, token=token, license_csrf=_csrf()
    )))


@license_public.route("/licenses/status/<token>/json", methods=["GET"])
def license_status_json(token):
    item = store.status(token)
    if not item:
        return no_cache(jsonify({"error": "الطلب غير موجود"})), 404
    # A fresh same-origin status request repairs the customer CSRF cookie after
    # an admin login in the same browser calls session.clear().
    return no_cache(jsonify({
        "status": item["status"],
        "secondsLeft": max(0, int(item.get("seconds_left") or 0)),
        "reason": item.get("reason") if item["status"] == "rejected" else None,
        "csrfToken": _csrf(),
    }))


@license_public.route("/licenses/status/<token>/reveal", methods=["POST"])
def reveal_license(token):
    # A bearer URL alone is not enough to bypass same-origin CSRF validation.
    expected = session.get("betacode_license_csrf", "")
    supplied = request.form.get("_license_csrf", "") or request.headers.get("X-License-CSRF", "")
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        return no_cache(jsonify({"error": "انتهت صلاحية جلسة الصفحة. أعد التحقق من الحالة ثم حاول مجدداً.", "code": "csrf_expired"})), 400

    item = store.can_reveal(token)
    if item is None:
        return no_cache(jsonify({"error": "انتهت مهلة عرض المفتاح أو لم تتم الموافقة"})), 410

    try:
        key = generate_legacy_license(item["device_id"], item["license_type"], item["license_expiry"])
    except Exception:
        current_app.logger.exception("License generation failed for approved request #%s", item["id"])
        return no_cache(jsonify({"error": "خدمة إصدار التراخيص غير جاهزة"})), 503

    # One more server-side expiry check after generation; the DB clock is authoritative.
    if store.can_reveal(token) is None:
        return no_cache(jsonify({"error": "انتهت مهلة عرض المفتاح"})), 410
    return no_cache(jsonify({"licenseKey": key}))
