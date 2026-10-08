"""
تخزين البرامج والإصدارات على القرص.

uploads/
  <slug>/
    program.json            بيانات البرنامج
    manifest.json           آخر إصدار (متوافق مع الكود القديم)
    releases/<version>/
        release.json
        <file>
"""
import hashlib
import json
import os
import re
import secrets
import shutil
import uuid
from datetime import datetime, timezone

from packaging.version import InvalidVersion, Version
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT") or os.path.join(BASE_DIR, "uploads")
PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL", "https://uplowd-production.up.railway.app"
).rstrip("/")
DEFAULT_PROGRAM = os.environ.get("DEFAULT_PROGRAM", "Devspark")

ALLOWED_EXTENSIONS = {".exe", ".msi", ".zip", ".rar"}
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,49}$")
VERSION_RE = re.compile(r"^\d+(\.\d+){2,3}$")
PALETTE_SIZE = 8

os.makedirs(UPLOAD_ROOT, exist_ok=True)


class StorageError(ValueError):
    """خطأ يمكن عرضه للمستخدم."""


# ------------------------------------------------------------------ JSON
def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def write_json(path, data):
    tmp = f"{path}.{uuid.uuid4().hex}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# ------------------------------------------------------------------ Versions
def normalize_version(value, default=""):
    m = re.search(r"\d+(?:\.\d+){0,3}", str(value or ""))
    if not m:
        return default
    parts = m.group(0).split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts[:4])


def parse_version(value):
    try:
        return Version(value)
    except (InvalidVersion, TypeError):
        raise StorageError("رقم الإصدار غير صالح.")


def _vkey(rec):
    try:
        return Version(rec.get("version", "0"))
    except InvalidVersion:
        return Version("0")


# ------------------------------------------------------------------ Slugs / paths
def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")[:40]


def valid_slug(slug):
    return bool(slug and SLUG_RE.match(slug))


def program_dir(slug):
    """مجلد البرنامج (غير حساس لحالة الأحرف لدعم البيانات القديمة)."""
    if not valid_slug(slug):
        return None
    exact = os.path.join(UPLOAD_ROOT, slug)
    if os.path.isdir(exact):
        return exact
    try:
        for name in os.listdir(UPLOAD_ROOT):
            full = os.path.join(UPLOAD_ROOT, name)
            if name.lower() == slug.lower() and os.path.isdir(full):
                return full
    except OSError:
        pass
    return None


def _color_for(slug):
    return sum(map(ord, slug)) % PALETTE_SIZE


def download_url(slug, version, filename):
    return f"{PUBLIC_BASE_URL}/download/{slug}/{version}/{filename}"


# ------------------------------------------------------------------ Releases
def _release_record(version, minimum, filename, size, sha256, date, notes, restart, migration):
    return {
        "version": version,
        "minimumVersion": minimum,
        "fileName": filename,
        "size": size,
        "sha256": sha256,
        "releaseDate": date,
        "releaseNotes": notes,
        "requiresRestart": restart,
        "requiresDatabaseMigration": migration,
    }


def _list_releases(path):
    out = []
    rroot = os.path.join(path, "releases")
    if not os.path.isdir(rroot):
        return out
    for ver in os.listdir(rroot):
        rdir = os.path.join(rroot, ver)
        rec = read_json(os.path.join(rdir, "release.json"))
        if rec and rec.get("fileName") and os.path.isfile(os.path.join(rdir, rec["fileName"])):
            out.append(rec)
    out.sort(key=_vkey, reverse=True)
    return out


def _migrate_legacy(path, legacy):
    """نقل ملف Setup القديم (في جذر المجلد) إلى هيكل الإصدارات."""
    try:
        if not legacy or os.path.isdir(os.path.join(path, "releases")):
            return
        filename = os.path.basename(legacy.get("fileName") or legacy.get("package") or "")
        version = normalize_version(legacy.get("version"))
        src = os.path.join(path, filename)
        if not (filename and version and os.path.isfile(src)):
            return
        rdir = os.path.join(path, "releases", version)
        os.makedirs(rdir, exist_ok=True)
        shutil.move(src, os.path.join(rdir, filename))
        write_json(os.path.join(rdir, "release.json"), _release_record(
            version, normalize_version(legacy.get("minimumVersion"), "0.0.0"), filename,
            int(legacy.get("size") or 0), legacy.get("sha256", ""),
            legacy.get("releaseDate") or now_iso(), legacy.get("releaseNotes", ""),
            bool(legacy.get("requiresRestart")), bool(legacy.get("requiresDatabaseMigration")),
        ))
    except Exception as ex:  # لا نكسر الصفحة بسبب الترحيل
        print("[STORAGE] legacy migration failed:", ex, flush=True)


