"""BETACODE update storage: stable program keys, legacy slug compatibility.

The directory slug is internal; programKey is the stable public application identity.
Keep UPLOAD_ROOT on persistent storage in production.
"""
import hashlib
import json
import os
import re
import secrets
import shutil
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from packaging.version import InvalidVersion, Version
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT") or os.path.join(BASE_DIR, "uploads")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://betacode.up.railway.app").rstrip("/")
DEFAULT_PROGRAM = os.environ.get("DEFAULT_PROGRAM", "betacode-erp").strip().lower()
ALLOWED_EXTENSIONS = {".exe", ".msi", ".zip", ".rar"}
SLUG_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,49}$")
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
VERSION_RE = re.compile(r"^\d+(?:\.\d+){2,3}$")
PALETTE_SIZE = 8
os.makedirs(UPLOAD_ROOT, exist_ok=True)


class StorageError(ValueError):
    pass


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else None
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


def normalize_version(value, default=""):
    # Accept up to four numeric segments; normalize missing third segment.
    text = str(value or "").strip()
    if not re.fullmatch(r"v?\d+(?:\.\d+){0,3}", text, re.I):
        return default
    parts = text.lstrip("vV").split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts)


def parse_version(value):
    try:
        return Version(value)
    except (InvalidVersion, TypeError, ValueError):
        raise StorageError("رقم الإصدار غير صالح.")


def _vkey(rec):
    try:
        return Version(rec.get("version", "0"))
    except (InvalidVersion, TypeError):
        return Version("0")


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")[:40]


def valid_slug(slug):
    return isinstance(slug, str) and bool(SLUG_RE.fullmatch(slug))


def valid_program_key(key):
    return isinstance(key, str) and bool(KEY_RE.fullmatch(key))


def _derive_key(name, slug):
    # Name-based migration for old programs, e.g. BETACODE ERP => betacode-erp.
    # For non-Latin names with no Latin letters, a deliberate key must be supplied.
    key = slugify(name)
    if not valid_program_key(key):
        candidate = str(slug).strip().lower().replace("_", "-")
        key = candidate if valid_program_key(candidate) else ""
    return key


def program_dir(slug):
    if not valid_slug(slug):
        return None
    exact = os.path.join(UPLOAD_ROOT, slug)
    if os.path.isdir(exact):
        return exact
    try:
        for entry in os.scandir(UPLOAD_ROOT):
            if entry.is_dir() and entry.name.lower() == slug.lower():
                return entry.path
    except OSError:
        pass
    return None


def _color_for(slug):
    return sum(map(ord, slug)) % PALETTE_SIZE


def download_url(slug, version, filename):
    return (f"{PUBLIC_BASE_URL}/download/{quote(slug, safe='')}/"
            f"{quote(version, safe='')}/{quote(filename, safe='')}")


def _release_record(version, minimum, filename, size, sha256, date, notes, restart, migration):
    return {"version": version, "minimumVersion": minimum, "fileName": filename,
            "size": size, "sha256": sha256, "releaseDate": date,
            "releaseNotes": notes, "requiresRestart": restart,
            "requiresDatabaseMigration": migration}


def _list_releases(path):
    out = []
    rroot = os.path.join(path, "releases")
    if not os.path.isdir(rroot):
        return out
    for ver in os.listdir(rroot):
        if not VERSION_RE.fullmatch(ver):
            continue
        rdir = os.path.join(rroot, ver)
        if not os.path.isdir(rdir):
            continue
        rec = read_json(os.path.join(rdir, "release.json"))
        if not rec:
            continue
        filename = rec.get("fileName")
        if (not isinstance(filename, str) or not filename or
                os.path.basename(filename) != filename or filename.startswith(".")):
            continue
        if os.path.isfile(os.path.join(rdir, filename)):
            out.append(rec)
    out.sort(key=_vkey, reverse=True)
    return out


def _migrate_legacy(path, legacy):
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
            version, normalize_version(legacy.get("minimumVersion"), "0.0.0"),
            filename, int(legacy.get("size") or 0), legacy.get("sha256", ""),
            legacy.get("releaseDate") or now_iso(), legacy.get("releaseNotes", ""),
            bool(legacy.get("requiresRestart")),
            bool(legacy.get("requiresDatabaseMigration"))))
    except Exception as ex:
        print("[STORAGE] legacy migration failed:", repr(ex), flush=True)


