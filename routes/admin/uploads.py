from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)

import os
import re
import json
import uuid
import hashlib

from datetime import datetime, timezone

from packaging import version
from werkzeug.utils import secure_filename

from routes.admin import admin


# ============================================================
# Settings
# ============================================================

DELETE_PASSWORD = os.environ.get(
    "DELETE_PASSWORD",
    "123456"
)

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    ),
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# Devspark Update Server
# ============================================================

PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://uplowd-production.up.railway.app"
).rstrip("/")


DEFAULT_PROGRAM = "Devspark"

DEFAULT_PRODUCT = "Devspark ERP"


# ============================================================
# Update Package Rules
# ============================================================

UPDATE_EXTENSION = ".exe"

SETUP_FILENAME = "Devspark_Setup.exe"


# ============================================================
# General Upload Rules
# ============================================================

ALLOWED_EXTENSIONS = {
    ".exe",
    ".setup",
    ".msi",
    ".zip",
    ".rar"
}


# ============================================================
# Admin Authentication
# ============================================================

def admin_required():
    """
    التحقق من تسجيل دخول المدير.

    إذا لم يكن المدير مسجلًا:
        يتم تحويله إلى صفحة تسجيل الدخول.

    ترجع:
        None إذا كان مسجلًا.
        Redirect إذا لم يكن مسجلًا.
    """

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin.login")
        )

    return None


# ============================================================
# Logging
# ============================================================

def log(message):
    """
    تسجيل معلومات في Railway logs.
    """

    print(
        "[DEVSPARK UPDATE SERVER] "
        + str(message),
        flush=True
    )


# ============================================================
# General Helpers
# ============================================================

def allowed_file(filename):
    """
    التحقق من امتداد الملف.
    """

    if not filename:
        return False

    _, ext = os.path.splitext(
        filename.lower()
    )

    return ext in ALLOWED_EXTENSIONS


def calculate_sha256(file_path):
    """
    حساب SHA-256 للملف.
    """

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as f:

        while True:

            chunk = f.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(
                chunk
            )

    return sha256.hexdigest()


def get_file_size(file_path):
    """
    الحصول على حجم الملف بالبايت.
    """

    return os.path.getsize(
        file_path
    )


def normalize_version(
    value,
    default="0.0.0"
):
    """
    تحويل الإصدار إلى:

        1.0.0

    أمثلة:

        1       -> 1.0.0
        1.2     -> 1.2.0
        1.2.3   -> 1.2.3
        v1.2.3  -> 1.2.3
    """

    if value is None:
        return default

    value = str(
        value
    ).strip()

    if not value:
        return default

    match = re.search(
        r"(\d+(?:\.\d+){0,3})",
        value
    )

    if not match:
        return default

    parts = match.group(1).split(".")

    while len(parts) < 3:
        parts.append("0")

    return ".".join(
        parts[:3]
    )


def parse_version(
    value,
    field_name="version"
):
    """
    قراءة الإصدار والتحقق منه.
    """

    normalized = normalize_version(
        value,
        default=""
    )

    if not normalized:

        raise ValueError(
            f"رقم الإصدار في {field_name} غير صالح."
        )

    try:

        return version.parse(
            normalized
        )

    except Exception as ex:

        raise ValueError(
            f"رقم الإصدار في {field_name} غير صالح."
        ) from ex


def sanitize_program_name(
    program_name
):
    """
    تنظيف اسم البرنامج ومنع Path Traversal.
    """

    program_name = (
        str(program_name or "")
        .strip()
    )

    if not program_name:
        program_name = DEFAULT_PROGRAM

    program_name = secure_filename(
        program_name
    )

    if not program_name:
        program_name = DEFAULT_PROGRAM

    return program_name


def get_program_folder(
    program_name=DEFAULT_PROGRAM
):
    """
    الحصول على مجلد البرنامج.
    """

    program_name = sanitize_program_name(
        program_name
    )

    program_folder = os.path.join(
        UPLOAD_FOLDER,
        program_name
    )

    os.makedirs(
        program_folder,
        exist_ok=True
    )

    return program_folder


def get_manifest_path(
    program_name=DEFAULT_PROGRAM
):
    """
    الحصول على مسار manifest.json.
    """

    return os.path.join(
        get_program_folder(
            program_name
        ),
        "manifest.json"
    )


