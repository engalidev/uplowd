from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    jsonify,
)

import os
import re
import json
import uuid
import hashlib
import shutil

from datetime import datetime, timezone

from packaging import version
from werkzeug.utils import secure_filename


# ============================================================
# Flask App
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "UPLOAD_MANAGER_SECRET"
)


# ============================================================
# Settings
# ============================================================

DELETE_PASSWORD = os.environ.get(
    "DELETE_PASSWORD",
    "123456"
)

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
# Devspark Update Server
# ============================================================

# رابط السيرفر العام.
#
# يمكن تغييره من Railway Environment Variables:
#
# PUBLIC_BASE_URL
#
# مثال:
#
# https://uplowd-production.up.railway.app
#

PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://uplowd-production.up.railway.app"
).rstrip("/")


DEFAULT_PROGRAM = "Devspark"

DEFAULT_PRODUCT = "Devspark ERP"


# ============================================================
# Update Package Rules
# ============================================================

# النظام الرسمي للتحديث يعتمد على:
#
#     Devspark_Setup.exe
#
# ولا يعتمد على:
#
#     ZIP
#     RAR
#     MSI
#
# لذلك /publish-update يقبل EXE فقط.
#

UPDATE_EXTENSION = ".exe"

SETUP_FILENAME = "Devspark_Setup.exe"


# ============================================================
# General Upload Rules
# ============================================================

# صفحة الرفع العامة يمكنها استقبال هذه الملفات.
#
# أما /publish-update فهو EXE فقط.
#

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
    """
    تسجيل معلومات مفيدة في Railway logs.
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
    التحقق من امتداد ملف الرفع العام.
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
    تحويل الإصدار إلى صيغة:

        1.0.0

    أمثلة:

        1       -> 1.0.0
        1.2     -> 1.2.0
        1.2.3   -> 1.2.3
        v1.2.3  -> 1.2.3
        Devspark 1.2.3 -> 1.2.3
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
        app.config["UPLOAD_FOLDER"],
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
    مسار Manifest.
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
    """
    حفظ Manifest بطريقة آمنة.

    يتم أولًا إنشاء ملف مؤقت،
    ثم استبدال manifest.json ذريًا.
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
    إنشاء رابط HTTPS للتحميل.
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
    التأكد من أن الرابط HTTPS.
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
    التحقق من اسم ملف Setup.

    النظام الرسمي يسمح بأي اسم EXE أثناء الرفع،
    لكن الخادم سيعيد تسميته إلى:

        Devspark_Setup.exe
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
    حذف ملف بدون رفع استثناء.
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
                "Deleted temporary/failed file: "
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
    إنشاء مسار ملف مؤقت داخل مجلد البرنامج.
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


def safe_replace_file(
    source_path,
    destination_path
):
    """
    استبدال ملف بطريقة آمنة قدر الإمكان.

    source_path:
        الملف الجديد.

    destination_path:
        الملف النهائي.
    """

    os.replace(
        source_path,
        destination_path
    )


# ============================================================
# Main Management Page
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if request.method == "POST":

        # ----------------------------------------------------
        # Program
        # ----------------------------------------------------

        program_name = sanitize_program_name(
            request.form.get(
                "program_name",
                DEFAULT_PROGRAM
            )
        )

        program_folder = get_program_folder(
            program_name
        )

        # ----------------------------------------------------
        # Uploaded file
        # ----------------------------------------------------

        file = request.files.get(
            "file"
        )

        if not file or not file.filename:

            flash(
                "⚠️ لم يتم اختيار ملف."
            )

            return redirect(
                url_for("index")
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
                url_for("index")
            )

        # ----------------------------------------------------
        # Generate safe storage filename
        # ----------------------------------------------------

        filename = (
            f"{uuid.uuid4().hex}_"
            f"{original_filename}"
        )

        file_path = os.path.join(
            program_folder,
            filename
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        try:

            file.save(
                file_path
            )

        except Exception as ex:

            log(
                "ERROR: General upload failed: "
                + str(ex)
            )

            remove_file_safely(
                file_path
            )

            flash(
                f"❌ فشل رفع الملف: {ex}"
            )

            return redirect(
                url_for("index")
            )

        log(
            "General file uploaded: "
            + file_path
        )

        flash(
            f"✅ تم رفع {original_filename} بنجاح."
        )

        return redirect(
            url_for("index")
        )

    # ========================================================
    # عرض الملفات
    # ========================================================

    programs = {}

    upload_root = app.config[
        "UPLOAD_FOLDER"
    ]

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

    # --------------------------------------------------------
    # Devspark Manifest
    # --------------------------------------------------------

    manifest_data = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "index.html",
        programs=programs,
        manifest=manifest_data
    )