def _load_meta(path):
    slug = os.path.basename(path)
    meta_path = os.path.join(path, "program.json")
    meta = read_json(meta_path)
    if meta is None:
        legacy = read_json(os.path.join(path, "manifest.json"))
        meta = {"name": (legacy or {}).get("product") or slug,
                "description": "", "category": "", "icon": "",
                "color": _color_for(slug),
                "createdAt": (legacy or {}).get("releaseDate") or now_iso()}
        write_json(meta_path, meta)
        _migrate_legacy(path, legacy)

    # Safe one-time migration: never rename or move releases/directories.
    key = meta.get("programKey") or meta.get("program_key")
    if not key:
        key = _derive_key(meta.get("name") or slug, slug)
        if key:
            meta["programKey"] = key
            meta.pop("program_key", None)
            write_json(meta_path, meta)
    meta["slug"] = slug
    return meta


def _all_program_paths():
    try:
        return [entry.path for entry in os.scandir(UPLOAD_ROOT)
                if entry.is_dir() and valid_slug(entry.name)]
    except OSError:
        return []


def get_program_by_key(program_key):
    key = str(program_key or "").strip().lower()
    if not valid_program_key(key):
        return None
    matches = []
    for path in _all_program_paths():
        meta = _load_meta(path)
        if str(meta.get("programKey") or "").lower() == key:
            matches.append(path)
    if len(matches) > 1:
        # Fail closed: never serve an arbitrary program's update.
        print("[STORAGE] duplicate programKey:", key, flush=True)
        return None
    return get_program(os.path.basename(matches[0])) if matches else None


def _assert_key_unique(key, except_slug=None):
    for path in _all_program_paths():
        slug = os.path.basename(path)
        if except_slug and slug.lower() == except_slug.lower():
            continue
        meta = _load_meta(path)
        if str(meta.get("programKey") or "").lower() == key:
            raise StorageError("هوية البرنامج الثابتة مستخدمة لبرنامج آخر.")


def build_manifest(program, rel):
    url = download_url(program["slug"], rel["version"], rel["fileName"])
    return {"product": program["name"],
            "program": program.get("programKey") or program["slug"],
            "programKey": program.get("programKey") or "",
            "version": rel["version"],
            "minimumVersion": rel.get("minimumVersion", "0.0.0"),
            "package": rel["fileName"], "packageUrl": url,
            "downloadUrl": url, "fileName": rel["fileName"],
            "size": rel.get("size", 0), "sha256": rel.get("sha256", ""),
            "releaseDate": rel.get("releaseDate", ""),
            "releaseNotes": rel.get("releaseNotes", ""),
            "requiresRestart": bool(rel.get("requiresRestart")),
            "requiresDatabaseMigration": bool(rel.get("requiresDatabaseMigration"))}


def _write_manifest(path):
    meta = _load_meta(path)
    releases = _list_releases(path)
    target = os.path.join(path, "manifest.json")
    if releases:
        write_json(target, build_manifest(meta, releases[0]))
    elif os.path.isfile(target):
        os.remove(target)


def _decorate(meta, releases):
    name = meta.get("name") or meta["slug"]
    icon = (meta.get("icon") or "").strip()
    latest = releases[0] if releases else None
    return {**meta, "name": name, "letter": icon or name[:1].upper(),
            "releases": releases, "latest": latest,
            "release_count": len(releases),
            "total_size": sum(int(r.get("size") or 0) for r in releases),
            "updated": (latest or {}).get("releaseDate") or meta.get("createdAt", "")}


def get_program(slug):
    path = program_dir(slug)
    return _decorate(_load_meta(path), _list_releases(path)) if path else None


def list_programs():
    items = [_decorate(_load_meta(path), _list_releases(path))
             for path in _all_program_paths()]
    items.sort(key=lambda p: p["updated"], reverse=True)
    return items


def create_program(name, slug="", description="", category="", icon="", program_key=""):
    name = (name or "").strip()
    if len(name) < 2:
        raise StorageError("اكتب اسم البرنامج (حرفان على الأقل).")
    slug = (slug or "").strip().lower() or slugify(name) or "app-" + secrets.token_hex(3)
    if not valid_slug(slug):
        raise StorageError("المعرّف الداخلي يقبل الإنجليزية والأرقام و - و _ فقط.")
    if program_dir(slug):
        raise StorageError("المعرّف الداخلي مستخدم بالفعل.")
    key = (program_key or "").strip().lower() or _derive_key(name, slug)
    if not valid_program_key(key):
        raise StorageError("حدد هوية ثابتة بالإنجليزية مثل betacode-erp أو betacode-school.")
    _assert_key_unique(key)
    path = os.path.join(UPLOAD_ROOT, slug)
    os.makedirs(os.path.join(path, "releases"))
    try:
        write_json(os.path.join(path, "program.json"), {
            "name": name[:80], "programKey": key,
            "description": (description or "").strip()[:600],
            "category": (category or "").strip()[:40],
            "icon": (icon or "").strip()[:2],
            "color": _color_for(slug), "createdAt": now_iso()})
    except Exception:
        shutil.rmtree(path, ignore_errors=True)
        raise
    return slug