def load_manifest(
    program_name=DEFAULT_PROGRAM
):
    """
    قراءة Manifest الحالي.
    """

    manifest_path = get_manifest_path(
        program_name
    )

    if not os.path.isfile(
        manifest_path
    ):
        return None

    try:

        with open(
            manifest_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(
                f
            )

        if not isinstance(
            data,
            dict
        ):
            return None

        return data

    except Exception as ex:

        log(
            "WARNING: Failed to load manifest: "
            + str(ex)
        )

        return None


def save_manifest(
    manifest,
    program_name=DEFAULT_PROGRAM
):
    """
    حفظ Manifest بطريقة آمنة.
    """

    manifest_path = get_manifest_path(
        program_name
    )

    temp_path = (
        manifest_path
        + "."
        + uuid.uuid4().hex
        + ".tmp"
    )

    try:

        with open(
            temp_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                manifest,
                f,
                ensure_ascii=False,
                indent=2
            )

            f.flush()

            try:
                os.fsync(
                    f.fileno()
                )
            except Exception:
                pass

        os.replace(
            temp_path,
            manifest_path
        )

    except Exception:

        try:

            if os.path.exists(
                temp_path
            ):
                os.remove(
                    temp_path
                )

        except Exception:
            pass

        raise


def build_download_url(
    program_name,
    filename
):
    """
    إنشاء رابط تحميل HTTPS.
    """

    program_name = sanitize_program_name(
        program_name
    )

    filename = os.path.basename(
        str(filename or "")
    )

    return (
        f"{PUBLIC_BASE_URL}"
        f"/download/"
        f"{program_name}/"
        f"{filename}"
    )


def is_https_url(url):
    """
    التحقق من HTTPS.
    """

    return (
        isinstance(
            url,
            str
        )
        and
        url.lower().startswith(
            "https://"
        )
    )


def validate_setup_filename(
    filename
):
    """
    التحديث الرسمي يجب أن يكون EXE.
    """

    if not filename:
        return False

    filename = os.path.basename(
        filename
    )

    return filename.lower().endswith(
        UPDATE_EXTENSION
    )


def remove_file_safely(
    file_path
):
    """
    حذف ملف بدون رفع Exception.
    """

    try:

        if (
            file_path
            and
            os.path.isfile(
                file_path
            )
        ):

            os.remove(
                file_path
            )

            log(
                "Deleted file: "
                + file_path
            )

    except Exception as ex:

        log(
            "WARNING: Could not delete file: "
            + str(ex)
        )


def create_temp_path(
    folder,
    prefix,
    extension=""
):
    """
    إنشاء مسار مؤقت داخل مجلد البرنامج.
    """

    return os.path.join(
        folder,
        (
            "."
            + prefix
            + "_"
            + uuid.uuid4().hex
            + extension
        )
    )


# ============================================================
# Admin Uploads Page
# ============================================================

@admin.route(
    "/uploads",
    methods=["GET", "POST"]
)
def uploads():

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    auth_response = admin_required()

    if auth_response:
        return auth_response

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        program_name = sanitize_program_name(
            request.form.get(
                "program_name",
                DEFAULT_PROGRAM
            )
        )

        program_folder = get_program_folder(
            program_name
        )

        file = request.files.get(
            "file"
        )

        if not file or not file.filename:

            flash(
                "⚠️ لم يتم اختيار ملف.",
                "error"
            )

            return redirect(
                url_for("admin.uploads")
            )

        original_filename = secure_filename(
            file.filename
        )

        if not allowed_file(
            original_filename
        ):

            flash(
                "⚠️ امتداد الملف غير مدعوم. "
                "المسموح: EXE, SETUP, MSI, ZIP, RAR",
                "error"
            )

            return redirect(
                url_for("admin.uploads")
            )

        filename = (
            f"{uuid.uuid4().hex}_"
            f"{original_filename}"
        )

        file_path = os.path.join(
            program_folder,
            filename
        )

        try:

            file.save(
                file_path
            )

            log(
                "Admin uploaded file: "
                + file_path
            )

            flash(
                f"✅ تم رفع {original_filename} بنجاح.",
                "success"
            )

        except Exception as ex:

            remove_file_safely(
                file_path
            )

            log(
                "ERROR: General upload failed: "
                + str(ex)
            )

            flash(
                f"❌ فشل رفع الملف: {ex}",
                "error"
            )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Files
    # --------------------------------------------------------

    programs = {}

    if os.path.isdir(
        UPLOAD_FOLDER
    ):

        try:

            program_names = sorted(
                os.listdir(
                    UPLOAD_FOLDER
                ),
                reverse=True
            )

        except Exception:

            program_names = []

        for prog in program_names:

            prog_path = os.path.join(
                UPLOAD_FOLDER,
                prog
            )

            if not os.path.isdir(
                prog_path
            ):
                continue

            files = []

            try:

                filenames = os.listdir(
                    prog_path
                )

            except Exception:

                filenames = []

            for filename in sorted(
                filenames,
                reverse=True
            ):

                if filename.lower() == "manifest.json":
                    continue

                if filename.startswith("."):
                    continue

                full_path = os.path.join(
                    prog_path,
                    filename
                )

                if os.path.isfile(
                    full_path
                ):

                    files.append(
                        filename
                    )

            programs[prog] = files

    manifest_data = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "admin/admin_uploads.html",
        programs=programs,
        manifest=manifest_data
    )


