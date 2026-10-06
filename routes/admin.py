# ============================================================
# routes/admin.py
# Devspark ERP Update Server
#
# مسؤول عن:
#
# /admin
# /admin/files
# /admin/publish
#
# /delete/<program>/<filename>
# /publish-update
#
# جميعها محمية بتسجيل دخول الإدارة.
#
# ============================================================

import os
import re
import uuid

from datetime import datetime, timezone

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)

from werkzeug.utils import secure_filename

from packaging import version

from .login import admin_required


# ============================================================
# Blueprint
# ============================================================

admin_bp = Blueprint(
    "admin",
    __name__
)


# ============================================================
# Constants
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
    ".rar"
}


# ============================================================
# Logging
# ============================================================

def log(message):

    print(
        "[DEVSPARK ADMIN] "
        + str(message),
        flush=True
    )


# ============================================================
# Helpers
# ============================================================

def get_upload_folder():

    return current_app.config[
        "UPLOAD_FOLDER"
    ]


def allowed_file(filename):

    if not filename:
        return False

    _, ext = os.path.splitext(
        filename.lower()
    )

    return ext in ALLOWED_EXTENSIONS


def normalize_version(
    value,
    default="0.0.0"
):

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

    program_name = (
        str(
            program_name or ""
        )
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

    program_name = sanitize_program_name(
        program_name
    )

    program_folder = os.path.join(
        get_upload_folder(),
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

    return os.path.join(
        get_program_folder(
            program_name
        ),
        "manifest.json"
    )


def load_manifest(
    program_name=DEFAULT_PROGRAM
):

    manifest_path = get_manifest_path(
        program_name
    )

    if not os.path.isfile(
        manifest_path
    ):

        return None

    try:

        import json

        with open(
            manifest_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

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

    import json

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


def calculate_sha256(
    file_path
):

    import hashlib

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


def get_file_size(
    file_path
):

    return os.path.getsize(
        file_path
    )


def build_download_url(
    program_name,
    filename
):

    public_base_url = current_app.config[
        "PUBLIC_BASE_URL"
    ]

    program_name = sanitize_program_name(
        program_name
    )

    filename = os.path.basename(
        str(filename or "")
    )

    return (
        f"{public_base_url}"
        f"/download/"
        f"{program_name}/"
        f"{filename}"
    )


def is_https_url(url):

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
                "Deleted temporary file: "
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
# Admin Dashboard
# ============================================================

@admin_bp.route(
    "/admin",
    methods=["GET"]
)
@admin_required
def dashboard():

    programs = {}

    upload_root = get_upload_folder()

    if os.path.isdir(
        upload_root
    ):

        try:

            program_names = sorted(
                os.listdir(
                    upload_root
                ),
                reverse=True
            )

        except Exception:

            program_names = []

        for prog in program_names:

            prog_path = os.path.join(
                upload_root,
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

    manifest = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "admin/index.html",
        programs=programs,
        manifest=manifest,
        admin_username=session_username()
    )


# ============================================================
# Admin Files
# ============================================================

@admin_bp.route(
    "/admin/files",
    methods=["GET"]
)
@admin_required
def files():

    return redirect(
        url_for(
            "admin.dashboard"
        )
    )


# ============================================================
# Admin Publish Page
# ============================================================

@admin_bp.route(
    "/admin/publish",
    methods=["GET"]
)
@admin_required
def publish():

    manifest = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "admin/index.html",
        manifest=manifest,
        programs={},
        admin_username=session_username()
    )


# ============================================================
# Session Username
# ============================================================

def session_username():

    from flask import session

    return session.get(
        "admin_username",
        "beatacode"
    )


# ============================================================
# General Upload
# ============================================================

@admin_bp.route(
    "/admin/upload",
    methods=["POST"]
)
@admin_required
def upload_file():

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
            "⚠️ لم يتم اختيار ملف."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    original_filename = secure_filename(
        file.filename
    )

    if not allowed_file(
        original_filename
    ):

        flash(
            "⚠️ امتداد الملف غير مدعوم. "
            "المسموح: EXE, SETUP, MSI, ZIP, RAR"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
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
            "General file uploaded: "
            + file_path
        )

        flash(
            f"✅ تم رفع {original_filename} بنجاح."
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
            f"❌ فشل رفع الملف: {ex}"
        )

    return redirect(
        url_for(
            "admin.dashboard"
        )
    )


# ============================================================
# Delete
# ============================================================

@admin_bp.route(
    "/delete/<program>/<path:filename>",
    methods=["POST"]
)
@admin_required
def delete_file(
    program,
    filename
):

    delete_password = current_app.config[
        "DELETE_PASSWORD"
    ]

    password = request.form.get(
        "password",
        ""
    )

    if password != delete_password:

        flash(
            "❌ كلمة مرور حذف الملف غير صحيحة."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    program = sanitize_program_name(
        program
    )

    filename = os.path.basename(
        filename
    )

    if not filename:

        flash(
            "⚠️ اسم الملف غير صالح."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    file_path = os.path.join(
        get_upload_folder(),
        program,
        filename
    )

    if not os.path.isfile(
        file_path
    ):

        flash(
            "⚠️ الملف غير موجود."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    try:

        os.remove(
            file_path
        )

        log(
            "File deleted: "
            + file_path
        )

        flash(
            f"🗑️ تم حذف {filename} بنجاح."
        )

    except Exception as ex:

        log(
            "ERROR: Delete failed: "
            + str(ex)
        )

        flash(
            f"❌ فشل حذف الملف: {ex}"
        )

    return redirect(
        url_for(
            "admin.dashboard"
        )
    )


# ============================================================
# Publish Update
# ============================================================

@admin_bp.route(
    "/publish-update",
    methods=["POST"]
)
@admin_required
def publish_update():

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
            "❌ رقم الإصدار غير صالح."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    try:

        release_version_obj = parse_version(
            release_version,
            "version"
        )

    except ValueError as ex:

        flash(
            f"❌ {ex}"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
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
            f"❌ {ex}"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    if minimum_version_obj > release_version_obj:

        flash(
            "❌ Minimum Version لا يمكن أن يكون أعلى من إصدار التحديث."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # Release Notes
    # --------------------------------------------------------

    release_notes = (
        request.form.get(
            "release_notes",
            ""
        )
        .strip()
    )

    # --------------------------------------------------------
    # Flags
    # --------------------------------------------------------

    requires_restart = (
        request.form.get(
            "requires_restart"
        )
        == "on"
    )

    requires_database_migration = (
        request.form.get(
            "requires_database_migration"
        )
        == "on"
    )

    # --------------------------------------------------------
    # Setup
    # --------------------------------------------------------

    file = request.files.get(
        "update_file"
    )

    if not file or not file.filename:

        flash(
            "❌ يجب اختيار ملف Devspark_Setup.exe للتحديث."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    original_filename = secure_filename(
        file.filename
    )

    if not validate_setup_filename(
        original_filename
    ):

        flash(
            "❌ ملف التحديث يجب أن يكون EXE فقط."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # Folder
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
                    f"❌ الإصدار {release_version} "
                    f"ليس أحدث من الإصدار الحالي "
                    f"{current_version_text}."
                )

                return redirect(
                    url_for(
                        "admin.dashboard"
                    )
                )

        except ValueError:

            flash(
                "❌ تعذر مقارنة أرقام الإصدارات."
            )

            return redirect(
                url_for(
                    "admin.dashboard"
                )
            )

    # --------------------------------------------------------
    # Official filename
    # --------------------------------------------------------

    filename = SETUP_FILENAME

    file_path = os.path.join(
        program_folder,
        filename
    )

    # --------------------------------------------------------
    # Temporary setup
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
            f"❌ فشل حفظ ملف التحديث: {ex}"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    if not os.path.isfile(
        temp_setup_path
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ لم يتم إنشاء ملف التحديث المؤقت."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # Size
    # --------------------------------------------------------

    try:

        file_size = get_file_size(
            temp_setup_path
        )

        if file_size <= 0:

            raise ValueError(
                "ملف Devspark_Setup.exe فارغ."
            )

    except Exception as ex:

        remove_file_safely(
            temp_setup_path
        )

        flash(
            f"❌ ملف التحديث غير صالح: {ex}"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # SHA
    # --------------------------------------------------------

    try:

        sha256 = calculate_sha256(
            temp_setup_path
        )

    except Exception as ex:

        remove_file_safely(
            temp_setup_path
        )

        flash(
            f"❌ فشل حساب SHA-256: {ex}"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    if not re.fullmatch(
        r"[a-fA-F0-9]{64}",
        sha256
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ SHA-256 الناتج غير صالح."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # URL
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
            "❌ رابط التحديث يجب أن يكون HTTPS."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    release_date = datetime.now(
        timezone.utc
    ).isoformat()

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
    # Backup old setup
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
                "❌ تعذر تجهيز ملف Setup القديم للاستبدال."
            )

            log(
                "ERROR backup: "
                + str(ex)
            )

            return redirect(
                url_for(
                    "admin.dashboard"
                )
            )

    # --------------------------------------------------------
    # Publish new setup
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
                    "CRITICAL restore error: "
                    + str(restore_ex)
                )

        flash(
            f"❌ فشل نشر ملف التحديث: {ex}"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # Save manifest
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

        try:

            if old_manifest_exists and old_manifest_data:

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

        except Exception as restore_manifest_ex:

            log(
                "CRITICAL manifest restore error: "
                + str(restore_manifest_ex)
            )

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
                "CRITICAL setup restore error: "
                + str(restore_ex)
            )

        flash(
            f"❌ فشل إنشاء manifest.json: {ex}"
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # Delete backup
    # --------------------------------------------------------

    if backup_setup_path:

        remove_file_safely(
            backup_setup_path
        )

    # --------------------------------------------------------
    # Final verification
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

        log(
            "CRITICAL verification error: "
            + str(ex)
        )

        flash(
            "⚠️ تم نشر التحديث ولكن فشل التحقق النهائي من الملف."
        )

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    log(
        "PUBLISH UPDATE SUCCESS"
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
        "Size: "
        + str(file_size)
    )

    log(
        "SHA256: "
        + sha256
    )

    flash(
        f"🚀 تم نشر Devspark ERP بالإصدار "
        f"{release_version} بنجاح."
    )

    return redirect(
        url_for(
            "admin.dashboard"
        )
    ) 