def update_program(slug, name, description, category, icon, program_key=""):
    path = program_dir(slug)
    if not path:
        raise StorageError("البرنامج غير موجود.")
    name = (name or "").strip()
    if len(name) < 2:
        raise StorageError("اكتب اسم البرنامج (حرفان على الأقل).")
    meta = _load_meta(path)
    existing_key = (meta.get("programKey") or "").strip().lower()
    requested_key = (program_key or "").strip().lower()
    if requested_key and requested_key != existing_key:
        if existing_key:
            raise StorageError("هوية البرنامج الثابتة لا يمكن تغييرها بعد إنشائها.")
        if not valid_program_key(requested_key):
            raise StorageError("هوية البرنامج الثابتة غير صالحة.")
        _assert_key_unique(requested_key, except_slug=slug)
        meta["programKey"] = requested_key
    meta.pop("slug", None)
    meta.update(name=name[:80], description=(description or "").strip()[:600],
                category=(category or "").strip()[:40],
                icon=(icon or "").strip()[:2])
    write_json(os.path.join(path, "program.json"), meta)
    _write_manifest(path)


def delete_program(slug):
    path = program_dir(slug)
    if not path:
        raise StorageError("البرنامج غير موجود.")
    shutil.rmtree(path)


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
        raise StorageError("اكتب رقم إصدار صحيحاً مثل 1.0.1.")
    ver_obj = parse_version(ver)
    minimum = normalize_version(minimum_version, "0.0.0")
    if parse_version(minimum) > ver_obj:
        raise StorageError("الحد الأدنى للإصدار لا يمكن أن يكون أعلى من إصدار التحديث.")
    if not file or not file.filename:
        raise StorageError("اختر ملف التحديث أولاً.")
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise StorageError("نوع الملف غير مدعوم. المسموح: EXE, MSI, ZIP, RAR.")
    filename = secure_filename(file.filename)
    if not filename or not filename.lower().endswith(ext):
        filename = f"{slug}_{ver}{ext}"
    releases = _list_releases(path)
    if releases and ver_obj <= _vkey(releases[0]):
        raise StorageError(f"الإصدار {ver} ليس أحدث من الإصدار الحالي {releases[0]['version']}.")
    rdir = os.path.join(path, "releases", ver)
    if os.path.exists(rdir):
        raise StorageError("مجلد هذا الإصدار موجود بالفعل؛ لن نحذف محتواه.")
    os.makedirs(rdir)
    try:
        tmp = os.path.join(rdir, ".upload-" + uuid.uuid4().hex)
        file.save(tmp)
        sha256, size = _sha256_and_size(tmp)
        if size <= 0:
            raise StorageError("الملف المرفوع فارغ.")
        os.replace(tmp, os.path.join(rdir, filename))
        rec = _release_record(ver, minimum, filename, size, sha256, now_iso(),
                              (notes or "").strip(), bool(requires_restart),
                              bool(requires_migration))
        write_json(os.path.join(rdir, "release.json"), rec)
        _write_manifest(path)
        return rec
    except Exception:
        shutil.rmtree(rdir, ignore_errors=True)
        raise


def delete_release(slug, version):
    path = program_dir(slug)
    if not path or not VERSION_RE.fullmatch(version or ""):
        raise StorageError("الإصدار غير موجود.")
    rdir = os.path.join(path, "releases", version)
    if not os.path.isdir(rdir):
        raise StorageError("الإصدار غير موجود.")
    shutil.rmtree(rdir)
    _write_manifest(path)


def manifest_for(slug):
    p = get_program(slug)
    return build_manifest(p, p["latest"]) if p and p["latest"] else None


def manifest_for_key(program_key):
    p = get_program_by_key(program_key)
    return build_manifest(p, p["latest"]) if p and p["latest"] else None


def recent_releases(limit=10):
    rows = []
    for p in list_programs():
        for r in p["releases"]:
            rows.append({**r, "slug": p["slug"], "programKey": p.get("programKey", ""),
                         "programName": p["name"], "letter": p["letter"],
                         "color": p["color"]})
    rows.sort(key=lambda r: r.get("releaseDate", ""), reverse=True)
    return rows[:limit]


def stats():
    items = list_programs()
    return {"programs": len(items),
            "releases": sum(p["release_count"] for p in items),
            "size": sum(p["total_size"] for p in items)}
