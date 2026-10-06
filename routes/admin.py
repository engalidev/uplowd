# ============================================================
# admin.py
# Devspark ERP - Admin Management
#
# جميع وظائف الإدارة موجودة هنا:
#
#   /admin
#   /admin/upload
#   /admin/delete/<program>/<filename>
#   /admin/publish-update
#
# جميعها محمية بـ admin_required
# ============================================================

import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app import (
    DEFAULT_PROGRAM,
    DEFAULT_PRODUCT,
    SETUP_FILENAME,
    allowed_file,
    calculate_sha256,
    get_file_size,
    normalize_version,
    parse_version,
    sanitize_program_name,
    get_program_folder,
    load_manifest,
    save_manifest,
    build_download_url,
    is_https_url,
    validate_setup_filename,
    remove_file_safely,
    create_temp_path,
    safe_replace_file,
    log,
)

from login import admin_required


# ============================================================
# Blueprint
# ============================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ============================================================
# Local helpers
# ============================================================

def _scan_program_files(
    program_name: str
) -> list[dict]:
    """
    قراءة الملفات الموجودة للبرنامج.
    """

    program_name = sanitize_program_name(
        program_name
    )

    program_folder = get_program_folder(
        program_name
    )

    files = []

    if not program_folder.exists():
        return files

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

        try:
            stat = file_path.stat()

            files.append(
                {
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(
                        stat.st_mtime
                    ).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "extension": file_path.suffix.lower(),
                    "download_url": build_download_url(
                        program_name,
                        file_path.name
                    )
                }
            )

        except OSError:
            continue

    return files


def _scan_programs() -> list[dict]:
    """
    قراءة جميع البرامج الموجودة.
    """

    programs = []

    upload_folder = Path(
        current_app.config["UPLOAD_FOLDER"]
    )

    upload_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    for program_folder in sorted(
        upload_folder.iterdir(),
        key=lambda item: item.name.lower()
    ):

        if not program_folder.is_dir():
            continue

        program_name = program_folder.name

        manifest = load_manifest(
            program_name
        )

        files = _scan_program_files(
            program_name
        )

        programs.append(
            {
                "name": program_name,
                "manifest": manifest,
                "files": files
            }
        )

    return programs


def _get_backup_path(
    program_folder: Path
) -> Path:

    return program_folder / (
        f".backup_{uuid.uuid4().hex}.exe"
    )


def _validate_manifest_for_publish(
    manifest: dict
) -> tuple[bool, str]:

    package = manifest.get(
        "package"
    ) or manifest.get(
        "fileName"
    )

    if not package:
        return False, "اسم حزمة التحديث غير موجود."

    if not validate_setup_filename(
        package
    ):
        return (
            False,
            "ملف التحديث يجب أن يكون EXE."
        )

    package_url = manifest.get(
        "packageUrl"
    )

    if not is_https_url(
        package_url
    ):
        return (
            False,
            "رابط التحديث يجب أن يكون HTTPS."
        )

    size = manifest.get(
        "size",
        0
    )

    try:
        if int(size) <= 0:
            return (
                False,
                "حجم ملف التحديث غير صالح."
            )
    except Exception:
        return (
            False,
            "حجم ملف التحديث غير صالح."
        )

    sha256 = str(
        manifest.get(
            "sha256",
            ""
        )
    ).strip().lower()

    if not re.fullmatch(
        r"[a-f0-9]{64}",
        sha256
    ):
        return (
            False,
            "SHA-256 غير صالح."
        )

    return True, ""


# ============================================================
# Dashboard
# ============================================================

@admin_bp.route("/")
@admin_required
def dashboard():

    programs = _scan_programs()

    default_manifest = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "admin.html",
        programs=programs,
        manifest=default_manifest,
        default_program=DEFAULT_PROGRAM,
        product_name=DEFAULT_PRODUCT,
        admin_username=session_username()
    )


# ============================================================
# Session username helper
# ============================================================

def session_username() -> str:

    from flask import session

    return session.get(
        "admin_username",
        ""
    )