# ============================================================
# Download
# ============================================================

@app.route(
    "/download/<program>/<path:filename>"
)
def download_file(
    program,
    filename
):

    program = sanitize_program_name(
        program
    )

    filename = os.path.basename(
        filename
    )

    if not filename:

        return (
            "Invalid filename.",
            400
        )

    program_folder = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program
    )

    if not os.path.isdir(
        program_folder
    ):

        return (
            "Program not found.",
            404
        )

    full_path = os.path.join(
        program_folder,
        filename
    )

    if not os.path.isfile(
        full_path
    ):

        return (
            "File not found.",
            404
        )

    log(
        "Download requested: "
        + program
        + "/"
        + filename
    )

    return send_from_directory(
        program_folder,
        filename,
        as_attachment=True
    )


# ============================================================
# Delete
# ============================================================

@app.route(
    "/delete/<program>/<path:filename>",
    methods=["POST"]
)
def delete_file(
    program,
    filename
):

    password = request.form.get(
        "password",
        ""
    )

    if password != DELETE_PASSWORD:

        flash(
            "❌ كلمة المرور غير صحيحة."
        )

        return redirect(
            url_for("index")
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
            url_for("index")
        )

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program,
        filename
    )

    if os.path.isfile(
        file_path
    ):

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

    else:

        flash(
            "⚠️ الملف غير موجود."
        )

    return redirect(
        url_for("index")
    )


# ============================================================
# Publish Devspark Update
# ============================================================

