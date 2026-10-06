# ============================================================
# app.py
# Devspark ERP - Public Update Server
#
# الوظائف العامة فقط:
#   /
#   /download/<program>/<filename>
#   /manifest.json
#   /latest_version/<program_name>
#   /health
#
# وظائف الإدارة موجودة بالكامل في:
#   admin.py
#
# تسجيل الدخول موجود في:
#   login.py
# ============================================================

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from flask import (
    Flask,
    abort,
    jsonify,
    render_template,
    send_from_directory,
)


# ============================================================
# Flask App
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "DEVSpark_CHANGE_THIS_SECRET_KEY"
)


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(app.root_path)

UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://uplowd-production.up.railway.app"
).rstrip("/")


# ============================================================
# Default values
# ============================================================

DEFAULT_PROGRAM = "Devspark"
DEFAULT_PRODUCT = "Devspark ERP"

UPDATE_EXTENSION = ".exe"

SETUP_FILENAME = "Devspark_Setup.exe"

ALLOWED_EXTENSIONS = {
    ".exe",
    ".setup",
    ".msi",
    ".zip",
    ".rar",
}


# ============================================================
# Logging
# ============================================================

def log(message: str) -> None:
    """طباعة سجل بسيط إلى stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


# ============================================================
# File helpers
# ============================================================

def allowed_file(filename: str) -> bool:
    """التحقق من امتداد الملف."""
    if not filename:
        return False

    extension = Path(filename).suffix.lower()

    return extension in ALLOWED_EXTENSIONS


def calculate_sha256(file_path: str | Path) -> str:
    """حساب SHA-256 للملف."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def get_file_size(file_path: str | Path) -> int:
    """الحصول على حجم الملف بالبايت."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


# ============================================================
# Version helpers
# ============================================================

def normalize_version(version: str | None) -> str:
    """
    توحيد رقم الإصدار.

    أمثلة:
        1        -> 1.0.0
        1.2      -> 1.2.0
        1.2.3    -> 1.2.3
        v1.2.3   -> 1.2.3
    """

    if version is None:
        return "0.0.0"

    value = str(version).strip()

    if not value:
        return "0.0.0"

    value = value.lower()

    if value.startswith("v"):
        value = value[1:]

    value = value.strip()

    parts = value.split(".")

    normalized_parts = []

    for part in parts[:3]:
        match = re.match(r"^\d+", part)

        if match:
            normalized_parts.append(match.group(0))
        else:
            normalized_parts.append("0")

    while len(normalized_parts) < 3:
        normalized_parts.append("0")

    return ".".join(normalized_parts)


def parse_version(version: str | None) -> tuple[int, int, int]:
    """تحويل رقم الإصدار إلى tuple للمقارنة."""
    normalized = normalize_version(version)

    try:
        major, minor, patch = normalized.split(".")
        return int(major), int(minor), int(patch)
    except Exception:
        return 0, 0, 0


# ============================================================
# Security / path helpers
# ============================================================

def sanitize_program_name(program_name: str | None) -> str:
    """
    تنظيف اسم البرنامج ومنع Path Traversal.
    """

    if not program_name:
        return DEFAULT_PROGRAM

    value = str(program_name).strip()

    value = os.path.basename(value)

    value = re.sub(r"[^A-Za-z0-9_\-\. ]+", "_", value)

    value = value.strip(" .")

    if not value:
        return DEFAULT_PROGRAM

    return value


def get_program_folder(program_name: str | None) -> Path:
    """الحصول على مجلد البرنامج داخل uploads."""
    safe_program = sanitize_program_name(program_name)

    folder = UPLOAD_FOLDER / safe_program

    folder.mkdir(parents=True, exist_ok=True)

    return folder


def get_manifest_path(program_name: str | None) -> Path:
    """مسار manifest.json للبرنامج."""
    return get_program_folder(program_name) / "manifest.json"


# ============================================================
# Manifest
# ============================================================

def load_manifest(program_name: str | None) -> dict:
    """قراءة manifest.json."""

    manifest_path = get_manifest_path(program_name)

    if not manifest_path.is_file():
        return {}

    try:
        with open(
            manifest_path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as ex:
        log(f"ERROR: Failed to load manifest: {ex}")

    return {}


def save_manifest(
    program_name: str | None,
    manifest: dict
) -> None:
    """
    حفظ manifest بشكل ذري.
    """

    manifest_path = get_manifest_path(program_name)

    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fd, temp_name = tempfile.mkstemp(
        prefix="manifest_",
        suffix=".tmp",
        dir=str(manifest_path.parent)
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                manifest,
                file,
                ensure_ascii=False,
                indent=2
            )

            file.flush()
            os.fsync(file.fileno())

        os.replace(
            temp_name,
            manifest_path
        )

    except Exception:
        try:
            os.remove(temp_name)
        except OSError:
            pass

        raise


# ============================================================
# URL helpers
# ============================================================

def build_download_url(
    program_name: str,
    filename: str
) -> str:

    program = sanitize_program_name(program_name)

    safe_filename = os.path.basename(filename)

    return (
        f"{PUBLIC_BASE_URL}"
        f"/download/"
        f"{quote(program, safe='')}/"
        f"{quote(safe_filename, safe='')}"
    )


def is_https_url(url: str | None) -> bool:
    """التحقق من أن الرابط HTTPS."""
    if not url:
        return False

    return str(url).lower().startswith("https://")


# ============================================================
# Setup validation helpers
# ============================================================

def validate_setup_filename(filename: str) -> bool:
    """
    التحقق من أن الملف النهائي هو ملف Setup صالح.
    """

    if not filename:
        return False

    extension = Path(filename).suffix.lower()

    return extension == ".exe"


def remove_file_safely(file_path: str | Path) -> bool:
    """
    حذف ملف بأمان.
    """

    path = Path(file_path)

    if not path.exists():
        return False

    try:
        path.unlink()

        log(f"File deleted: {path}")

        return True

    except Exception as ex:
        log(
            f"ERROR: Failed to delete "
            f"{path}: {ex}"
        )

        return False


def create_temp_path(
    directory: str | Path,
    prefix: str = "tmp_",
    suffix: str = ".tmp"
) -> Path:
    """
    إنشاء اسم ملف مؤقت بدون إنشاء الملف نفسه.
    """

    directory = Path(directory)

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    fd, temp_name = tempfile.mkstemp(
        prefix=prefix,
        suffix=suffix,
        dir=str(directory)
    )

    os.close(fd)

    path = Path(temp_name)

    try:
        path.unlink()
    except OSError:
        pass

    return path


def safe_replace_file(
    source_path: str | Path,
    destination_path: str | Path
) -> None:
    """
    استبدال ملف بطريقة آمنة.
    """

    source = Path(source_path)
    destination = Path(destination_path)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    os.replace(
        source,
        destination
    )


# ============================================================
# Public routes
# ============================================================

@app.route("/")
def index():
    """
    الصفحة العامة.

    هذه الصفحة للمستخدم فقط.
    لا يوجد فيها:
        - رفع
        - حذف
        - نشر
        - إدارة
    """

    programs = []

    if UPLOAD_FOLDER.exists():

        for program_folder in sorted(
            UPLOAD_FOLDER.iterdir(),
            key=lambda item: item.name.lower()
        ):

            if not program_folder.is_dir():
                continue

            program_name = program_folder.name

            manifest = load_manifest(
                program_name
            )

            files = []

            for file_path in sorted(
                program_folder.iterdir(),
                key=lambda item: item.name.lower()
            ):

                if not file_path.is_file():
                    continue

                if file_path.name.lower() == "manifest.json":
                    continue

                if file_path.name.startswith("."):
                    continue

                files.append(
                    {
                        "name": file_path.name,
                        "size": get_file_size(file_path),
                        "download_url": build_download_url(
                            program_name,
                            file_path.name
                        )
                    }
                )

            programs.append(
                {
                    "name": program_name,
                    "manifest": manifest,
                    "files": files
                }
            )

    default_manifest = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "index.html",
        programs=programs,
        manifest=default_manifest,
        default_program=DEFAULT_PROGRAM,
        product_name=DEFAULT_PRODUCT
    )


# ============================================================

@app.route(
    "/download/<program>/<path:filename>"
)
def download_file(
    program: str,
    filename: str
):
    """
    تحميل ملف عام.
    """

    program = sanitize_program_name(
        program
    )

    filename = os.path.basename(
        filename
    )

    if not filename:
        abort(404)

    program_folder = get_program_folder(
        program
    )

    file_path = program_folder / filename

    if not file_path.is_file():
        abort(404)

    return send_from_directory(
        str(program_folder),
        filename,
        as_attachment=True
    )


# ============================================================

@app.route("/manifest.json")
def manifest():
    """
    API العام للتحديث.
    """

    program_name = request_program_name()

    data = load_manifest(
        program_name
    )

    if not data:

        data = {
            "product": DEFAULT_PRODUCT,
            "program": program_name,
            "version": "0.0.0",
            "minimumVersion": "0.0.0",
            "package": SETUP_FILENAME,
            "packageUrl": build_download_url(
                program_name,
                SETUP_FILENAME
            ),
            "downloadUrl": build_download_url(
                program_name,
                SETUP_FILENAME
            ),
            "fileName": SETUP_FILENAME,
            "size": 0,
            "sha256": "",
            "releaseDate": None,
            "releaseNotes": "",
            "requiresRestart": False,
            "requiresDatabaseMigration": False
        }

    package_name = data.get(
        "package"
    ) or data.get(
        "fileName"
    ) or SETUP_FILENAME

    package_name = os.path.basename(
        package_name
    )

    package_path = (
        get_program_folder(program_name)
        / package_name
    )

    package_url = build_download_url(
        program_name,
        package_name
    )

    data["product"] = data.get(
        "product",
        DEFAULT_PRODUCT
    )

    data["program"] = program_name

    data["package"] = package_name
    data["fileName"] = package_name

    data["packageUrl"] = package_url
    data["downloadUrl"] = package_url

    if package_path.is_file():

        data["size"] = get_file_size(
            package_path
        )

        try:
            data["sha256"] = calculate_sha256(
                package_path
            )
        except Exception:
            pass

    else:
        data.setdefault(
            "size",
            0
        )

        data.setdefault(
            "sha256",
            ""
        )

    return jsonify(data)


# ============================================================

def request_program_name() -> str:
    """
    الحصول على اسم البرنامج من query string
    مع الحفاظ على Devspark كافتراضي.

    أمثلة:
        /manifest.json
        /manifest.json?program=Devspark
    """

    from flask import request

    program_name = request.args.get(
        "program",
        DEFAULT_PROGRAM
    )

    return sanitize_program_name(
        program_name
    )


# ============================================================

@app.route(
    "/latest_version/<program_name>"
)
def latest_version(
    program_name: str
):
    """
    API قديم للتوافق مع النسخ السابقة
    من برنامج Devspark Updater.
    """

    program_name = sanitize_program_name(
        program_name
    )

    manifest_data = load_manifest(
        program_name
    )

    if manifest_data:

        version = normalize_version(
            manifest_data.get(
                "version",
                "0.0.0"
            )
        )

        package_name = (
            manifest_data.get(
                "package"
            )
            or manifest_data.get(
                "fileName"
            )
            or SETUP_FILENAME
        )

        package_name = os.path.basename(
            package_name
        )

        package_path = (
            get_program_folder(
                program_name
            )
            / package_name
        )

        download_url = build_download_url(
            program_name,
            package_name
        )

        return jsonify(
            {
                "program": program_name,
                "version": version,
                "package": package_name,
                "fileName": package_name,
                "downloadUrl": download_url,
                "packageUrl": download_url,
                "exists": package_path.is_file()
            }
        )

    # --------------------------------------------------------
    # توافق إضافي مع الملفات القديمة
    # --------------------------------------------------------

    program_folder = get_program_folder(
        program_name
    )

    legacy_files = []

    for file_path in program_folder.iterdir():

        if not file_path.is_file():
            continue

        if file_path.name.lower() == "manifest.json":
            continue

        if file_path.name.startswith("."):
            continue

        if file_path.suffix.lower() != ".exe":
            continue

        legacy_files.append(
            file_path
        )

    if legacy_files:

        latest_file = max(
            legacy_files,
            key=lambda item: item.stat().st_mtime
        )

        download_url = build_download_url(
            program_name,
            latest_file.name
        )

        return jsonify(
            {
                "program": program_name,
                "version": "0.0.0",
                "package": latest_file.name,
                "fileName": latest_file.name,
                "downloadUrl": download_url,
                "packageUrl": download_url,
                "exists": True
            }
        )

    return jsonify(
        {
            "program": program_name,
            "version": "0.0.0",
            "package": SETUP_FILENAME,
            "fileName": SETUP_FILENAME,
            "downloadUrl": build_download_url(
                program_name,
                SETUP_FILENAME
            ),
            "packageUrl": build_download_url(
                program_name,
                SETUP_FILENAME
            ),
            "exists": False
        }
    )


# ============================================================

@app.route("/health")
def health():
    """
    فحص حالة السيرفر.
    """

    return jsonify(
        {
            "status": "ok",
            "service": "Devspark ERP Update Server",
            "product": DEFAULT_PRODUCT,
            "time": datetime.now(
                timezone.utc
            ).isoformat()
        }
    )


# ============================================================
# Register Blueprints
# ============================================================
#
# مهم:
# جميع وظائف admin موجودة في admin.py
# ولا يتم وضعها هنا.
#
# الاستيراد في الأسفل متعمد حتى تكون جميع
# الدوال والمساعدات السابقة معرفة قبل admin.py.
# ============================================================

from login import login_bp
from admin import admin_bp

app.register_blueprint(
    login_bp
)

app.register_blueprint(
    admin_bp
)


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
