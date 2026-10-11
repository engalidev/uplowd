"""Register public and admin license blueprints in app.py. No WPF API required."""
import os
import secrets
from flask import (Blueprint, abort, current_app, jsonify, redirect, render_template,
                   request, session, url_for, flash, make_response)
from services import license_store as store
from services.license_crypto import generate_legacy_license



def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, private, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def _csrf():
    if 'betacode_license_csrf' not in session:
        session['betacode_license_csrf'] = secrets.token_urlsafe(32)
    return session['betacode_license_csrf']


def _verify_csrf():
    expected = session.get('betacode_license_csrf', '')
    supplied = request.form.get('_license_csrf', '') or request.headers.get('X-License-CSRF', '')
    if not expected or not secrets.compare_digest(expected, supplied):
        abort(400, description='CSRF verification failed')


def _admin_guard():
    # Current admin_base.html displays session['admin_username'].
    # Verify this matches the session key set by routes/admin/login.py.
    if not session.get('admin_username'):
        return redirect(url_for('admin.login', next=request.path))
    return None


license_admin = Blueprint('license_admin', __name__, url_prefix='/admin/licenses')

@license_admin.route('', methods=['GET'])
def index():
    guard = _admin_guard()
    if guard:
        return guard
    return no_cache(make_response(render_template('admin/admin_licenses.html',
                                                  requests=store.list_requests(), license_csrf=_csrf())))


@license_admin.route('/<int:request_id>/approve', methods=['POST'])
def approve(request_id):
    guard = _admin_guard()
    if guard:
        return guard
    _verify_csrf()
    try:
        from services.license_crypto import generate_legacy_license
        from datetime import date
        # Validate signing configuration before irreversibly approving a request.
        generate_legacy_license('CONFIGURATION-CHECK', 'PROFESSIONAL', date(2040, 12, 31))
        store.decide(request_id, 'approve', str(session['admin_username']))
        flash('تمت الموافقة. بدأت مهلة عرض المفتاح لمدة 60 ثانية.', 'success')
    except (ValueError, RuntimeError) as exc:
        flash(str(exc), 'error')
    return redirect(url_for('license_admin.index'), code=303)


@license_admin.route('/<int:request_id>/reject', methods=['POST'])
def reject(request_id):
    guard = _admin_guard()
    if guard:
        return guard
    _verify_csrf()
    try:
        store.decide(request_id, 'reject', str(session['admin_username']), request.form.get('reason',''))
        flash('تم رفض الطلب.', 'success')
    except ValueError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('license_admin.index'), code=303)