# ============================================================
# General upload
# ============================================================

@admin_bp.route(
    "/upload",
    methods=["POST"]
)
@admin_required
def upload_file():

    program_name = request.form.get(
        "program_name",
        DEFAULT_PROGRAM
    ).strip()

    program_name = sanitize_program_name(
        program_name
    )

    uploaded_file = request.files.get(
        "file"
    )

    if uploaded_file is None:
        flash(
            "❌ لم يتم اختيار أي ملف."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    original_filename = (
        uploaded_file.filename
        or ""
    ).strip()

    if not original_filename:
        flash(
            "❌ اسم الملف غير صالح."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    if not allowed_file(
        original_filename
    ):
        flash(
            "❌ امتداد الملف غير مسموح."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    program_folder = get_program_folder(
        program_name
    )

    safe_filename = os.path.basename(
        original_filename
    )

    final_filename = (
        f"{uuid.uuid4().hex}_"
        f"{safe_filename}"
    )

    destination = (
        program_folder
        / final_filename
    )

    try:

        uploaded_file.save(
            str(destination)
        )

        file_size = get_file_size(
            destination
        )

        if file_size <= 0:

            remove_file_safely(
                destination
            )

            flash(
                "❌ الملف المرفوع فارغ."
            )

            return redirect(
                url_for("admin.dashboard")
            )

        log(
            "File uploaded: "
            f"{destination}"
        )

        flash(
            f"✅ تم رفع الملف {safe_filename} بنجاح."
        )

    except Exception as ex:

        log(
            "ERROR: Upload failed: "
            f"{ex}"
        )

        remove_file_safely(
            destination
        )

        flash(
            f"❌ فشل رفع الملف: {ex}"
        )

    return redirect(
        url_for("admin.dashboard")
    )


# ============================================================
# Delete file
# ============================================================

@admin_bp.route(
    "/delete/<program>/<path:filename>",
    methods=["POST"]
)
@admin_required
def delete_file(
    program: str,
    filename: str
):

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
            url_for("admin.dashboard")
        )

    # منع حذف manifest من خلال مسار الملفات
    if filename.lower() == "manifest.json":

        flash(
            "❌ لا يمكن حذف manifest.json من هنا."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    program_folder = get_program_folder(
        program
    )

    file_path = (
        program_folder
        / filename
    )

    if not file_path.is_file():

        flash(
            "⚠️ الملف غير موجود."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    # --------------------------------------------------------
    # حماية إضافية:
    # لا نحذف ملف التحديث المنشور الحالي بدون
    # السماح الواضح من النظام.
    # --------------------------------------------------------

    manifest = load_manifest(
        program
    )

    current_package = (
        manifest.get("package")
        or manifest.get("fileName")
        or ""
    )

    if (
        current_package
        and os.path.basename(
            current_package
        ).lower()
        == filename.lower()
    ):

        flash(
            "⚠️ لا يمكن حذف ملف التحديث المنشور الحالي. "
            "قم بنشر إصدار جديد أولاً."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    try:

        file_path.unlink()

        log(
            "File deleted: "
            f"{file_path}"
        )

        flash(
            f"🗑️ تم حذف {filename} بنجاح."
        )

    except Exception as ex:

        log(
            "ERROR: Delete failed: "
            f"{ex}"
        )

        flash(
            f"❌ فشل حذف الملف: {ex}"
        )

    return redirect(
        url_for("admin.dashboard")
    )


# ============================================================
# Publish update
# ============================================================

@admin_bp.route(
    "/publish-update",
    methods=["POST"]
)
@admin_required
def publish_update():

    # --------------------------------------------------------
    # Basic form data
    # --------------------------------------------------------

    program_name = request.form.get(
        "program_name",
        DEFAULT_PROGRAM
    ).strip()

    program_name = sanitize_program_name(
        program_name
    )

    release_version = normalize_version(
        request.form.get(
            "version",
            ""
        )
    )

    minimum_version = normalize_version(
        request.form.get(
            "minimum_version",
            "0.0.0"
        )
    )

    release_notes = request.form.get(
        "release_notes",
        ""
    ).strip()

    requires_restart = (
        request.form.get(
            "requires_restart"
        )
        in {
            "1",
            "true",
            "on",
            "yes"
        }
    )

    requires_database_migration = (
        request.form.get(
            "requires_database_migration"
        )
        in {
            "1",
            "true",
            "on",
            "yes"
        }
    )

    # --------------------------------------------------------
    # Validate versions
    # --------------------------------------------------------

    release_tuple = parse_version(
        release_version
    )

    minimum_tuple = parse_version(
        minimum_version
    )

    if minimum_tuple > release_tuple:

        flash(
            "❌ الحد الأدنى للإصدار لا يمكن أن "
            "يكون أعلى من إصدار التحديث."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    # --------------------------------------------------------
    # Uploaded EXE
    # --------------------------------------------------------

    uploaded_file = request.files.get(
        "update_file"
    )

    if uploaded_file is None:

        flash(
            "❌ لم يتم اختيار ملف التحديث."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    original_filename = (
        uploaded_file.filename
        or ""
    ).strip()

    if not original_filename:

        flash(
            "❌ اسم ملف التحديث غير صالح."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    # التحديث المنشور يجب أن يكون EXE
    if not validate_setup_filename(
        original_filename
    ):

        flash(
            "❌ ملف التحديث يجب أن يكون EXE."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    # --------------------------------------------------------
    # Program folder
    # --------------------------------------------------------

    program_folder = get_program_folder(
        program_name
    )

    # --------------------------------------------------------
    # Current manifest
    # --------------------------------------------------------

    old_manifest = load_manifest(
        program_name
    )

    old_version = normalize_version(
        old_manifest.get(
            "version",
            "0.0.0"
        )
    )

    if (
        parse_version(release_version)
        <= parse_version(old_version)
    ):

        flash(
            "❌ إصدار التحديث الجديد يجب أن يكون "
            "أعلى من الإصدار الحالي."
        )

        return redirect(
            url_for("admin.dashboard")
        )

    # --------------------------------------------------------
    # Official filename
    # --------------------------------------------------------

    filename = SETUP_FILENAME

    final_path = (
        program_folder
        / filename
    )

    temp_path = (
        program_folder
        / (
            f".upload_{uuid.uuid4().hex}.tmp"
        )
    )

    backup_path = None

    # --------------------------------------------------------
    # Save upload to temporary file
    # --------------------------------------------------------

    try:

        uploaded_file.save(
            str(temp_path)
        )

        if not temp_path.is_file():

            flash(
                "❌ فشل حفظ ملف التحديث المؤقت."
            )

            return redirect(
                url_for("admin.dashboard")
            )

        temp_size = get_file_size(
            temp_path
        )

        if temp_size <= 0:

            remove_file_safely(
                temp_path
            )

            flash(
                "❌ ملف التحديث فارغ."
            )

            return redirect(
                url_for("admin.dashboard")
            )

        # ----------------------------------------------------
        # SHA256
        # ----------------------------------------------------

        temp_sha256 = calculate_sha256(
            temp_path
        )

        # ----------------------------------------------------
        # Download URL
        # ----------------------------------------------------

        package_url = build_download_url(
            program_name,
            filename
        )

        if not is_https_url(
            package_url
        ):

            remove_file_safely(
                temp_path
            )

            flash(
                "❌ رابط التحديث يجب أن يكون HTTPS."
            )

            return redirect(
                url_for("admin.dashboard")
            )

        # ----------------------------------------------------
        # New manifest
        # ----------------------------------------------------

        release_date = datetime.now(
            timezone.utc
        ).isoformat()

        new_manifest = {
            "product": DEFAULT_PRODUCT,
            "program": program_name,
            "version": release_version,
            "minimumVersion": minimum_version,
            "package": filename,
            "packageUrl": package_url,
            "downloadUrl": package_url,
            "fileName": filename,
            "size": temp_size,
            "sha256": temp_sha256,
            "releaseDate": release_date,
            "releaseNotes": release_notes,
            "requiresRestart": requires_restart,
            "requiresDatabaseMigration": (
                requires_database_migration
            )
        }

        # ----------------------------------------------------
        # Validate new manifest
        # ----------------------------------------------------

        valid, error_message = (
            _validate_manifest_for_publish(
                new_manifest
            )
        )

        if not valid:

            remove_file_safely(
                temp_path
            )

            flash(
                f"❌ {error_message}"
            )

            return redirect(
                url_for("admin.dashboard")
            )

        # ----------------------------------------------------
        # Backup old setup
        # ----------------------------------------------------

        old_setup_existed = (
            final_path.is_file()
        )

        if old_setup_existed:

            backup_path = _get_backup_path(
                program_folder
            )

            shutil.copy2(
                final_path,
                backup_path
            )

            log(
                "Old setup backed up: "
                f"{backup_path}"
            )

        # ----------------------------------------------------
        # Replace setup
        # ----------------------------------------------------

        safe_replace_file(
            temp_path,
            final_path
        )

        # ----------------------------------------------------
        # Verify final file
        # ----------------------------------------------------

        final_size = get_file_size(
            final_path
        )

        final_sha256 = calculate_sha256(
            final_path
        )

        if final_size != temp_size:

            raise RuntimeError(
                "حجم الملف النهائي لا يطابق الملف المرفوع."
            )

        if final_sha256.lower() != temp_sha256.lower():

            raise RuntimeError(
                "SHA-256 للملف النهائي لا يطابق الملف المرفوع."
            )

        # ----------------------------------------------------
        # Save manifest
        # ----------------------------------------------------

        save_manifest(
            program_name,
            new_manifest
        )

        # ----------------------------------------------------
        # Final verification
        # ----------------------------------------------------

        saved_manifest = load_manifest(
            program_name
        )

        saved_version = normalize_version(
            saved_manifest.get(
                "version",
                ""
            )
        )

        saved_package = os.path.basename(
            saved_manifest.get(
                "package",
                ""
            )
        )

        if saved_version != release_version:

            raise RuntimeError(
                "فشل التحقق من manifest بعد الحفظ."
            )

        if saved_package != filename:

            raise RuntimeError(
                "اسم ملف التحديث في manifest غير صحيح."
            )

        # ----------------------------------------------------
        # Delete old backup after success
        # ----------------------------------------------------

        if backup_path is not None:

            remove_file_safely(
                backup_path
            )

            backup_path = None

        log(
            "Update published successfully: "
            f"{program_name} "
            f"{release_version}"
        )

        flash(
            "🚀 تم نشر Devspark ERP "
            f"بالإصدار {release_version} بنجاح."
        )

    except Exception as ex:

        log(
            "ERROR: Publish update failed: "
            f"{ex}"
        )

        # ----------------------------------------------------
        # Remove temporary upload
        # ----------------------------------------------------

        remove_file_safely(
            temp_path
        )

        # ----------------------------------------------------
        # Restore old setup
        # ----------------------------------------------------

        try:

            if (
                backup_path is not None
                and backup_path.is_file()
            ):

                if final_path.exists():

                    remove_file_safely(
                        final_path
                    )

                safe_replace_file(
                    backup_path,
                    final_path
                )

                backup_path = None

                log(
                    "Old setup restored."
                )

        except Exception as restore_ex:

            log(
                "ERROR: Failed to restore "
                f"old setup: {restore_ex}"
            )

        # ----------------------------------------------------
        # Restore old manifest
        # ----------------------------------------------------

        try:

            save_manifest(
                program_name,
                old_manifest
            )

            log(
                "Old manifest restored."
            )

        except Exception as manifest_ex:

            log(
                "ERROR: Failed to restore "
                f"old manifest: {manifest_ex}"
            )

        flash(
            f"❌ فشل نشر التحديث: {ex}"
        )

        return redirect(
            url_for("admin.dashboard")
        )

    return redirect(
        url_for("admin.dashboard")
    )