@app.route(
    "/publish-update",
    methods=["POST"]
)
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
            "❌ رقم الإصدار غير صالح."
        )

        return redirect(
            url_for("index")
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
            url_for("index")
        )

    log(
        "Release version: "
        + release_version
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
            url_for("index")
        )

    log(
        "Minimum version: "
        + minimum_version
    )

    if minimum_version_obj > release_version_obj:

        flash(
            "❌ Minimum Version لا يمكن أن يكون "
            "أعلى من إصدار التحديث."
        )

        return redirect(
            url_for("index")
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
            "❌ يجب اختيار ملف Devspark_Setup.exe للتحديث."
        )

        return redirect(
            url_for("index")
        )

    original_filename = secure_filename(
        file.filename
    )

    log(
        "Uploaded setup filename: "
        + str(original_filename)
    )

    # --------------------------------------------------------
    # EXE ONLY
    # --------------------------------------------------------

    if not validate_setup_filename(
        original_filename
    ):

        flash(
            "❌ ملف التحديث يجب أن يكون EXE فقط."
        )

        return redirect(
            url_for("index")
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

            log(
                "Current published version: "
                + current_version_text
            )

            if release_version_obj <= current_version_obj:

                flash(
                    f"❌ الإصدار {release_version} "
                    f"ليس أحدث من الإصدار الحالي "
                    f"{current_version_text}."
                )

                return redirect(
                    url_for("index")
                )

        except ValueError:

            flash(
                "❌ تعذر مقارنة أرقام الإصدارات."
            )

            return redirect(
                url_for("index")
            )

    # --------------------------------------------------------
    # Official Setup Filename
    # --------------------------------------------------------
    #
    # مهما كان اسم الملف الذي رفعه المستخدم:
    #
    #     Devspark_Setup.exe
    #
    # هو الاسم الرسمي على السيرفر.
    #
    # --------------------------------------------------------

    filename = SETUP_FILENAME

    file_path = os.path.join(
        program_folder,
        filename
    )

    # --------------------------------------------------------
    # Temporary Setup Path
    # --------------------------------------------------------
    #
    # لا نستبدل الملف القديم مباشرة.
    #
    # أولًا نحفظ الجديد في ملف مؤقت.
    #
    # إذا نجح كل شيء:
    #
    #     temp -> Devspark_Setup.exe
    #
    # --------------------------------------------------------

    temp_setup_path = create_temp_path(
        program_folder,
        "setup",
        ".exe"
    )

    log(
        "Temporary setup path: "
        + temp_setup_path
    )

    # --------------------------------------------------------
    # Save Uploaded Setup
    # --------------------------------------------------------

    try:

        file.save(
            temp_setup_path
        )

        log(
            "Temporary Setup EXE saved successfully."
        )

    except Exception as ex:

        remove_file_safely(
            temp_setup_path
        )

        log(
            "ERROR: Failed to save temporary setup: "
            + str(ex)
        )

        flash(
            f"❌ فشل حفظ ملف التحديث: {ex}"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # Validate Temporary Setup Exists
    # --------------------------------------------------------

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
            url_for("index")
        )

    # --------------------------------------------------------
    # Validate Size
    # --------------------------------------------------------

    try:

        file_size = get_file_size(
            temp_setup_path
        )

        log(
            "Setup size: "
            + str(file_size)
            + " bytes"
        )

        log(
            "Setup size: "
            + f"{file_size / 1024 / 1024:.2f}"
            + " MB"
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
            url_for("index")
        )

    # --------------------------------------------------------
    # SHA-256
    # --------------------------------------------------------

    try:

        sha256 = calculate_sha256(
            temp_setup_path
        )

        log(
            "SHA256: "
            + sha256
        )

    except Exception as ex:

        remove_file_safely(
            temp_setup_path
        )

        flash(
            f"❌ فشل حساب SHA-256: {ex}"
        )

        return redirect(
            url_for("index")
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
            "❌ SHA-256 الناتج غير صالح."
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # HTTPS Package URL
    # --------------------------------------------------------

    package_url = build_download_url(
        program_name,
        filename
    )

    log(
        "Package URL: "
        + package_url
    )

    if not is_https_url(
        package_url
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ خطأ داخلي: رابط التحديث يجب أن يكون HTTPS."
        )

        return redirect(
            url_for("index")
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
    # Validate Manifest
    # --------------------------------------------------------

    if not manifest_data["package"].lower().endswith(
        ".exe"
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ خطأ: Manifest يجب أن يشير إلى ملف EXE."
        )

        return redirect(
            url_for("index")
        )

    if not is_https_url(
        manifest_data["packageUrl"]
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ خطأ: packageUrl يجب أن يستخدم HTTPS."
        )

        return redirect(
            url_for("index")
        )

    if manifest_data["size"] <= 0:

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ خطأ: حجم Setup غير صالح."
        )

        return redirect(
            url_for("index")
        )

    if not re.fullmatch(
        r"[a-fA-F0-9]{64}",
        manifest_data["sha256"]
    ):

        remove_file_safely(
            temp_setup_path
        )

        flash(
            "❌ خطأ: SHA-256 غير صالح."
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # Backup Current Setup
    # --------------------------------------------------------
    #
    # في حالة وجود إصدار قديم:
    #
    #     Devspark_Setup.exe
    #
    # نعيد تسميته مؤقتًا قبل نشر الجديد.
    #
    # إذا فشل النشر، نستطيع استعادته.
    #
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

            log(
                "Previous Devspark_Setup.exe moved to temporary backup."
            )

        except Exception as ex:

            remove_file_safely(
                temp_setup_path
            )

            log(
                "ERROR: Could not backup previous setup: "
                + str(ex)
            )

            flash(
                "❌ تعذر تجهيز ملف Setup القديم للاستبدال."
            )

            return redirect(
                url_for("index")
            )

    # --------------------------------------------------------
    # Publish New Setup
    # --------------------------------------------------------

    try:

        safe_replace_file(
            temp_setup_path,
            file_path
        )

        log(
            "New Devspark_Setup.exe published successfully."
        )

    except Exception as ex:

        log(
            "ERROR: Failed to publish new Setup: "
            + str(ex)
        )

        remove_file_safely(
            temp_setup_path
        )

        # استعادة النسخة القديمة إن كانت موجودة.
        if backup_setup_path:

            try:

                if os.path.isfile(
                    backup_setup_path
                ):

                    os.replace(
                        backup_setup_path,
                        file_path
                    )

                    log(
                        "Previous Setup restored."
                    )

            except Exception as restore_ex:

                log(
                    "CRITICAL: Failed to restore previous Setup: "
                    + str(restore_ex)
                )

        flash(
            f"❌ فشل نشر ملف التحديث: {ex}"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # Save Manifest
    # --------------------------------------------------------
    #
    # نحتفظ بنسخة من Manifest القديم في الذاكرة.
    #
    # إذا فشل الحفظ الجديد:
    #
    #     نحاول إعادة Setup القديم
    #     ونحاول إعادة Manifest القديم
    #
    # حتى لا يصبح السيرفر في حالة غير متطابقة.
    #
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

        log(
            "manifest.json saved successfully."
        )

    except Exception as ex:

        log(
            "ERROR: Failed to save manifest: "
            + str(ex)
        )

        # ----------------------------------------------------
        # محاولة استعادة Manifest القديم
        # ----------------------------------------------------

        try:

            if old_manifest_exists and old_manifest_data:

                save_manifest(
                    old_manifest_data,
                    program_name
                )

                log(
                    "Previous manifest restored."
                )

            elif not old_manifest_exists:

                if os.path.isfile(
                    manifest_path
                ):

                    os.remove(
                        manifest_path
                    )

                log(
                    "New manifest removed because no previous manifest existed."
                )

        except Exception as manifest_restore_ex:

            log(
                "CRITICAL: Failed to restore previous manifest: "
                + str(manifest_restore_ex)
            )

        # ----------------------------------------------------
        # محاولة استعادة Setup القديم
        # ----------------------------------------------------

        try:

            if os.path.isfile(
                file_path
            ):

                os.remove(
                    file_path
                )

            if backup_setup_path and os.path.isfile(
                backup_setup_path
            ):

                os.replace(
                    backup_setup_path,
                    file_path
                )

                log(
                    "Previous Setup restored after manifest failure."
                )

        except Exception as restore_ex:

            log(
                "CRITICAL: Failed to restore previous Setup after manifest failure: "
                + str(restore_ex)
            )

        flash(
            f"❌ فشل إنشاء manifest.json: {ex}"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # Delete Backup
    # --------------------------------------------------------

    if backup_setup_path:

        remove_file_safely(
            backup_setup_path
        )

        log(
            "Previous Setup backup removed."
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

        if final_sha256.lower() != sha256.lower():

            raise ValueError(
                "SHA-256 للملف المنشور لا يطابق القيمة المحسوبة."
            )

        log(
            "Final Setup verification passed."
        )

    except Exception as ex:

        log(
            "CRITICAL: Final Setup verification failed: "
            + str(ex)
        )

        flash(
            "⚠️ تم نشر التحديث ولكن فشل التحقق النهائي من الملف."
        )

        return redirect(
            url_for("index")
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

    log(
        "=================================================="
    )

    flash(
        f"🚀 تم نشر Devspark ERP "
        f"بالإصدار {release_version} بنجاح."
    )

    return redirect(
        url_for("index")
    )


# ============================================================
# Manifest
# ============================================================

@app.route(
    "/manifest.json"
)
def manifest():

    program_name = DEFAULT_PROGRAM

    current_manifest = load_manifest(
        program_name
    )

    # --------------------------------------------------------
    # No Manifest
    # --------------------------------------------------------

    if not current_manifest:

        return jsonify({

            "product":
                DEFAULT_PRODUCT,

            "program":
                program_name,

            "version":
                "0.0.0",

            "minimumVersion":
                "0.0.0",

            "package":
                "",

            "packageUrl":
                "",

            "downloadUrl":
                "",

            "fileName":
                "",

            "size":
                0,

            "sha256":
                "",

            "releaseDate":
                "",

            "releaseNotes":
                "",

            "requiresRestart":
                False,

            "requiresDatabaseMigration":
                False
        })

    # --------------------------------------------------------
    # Copy Manifest
    # --------------------------------------------------------

    fixed_manifest = dict(
        current_manifest
    )

    # --------------------------------------------------------
    # Force HTTPS + Current Download URL
    # --------------------------------------------------------

    filename = (
        fixed_manifest.get(
            "package"
        )
        or
        fixed_manifest.get(
            "fileName"
        )
    )

    if filename:

        filename = os.path.basename(
            filename
        )

        fixed_url = build_download_url(
            program_name,
            filename
        )

        fixed_manifest[
            "package"
        ] = filename

        fixed_manifest[
            "fileName"
        ] = filename

        fixed_manifest[
            "packageUrl"
        ] = fixed_url

        fixed_manifest[
            "downloadUrl"
        ] = fixed_url

    # --------------------------------------------------------
    # Extra Safety:
    # Official Update Package Must Be EXE
    # --------------------------------------------------------

    if filename and not filename.lower().endswith(
        ".exe"
    ):

        log(
            "WARNING: Existing manifest points to a non-EXE."
        )

        log(
            "Filename: "
            + filename
        )

        fixed_manifest[
            "package"
        ] = ""

        fixed_manifest[
            "fileName"
        ] = ""

        fixed_manifest[
            "packageUrl"
        ] = ""

        fixed_manifest[
            "downloadUrl"
        ] = ""

        fixed_manifest[
            "size"
        ] = 0

        fixed_manifest[
            "sha256"
        ] = ""

    # --------------------------------------------------------
    # Verify Published File Exists
    # --------------------------------------------------------

    if filename:

        program_folder = get_program_folder(
            program_name
        )

        published_file_path = os.path.join(
            program_folder,
            filename
        )

        if not os.path.isfile(
            published_file_path
        ):

            log(
                "WARNING: Manifest package does not exist on disk: "
                + published_file_path
            )

            fixed_manifest[
                "packageUrl"
            ] = ""

            fixed_manifest[
                "downloadUrl"
            ] = ""

    return jsonify(
        fixed_manifest
    )


# ============================================================
# Latest Version - Legacy API
# ============================================================

@app.route(
    "/latest_version/<program_name>"
)
def latest_version(
    program_name
):

    program_name = sanitize_program_name(
        program_name
    )

    program_folder = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program_name
    )

    if not os.path.isdir(
        program_folder
    ):

        return jsonify({

            "latest_version":
                "0.0.0",

            "download_url":
                "",

            "sha256":
                "",

            "size":
                0
        })

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    current_manifest = load_manifest(
        program_name
    )

    if current_manifest:

        filename = (
            current_manifest.get(
                "package"
            )
            or
            current_manifest.get(
                "fileName"
            )
        )

        # النظام الجديد يقبل EXE فقط.
        if (
            not filename
            or
            not filename.lower().endswith(
                ".exe"
            )
        ):

            return jsonify({

                "latest_version":
                    current_manifest.get(
                        "version",
                        "0.0.0"
                    ),

                "download_url":
                    "",

                "sha256":
                    "",

                "size":
                    0
            })

        filename = os.path.basename(
            filename
        )

        full_path = os.path.join(
            program_folder,
            filename
        )

        if not os.path.isfile(
            full_path
        ):

            log(
                "WARNING: Manifest points to missing file: "
                + full_path
            )

            return jsonify({

                "latest_version":
                    current_manifest.get(
                        "version",
                        "0.0.0"
                    ),

                "download_url":
                    "",

                "sha256":
                    "",

                "size":
                    0
            })

        download_url = build_download_url(
            program_name,
            filename
        )

        return jsonify({

            "latest_version":
                current_manifest.get(
                    "version",
                    "0.0.0"
                ),

            "download_url":
                download_url,

            "sha256":
                current_manifest.get(
                    "sha256",
                    ""
                ),

            "size":
                current_manifest.get(
                    "size",
                    0
                )
        })

    # --------------------------------------------------------
    # Legacy Fallback
    # --------------------------------------------------------
    #
    # لا نبحث عن ZIP.
    #
    # نبحث فقط عن EXE يحمل إصدارًا.
    #
    # أمثلة:
    #
    # Devspark_Setup_1.0.1.exe
    # Devspark_v1.0.1.exe
    # Devspark-1.0.1.exe
    #
    # --------------------------------------------------------

    latest_file = None

    latest_ver = version.parse(
        "0.0.0"
    )

    pattern = re.compile(
        r"(?:^|[-_])v?"
        r"(\d+\.\d+\.\d+)"
        r"(?:[-_.]|$)",
        re.IGNORECASE
    )

    try:

        filenames = os.listdir(
            program_folder
        )

    except Exception:

        filenames = []

    for filename in filenames:

        if filename.lower() == "manifest.json":
            continue

        if filename.startswith("."):
            continue

        if not filename.lower().endswith(
            ".exe"
        ):
            continue

        match = pattern.search(
            filename
        )

        if not match:
            continue

        try:

            current_ver = version.parse(
                match.group(1)
            )

        except Exception:

            continue

        if current_ver > latest_ver:

            latest_ver = current_ver
            latest_file = filename

    if not latest_file:

        return jsonify({

            "latest_version":
                "0.0.0",

            "download_url":
                "",

            "sha256":
                "",

            "size":
                0
        })

    download_url = build_download_url(
        program_name,
        latest_file
    )

    full_path = os.path.join(
        program_folder,
        latest_file
    )

    try:

        size = get_file_size(
            full_path
        )

        sha256 = calculate_sha256(
            full_path
        )

    except Exception:

        size = 0
        sha256 = ""

    return jsonify({

        "latest_version":
            str(latest_ver),

        "download_url":
            download_url,

        "sha256":
            sha256,

        "size":
            size
    })


# ============================================================
# Health Check
# ============================================================

@app.route(
    "/health"
)
def health():

    return jsonify({

        "status":
            "ok",

        "service":
            "Devspark Update Server",

        "time":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "publicBaseUrl":
            PUBLIC_BASE_URL,

        "updatePackage":
            SETUP_FILENAME,

        "updateMode":
            "setup-exe"
    })


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    log(
        "=================================================="
    )

    log(
        "Devspark Update Server starting..."
    )

    log(
        "Port: "
        + str(port)
    )

    log(
        "Public Base URL: "
        + PUBLIC_BASE_URL
    )

    log(
        "Update package mode: SETUP EXE"
    )

    log(
        "Official Setup filename: "
        + SETUP_FILENAME
    )

    log(
        "=================================================="
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