def _load_meta(path):
    slug = os.path.basename(path)
    meta = read_json(os.path.join(path, "program.json"))
    if meta:
        meta["slug"] = slug
        return meta
    legacy = read_json(os.path.join(path, "manifest.json"))
    meta = {
        "slug": slug,
        "name": (legacy or {}).get("product") or slug,
        "description": "",
        "category": "",
        "icon": "",
        "color": _color_for(slug),
        "createdAt": (legacy or {}).get("releaseDate") or now_iso(),
    }
    try:
        write_json(os.path.join(path, "program.json"), meta)
    except OSError:
        pass
    _migrate_legacy(path, legacy)
    return meta


def build_manifest(program, rel):
    url = download_url(program["slug"], rel["version"], rel["fileName"])
    return {
        "product": program["name"],
        "program": program["slug"],
        "version": rel["version"],
        "minimumVersion": rel.get("minimumVersion", "0.0.0"),
        "package": rel["fileName"],
        "packageUrl": url,
        "downloadUrl": url,
        "fileName": rel["fileName"],
        "size": rel.get("size", 0),
        "sha256": rel.get("sha256", ""),
        "releaseDate": rel.get("releaseDate", ""),
        "releaseNotes": rel.get("releaseNotes", ""),
        "requiresRestart": bool(rel.get("requiresRestart")),
        "requiresDatabaseMigration": bool(rel.get("requiresDatabaseMigration")),
    }


def _write_manifest(path):
    meta = _load_meta(path)
    meta["name"] = meta.get("name") or meta["slug"]
    releases = _list_releases(path)
    target = os.path.join(path, "manifest.json")
    if releases:
        write_json(target, build_manifest(meta, releases[0]))
    elif os.path.isfile(target):
        os.remove(target)


# ------------------------------------------------------------------ Programs
def _decorate(meta, releases):
    name = meta.get("name") or meta["slug"]
    icon = (meta.get("icon") or "").strip()
    latest = releases[0] if releases else None
    return {
        **meta,
        "name": name,
        "letter": icon or name[:1].upper(),
        "releases": releases,
        "latest": latest,
        "release_count": len(releases),
        "total_size": sum(int(r.get("size") or 0) for r in releases),
        "updated": (latest or {}).get("releaseDate") or meta.get("createdAt", ""),
    }


def get_program(slug):
    path = program_dir(slug)
    if not path:
        return None
    meta = _load_meta(path)
    return _decorate(meta, _list_releases(path))


def list_programs():
    items = []
    try:
        names = os.listdir(UPLOAD_ROOT)
    except OSError:
        return items
    for name in names:
        path = os.path.join(UPLOAD_ROOT, name)
        if os.path.isdir(path) and valid_slug(name):
            items.append(_decorate(_load_meta(path), _list_releases(path)))
    items.sort(key=lambda p: p["updated"], reverse=True)
    return items


def create_program(name, slug="", description="", category="", icon=""):
    name = (name or "").strip()
    if len(name) < 2:
        raise StorageError("اكتب اسم البرنامج (حرفان على الأقل).")
    slug = (slug or "").strip().lower() or slugify(name) or "app-" + secrets.token_hex(3)
    if not valid_slug(slug):
        raise StorageError("المعرّف يقبل أحرفًا إنجليزية وأرقامًا والرمزين - و _ فقط.")
    if program_dir(slug):
        raise StorageError("المعرّف مستخدم لبرنامج آخر. اختر معرّفًا مختلفًا.")
    path = os.path.join(UPLOAD_ROOT, slug)
    os.makedirs(os.path.join(path, "releases"))
    write_json(os.path.join(path, "program.json"), {
        "name": name[:80],
        "description": (description or "").strip()[:600],
        "category": (category or "").strip()[:40],
        "icon": (icon or "").strip()[:2],
        "color": _color_for(slug),
        "createdAt": now_iso(),
    })
    return slug


