"""PostgreSQL licensing records. No license plaintext/ciphertext is stored."""
import hashlib
import os
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone, date

import psycopg2
from psycopg2.extras import RealDictCursor

LIFETIME_SECONDS = 60
LICENSE_EXPIRY = date(2040, 12, 31)
LICENSE_TYPE = 'PROFESSIONAL'


def _dsn():
    value = os.environ.get('DATABASE_URL') or os.environ.get('LICENSE_DATABASE_URL')
    if not value:
        raise RuntimeError('DATABASE_URL or LICENSE_DATABASE_URL is required for license storage')
    return value


@contextmanager
def connection():
    db = psycopg2.connect(_dsn(), cursor_factory=RealDictCursor)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize():
    with connection() as db, db.cursor() as cur:
        cur.execute('''
          CREATE TABLE IF NOT EXISTS betacode_license_requests (
            id BIGSERIAL PRIMARY KEY,
            customer_name VARCHAR(160) NOT NULL,
            device_id VARCHAR(256) NOT NULL,
            access_hash CHAR(64) NOT NULL UNIQUE,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            decided_at TIMESTAMPTZ,
            visible_until TIMESTAMPTZ,
            decided_by VARCHAR(160),
            reason TEXT,
            license_type VARCHAR(40),
            license_expiry DATE,
            CHECK (status IN ('pending','approved','rejected'))
          )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_betacode_license_pending ON betacode_license_requests(status, requested_at)')
        cur.execute('''CREATE TABLE IF NOT EXISTS betacode_license_audit (
            id BIGSERIAL PRIMARY KEY,
            request_id BIGINT NOT NULL REFERENCES betacode_license_requests(id),
            action VARCHAR(32) NOT NULL,
            actor VARCHAR(160) NOT NULL,
            happened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            details TEXT
        )''')


def _hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def submit(customer_name, device_id):
    name = (customer_name or '').strip()
    device = (device_id or '').strip()
    if not (2 <= len(name) <= 160):
        raise ValueError('اكتب اسم العميل من حرفين إلى 160 حرفاً')
    if not (16 <= len(device) <= 256):
        raise ValueError('بصمة الجهاز غير صالحة (16-256 حرفاً)')
    # DeviceId may be alphanumeric with separators. Avoid control characters.
    if any(ord(c) < 32 for c in device):
        raise ValueError('بصمة الجهاز تحتوي على أحرف غير صالحة')
    token = secrets.token_urlsafe(36)
    with connection() as db, db.cursor() as cur:
        cur.execute('''INSERT INTO betacode_license_requests
                     (customer_name, device_id, access_hash) VALUES (%s,%s,%s)
                     RETURNING id''', (name, device, _hash(token)))
        row_id = cur.fetchone()['id']
    return row_id, token


def get_by_token(token):
    if not token or len(token) > 200:
        return None
    with connection() as db, db.cursor() as cur:
        cur.execute('SELECT * FROM betacode_license_requests WHERE access_hash=%s', (_hash(token),))
        return cur.fetchone()


def list_requests():
    with connection() as db, db.cursor() as cur:
        cur.execute('SELECT id, customer_name, device_id, status, requested_at, decided_at, visible_until, decided_by, reason FROM betacode_license_requests ORDER BY requested_at DESC LIMIT 200')
        return cur.fetchall()


def decide(request_id, action, actor, reason=''):
    if action not in ('approve','reject'):
        raise ValueError('قرار غير صالح')
    with connection() as db, db.cursor() as cur:
        cur.execute('SELECT * FROM betacode_license_requests WHERE id=%s FOR UPDATE', (request_id,))
        rec = cur.fetchone()
        if not rec:
            raise ValueError('الطلب غير موجود')
        if rec['status'] != 'pending':
            raise ValueError('تم البت بهذا الطلب مسبقاً. لا يمكن إعادة بدء الدقيقة.')
        # Database clock is authoritative; prevents independent web-worker clock drift.
        if action == 'approve':
            cur.execute('''UPDATE betacode_license_requests
                           SET status='approved', decided_at=NOW(), visible_until=NOW()+INTERVAL '60 seconds',
                               decided_by=%s, reason=NULL, license_type=%s, license_expiry=%s
                           WHERE id=%s RETURNING visible_until''',
                        (actor, LICENSE_TYPE, LICENSE_EXPIRY, request_id))
            until = cur.fetchone()['visible_until']
        else:
            cur.execute('''UPDATE betacode_license_requests SET status='rejected', decided_at=NOW(),
                           decided_by=%s, reason=%s WHERE id=%s''', (actor, reason[:1000], request_id))
            until = None
        cur.execute('''INSERT INTO betacode_license_audit (request_id, action, actor, details)
                       VALUES (%s,%s,%s,%s)''', (request_id, action, actor, reason[:1000] or None))
        return until


def can_reveal(token):
    """Use DB NOW() for authoritative expiry check; no key persisted."""
    if not token or len(token) > 200:
        return None
    with connection() as db, db.cursor() as cur:
        cur.execute('''SELECT id, device_id, license_type, license_expiry
                       FROM betacode_license_requests
                       WHERE access_hash=%s AND status='approved' AND visible_until > NOW()''', (_hash(token),))
        return cur.fetchone()


def status(token):
    if not token or len(token) > 200:
        return None
    with connection() as db, db.cursor() as cur:
        cur.execute('''SELECT id, customer_name, status, visible_until, reason,
                              GREATEST(0, CEIL(EXTRACT(EPOCH FROM (visible_until - NOW()))))::int AS seconds_left
                       FROM betacode_license_requests WHERE access_hash=%s''', (_hash(token),))
        return cur.fetchone()
def cleanup_expired_requests():
    """
    حذف الطلبات الموافق عليها والمنتهية نهائياً،
    مع حذف سجلات التدقيق المرتبطة بها.

    يعتمد على ساعة PostgreSQL.
    """

    with connection() as db, db.cursor() as cur:

        cur.execute("""
            WITH expired AS (
                SELECT id
                FROM betacode_license_requests
                WHERE status = 'approved'
                  AND visible_until <= NOW()
            ),
            deleted_audit AS (
                DELETE FROM betacode_license_audit
                WHERE request_id IN (
                    SELECT id FROM expired
                )
                RETURNING id
            )
            DELETE FROM betacode_license_requests
            WHERE id IN (
                SELECT id FROM expired
            )
            RETURNING id
        """)

        deleted_count = cur.rowcount

        return deleted_count
        db.commit()
        return deleted_count