# ============================================================
# Delete File
# ============================================================

@admin.route(
    "/delete/<program>/<path:filename>",
    methods=["POST"]
)
def delete_file(
    program,
    filename
):

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    auth_response = admin_required()

    if auth_response:
        return auth_response

    # --------------------------------------------------------
    # Delete Password
    # --------------------------------------------------------

    password = request.form.get(
        "password",
        ""
    )

    if password != DELETE_PASSWORD:

        flash(
            "❌ كلمة المرور غير صحيحة.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    program = sanitize_program_name(
        program
    )

    filename = os.path.basename(
        filename
    )

    if not filename:

        flash(
            "⚠️ اسم الملف غير صالح.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        program,
        filename
    )

    # --------------------------------------------------------
    # Delete
    # --------------------------------------------------------

    if os.path.isfile(
        file_path
    ):

        try:

            os.remove(
                file_path
            )

            log(
                "Admin deleted file: "
                + file_path
            )

            flash(
                f"🗑️ تم حذف {filename} بنجاح.",
                "success"
            )

        except Exception as ex:

            log(
                "ERROR: Delete failed: "
                + str(ex)
            )

            flash(
                f"❌ فشل حذف الملف: {ex}",
                "error"
            )

    else:

        flash(
            "⚠️ الملف غير موجود.",
            "error"
        )

    return redirect(
        url_for("admin.uploads")
    )


# ============================================================
# Publish Devspark Update
# ============================================================