def update_program(slug, name, description, category, icon):
    path = program_dir(slug)
    if not path:
        raise StorageError("البرنامج غير موجود.")
    name = (name or "").strip()
    if len(name) < 2:
        raise StorageError("اكتب اسم البرنامج (حرفان على الأقل).")
    meta = _load_meta(path)
    meta.pop("slug", None)
    meta.update(name=name[:80], description=(description or "").strip()[:600],
                category=(category or "").strip()[:40], icon=(icon or "").strip()[:2])
    write_json(os.path.join(path, "program.json"), meta)
    _write_manifest(path)


def delete_program(slug):
    path = program_dir(slug)
    if not path:
        raise StorageError("البرنامج غير موجود.")
    shutil.rmtree(path)


# ------------------------------------------------------------------ Publishing
def _sha256_and_size(path):
    h, size = hashlib.sha256(), 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def publish_release(slug, file, version, minimum_version="", notes="",
                    requires_restart=False, requires_migration=False):
    path = program_dir(slug)
    if not path:
        raise StorageError("البرنامج غير موجود.")
    slug = os.path.basename(path)

    ver = normalize_version(version)
    if not ver:
        raise StorageError("اكتب رقم إصدار صحيحًا مثل 1.0.1")
    ver_obj = parse_version(ver)

    minimum = normalize_version(minimum_version, "0.0.0")
    if parse_version(minimum) > ver_obj:
        raise StorageError("الحد الأدنى للإصدار لا يمكن أن يكون أعلى من إصدار التحديث.")

    if not file or not file.filename:
        raise StorageError("اختر ملف التحديث أولًا.")
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise StorageError("نوع الملف غير مدعوم. المسموح: EXE, MSI, ZIP, RAR.")
    filename = secure_filename(file.filename)
    if not filename or not filename.lower().endswith(ext):
        filename = f"{slug}_{ver}{ext}"

    releases = _list_releases(path)
    if releases and ver_obj <= _vkey(releases[0]):
        raise StorageError(
            f"الإصدار {ver} ليس أحدث من الإصدار الحالي {releases[0]['version']}."
        )

    rdir = os.path.join(path, "releases", ver)
    if os.path.exists(rdir):
        shutil.rmtree(rdir, ignore_errors=True)
    os.makedirs(rdir)
    try:
        tmp = os.path.join(rdir, ".upload-" + uuid.uuid4().hex)
        file.save(tmp)
        sha256, size = _sha256_and_size(tmp)
        if size <= 0:
            raise StorageError("الملف المرفوع فارغ.")
        os.replace(tmp, os.path.join(rdir, filename))
        rec = _release_record(ver, minimum, filename, size, sha256, now_iso(),
                              (notes or "").strip(), bool(requires_restart), bool(requires_migration))
        write_json(os.path.join(rdir, "release.json"), rec)
        _write_manifest(path)
        return rec
    except Exception:
        shutil.rmtree(rdir, ignore_errors=True)
        raise


def delete_release(slug, version):
    path = program_dir(slug)
    if not path or not VERSION_RE.match(version or ""):
        raise StorageError("الإصدار غير موجود.")
    rdir = os.path.join(path, "releases", version)
    if not os.path.isdir(rdir):
        raise StorageError("الإصدار غير موجود.")
    shutil.rmtree(rdir)
    _write_manifest(path)


# ------------------------------------------------------------------ Queries
def manifest_for(slug):
    p = get_program(slug)
    return build_manifest(p, p["latest"]) if p and p["latest"] else None


def recent_releases(limit=10):
    rows = []
    for p in list_programs():
        for r in p["releases"]:
            rows.append({**r, "slug": p["slug"], "programName": p["name"],
                         "letter": p["letter"], "color": p["color"]})
    rows.sort(key=lambda r: r.get("releaseDate", ""), reverse=True)
    return rows[:limit]


def stats():
    items = list_programs()
    return {
        "programs": len(items),
        "releases": sum(p["release_count"] for p in items),
        "size": sum(p["total_size"] for p in items),
    }