@admin.route(
    "/publish-update",
    methods=["POST"]
)
def publish_update():

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    auth_response = admin_required()

    if auth_response:
        return auth_response

    log(
        "=================================================="
    )

    log(
        "PUBLISH UPDATE START"
    )

    # --------------------------------------------------------
    # Program
    # --------------------------------------------------------

    program_name = sanitize_program_name(
        request.form.get(
            "program_name",
            DEFAULT_PROGRAM
        )
    )

    log(
        "Program: "
        + program_name
    )

    # --------------------------------------------------------
    # Version
    # --------------------------------------------------------

    raw_release_version = request.form.get(
        "version",
        ""
    )

    release_version = normalize_version(
        raw_release_version,
        default=""
    )

    if not release_version:

        flash(
            "❌ رقم الإصدار غير صالح.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    try:

        release_version_obj = parse_version(
            release_version,
            "version"
        )

    except ValueError as ex:

        flash(
            f"❌ {ex}",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Minimum Version
    # --------------------------------------------------------

    raw_minimum_version = request.form.get(
        "minimum_version",
        "0.0.0"
    )

    minimum_version = normalize_version(
        raw_minimum_version,
        default="0.0.0"
    )

    try:

        minimum_version_obj = parse_version(
            minimum_version,
            "minimumVersion"
        )

    except ValueError as ex:

        flash(
            f"❌ {ex}",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    if minimum_version_obj > release_version_obj:

        flash(
            "❌ Minimum Version لا يمكن أن يكون أعلى من إصدار التحديث.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Release Notes
    # --------------------------------------------------------

    release_notes = (
        request.form.get(
            "release_notes",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # Flags
    # --------------------------------------------------------

    requires_restart = (
        request.form.get(
            "requires_restart"
        ) == "on"
    )

    requires_database_migration = (
        request.form.get(
            "requires_database_migration"
        ) == "on"
    )

    # --------------------------------------------------------
    # Setup EXE
    # --------------------------------------------------------

    file = request.files.get(
        "update_file"
    )

    if not file or not file.filename:

        flash(
            "❌ يجب اختيار ملف Devspark_Setup.exe للتحديث.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    original_filename = secure_filename(
        file.filename
    )

    if not validate_setup_filename(
        original_filename
    ):

        flash(
            "❌ ملف التحديث يجب أن يكون EXE فقط.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Program Folder
    # --------------------------------------------------------

    program_folder = get_program_folder(
        program_name
    )

    # --------------------------------------------------------
    # Current Manifest
    # --------------------------------------------------------

    current_manifest = load_manifest(
        program_name
    )

    current_version_text = "0.0.0"

    if current_manifest:

        current_version_text = normalize_version(
            current_manifest.get(
                "version",
                "0.0.0"
            ),
            default="0.0.0"
        )

        try:

            current_version_obj = parse_version(
                current_version_text,
                "الإصدار الحالي"
            )

            if release_version_obj <= current_version_obj:

                flash(
                    f"❌ الإصدار {release_version} ليس أحدث من الإصدار الحالي {current_version_text}.",
                    "error"
                )

                return redirect(
                    url_for("admin.uploads")
                )

        except ValueError:

            flash(
                "❌ تعذر مقارنة أرقام الإصدارات.",
                "error"
            )

            return redirect(
                url_for("admin.uploads")
            )

    # --------------------------------------------------------
    # Official Setup Filename
    # --------------------------------------------------------

    filename = SETUP_FILENAME

    file_path = os.path.join(
        program_folder,
        filename
    )

    # --------------------------------------------------------
    # Temporary Setup
    # --------------------------------------------------------

    temp_setup_path = create_temp_path(
        program_folder,
        "setup",
        ".exe"
    )

    try:

        file.save(
            temp_setup_path
        )

    except Exception as ex:

        remove_file_safely(
            temp_setup_path
        )

        flash(
            f"❌ فشل حفظ ملف التحديث: {ex}",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Validate File
    # --------------------------------------------------------

    try:

        file_size = get_file_size(
            temp_setup_path
        )

        if file_size <= 0:

            raise ValueError(
                "ملف Devspark_Setup.exe فارغ."
            )

        sha256 = calculate_sha256(
            temp_setup_path
        )

    except Exception as ex:

        remove_file_safely(
            temp_setup_path
        )

        flash(
            f"❌ ملف التحديث غير صالح: {ex}",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # SHA-256 Validation
    # --------------------------------------------------------

    if not re.fullmatch(
        r"[a-fA-F0-9]{64}",
        sha256
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ SHA-256 الناتج غير صالح.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Package URL
    # --------------------------------------------------------

    package_url = build_download_url(
        program_name,
        filename
    )

    if not is_https_url(
        package_url
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ رابط التحديث يجب أن يكون HTTPS.",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Release Date
    # --------------------------------------------------------

    release_date = datetime.now(
        timezone.utc
    ).isoformat()

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest_data = {

        "product":
            DEFAULT_PRODUCT,

        "program":
            program_name,

        "version":
            release_version,

        "minimumVersion":
            minimum_version,

        "package":
            filename,

        "packageUrl":
            package_url,

        "downloadUrl":
            package_url,

        "fileName":
            filename,

        "size":
            file_size,

        "sha256":
            sha256,

        "releaseDate":
            release_date,

        "releaseNotes":
            release_notes,

        "requiresRestart":
            requires_restart,

        "requiresDatabaseMigration":
            requires_database_migration
    }

    # --------------------------------------------------------
    # Backup Previous Setup
    # --------------------------------------------------------

    backup_setup_path = None

    if os.path.isfile(
        file_path
    ):

        backup_setup_path = create_temp_path(
            program_folder,
            "setup_backup",
            ".exe"
        )

        try:

            os.replace(
                file_path,
                backup_setup_path
            )

        except Exception as ex:

            remove_file_safely(
                temp_setup_path
            )

            flash(
                "❌ تعذر تجهيز ملف Setup القديم للاستبدال.",
                "error"
            )

            log(
                "ERROR: Setup backup failed: "
                + str(ex)
            )

            return redirect(
                url_for("admin.uploads")
            )

    # --------------------------------------------------------
    # Publish Setup
    # --------------------------------------------------------

    try:

        os.replace(
            temp_setup_path,
            file_path
        )

    except Exception as ex:

        remove_file_safely(
            temp_setup_path
        )

        if backup_setup_path:

            try:

                if os.path.isfile(
                    backup_setup_path
                ):

                    os.replace(
                        backup_setup_path,
                        file_path
                    )

            except Exception as restore_ex:

                log(
                    "CRITICAL: Failed to restore Setup: "
                    + str(restore_ex)
                )

        flash(
            f"❌ فشل نشر ملف التحديث: {ex}",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Save Manifest
    # --------------------------------------------------------

    manifest_path = get_manifest_path(
        program_name
    )

    old_manifest_exists = os.path.isfile(
        manifest_path
    )

    old_manifest_data = current_manifest

    try:

        save_manifest(
            manifest_data,
            program_name
        )

    except Exception as ex:

        log(
            "ERROR: Failed to save manifest: "
            + str(ex)
        )

        # ----------------------------------------------------
        # Restore Manifest
        # ----------------------------------------------------

        try:

            if (
                old_manifest_exists
                and
                old_manifest_data
            ):

                save_manifest(
                    old_manifest_data,
                    program_name
                )

            elif not old_manifest_exists:

                if os.path.isfile(
                    manifest_path
                ):

                    os.remove(
                        manifest_path
                    )

        except Exception as restore_ex:

            log(
                "CRITICAL: Manifest restore failed: "
                + str(restore_ex)
            )

        # ----------------------------------------------------
        # Restore Setup
        # ----------------------------------------------------

        try:

            if os.path.isfile(
                file_path
            ):

                os.remove(
                    file_path
                )

            if (
                backup_setup_path
                and
                os.path.isfile(
                    backup_setup_path
                )
            ):

                os.replace(
                    backup_setup_path,
                    file_path
                )

        except Exception as restore_ex:

            log(
                "CRITICAL: Setup restore failed: "
                + str(restore_ex)
            )

        flash(
            f"❌ فشل إنشاء manifest.json: {ex}",
            "error"
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Remove Backup
    # --------------------------------------------------------

    if backup_setup_path:

        remove_file_safely(
            backup_setup_path
        )

    # --------------------------------------------------------
    # Final Verification
    # --------------------------------------------------------

    try:

        final_size = get_file_size(
            file_path
        )

        final_sha256 = calculate_sha256(
            file_path
        )

        if final_size != file_size:

            raise ValueError(
                "حجم الملف المنشور لا يطابق الحجم المحسوب."
            )

        if (
            final_sha256.lower()
            !=
            sha256.lower()
        ):

            raise ValueError(
                "SHA-256 للملف المنشور لا يطابق القيمة المحسوبة."
            )

    except Exception as ex:

        flash(
            "⚠️ تم نشر التحديث ولكن فشل التحقق النهائي من الملف.",
            "error"
        )

        log(
            "CRITICAL: Final verification failed: "
            + str(ex)
        )

        return redirect(
            url_for("admin.uploads")
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    log(
        "PUBLISH UPDATE SUCCESS"
    )

    log(
        "Program: "
        + program_name
    )

    log(
        "Version: "
        + release_version
    )

    log(
        "Previous Version: "
        + current_version_text
    )

    log(
        "Setup: "
        + filename
    )

    log(
        "Size: "
        + str(file_size)
        + " bytes"
    )

    log(
        "SHA256: "
        + sha256
    )

    log(
        "URL: "
        + package_url
    )

    flash(
        f"🚀 تم نشر Devspark ERP بالإصدار {release_version} بنجاح.",
        "success"
    )

    return redirect(
        url_for("admin.uploads")
    )
