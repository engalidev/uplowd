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

# مهم:
# نستخدم HTTPS بشكل صريح لأن DevsparkUpdateService
# يرفض أي PackageUrl لا يستخدم HTTPS.
PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://uplowd-production.up.railway.app"
).rstrip("/")


DEFAULT_PROGRAM = "Devspark"


# ============================================================
# Allowed Files
# ============================================================

ALLOWED_EXTENSIONS = {
    ".exe",
    ".setup",
    ".msi",
    ".zip",
    ".rar"
}


# ============================================================
# Helpers
# ============================================================

def allowed_file(filename):
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

            sha256.update(chunk)

    return sha256.hexdigest()


def get_file_size(file_path):
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
    """

    if value is None:
        return default

    value = str(value).strip()

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
    قراءة إصدار والتحقق منه.
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

    except Exception:
        raise ValueError(
            f"رقم الإصدار في {field_name} غير صالح."
        )


def get_program_folder(
    program_name=DEFAULT_PROGRAM
):
    """
    الحصول على مجلد البرنامج.
    """

    program_name = secure_filename(
        program_name
    )

    if not program_name:
        program_name = DEFAULT_PROGRAM

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

            return json.load(f)

    except Exception:

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
        manifest_path +
        "." +
        uuid.uuid4().hex +
        ".tmp"
    )

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

    os.replace(
        temp_path,
        manifest_path
    )


def build_download_url(
    program_name,
    filename
):
    """
    إنشاء رابط تحميل HTTPS.

    مهم جدًا:
    DevsparkUpdateService يشترط HTTPS.
    """

    program_name = secure_filename(
        program_name
    )

    filename = os.path.basename(
        filename
    )

    return (
        f"{PUBLIC_BASE_URL}"
        f"/download/"
        f"{program_name}/"
        f"{filename}"
    )


def find_latest_zip(
    program_name
):
    """
    البحث عن أحدث ZIP اعتمادًا على الإصدار.
    """

    program_folder = get_program_folder(
        program_name
    )

    latest_file = None

    latest_version = version.parse(
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

        return None, "0.0.0"

    for filename in filenames:

        if filename.lower() == "manifest.json":
            continue

        if not filename.lower().endswith(".zip"):
            continue

        match = pattern.search(
            filename
        )

        if not match:
            continue

        try:

            current_version = version.parse(
                match.group(1)
            )

        except Exception:

            continue

        if current_version > latest_version:

            latest_version = current_version
            latest_file = filename

    return (
        latest_file,
        str(latest_version)
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

        program_name = (
            request.form.get(
                "program_name",
                DEFAULT_PROGRAM
            ).strip()
        )

        if not program_name:
            program_name = DEFAULT_PROGRAM

        program_name = secure_filename(
            program_name
        )

        if not program_name:
            program_name = DEFAULT_PROGRAM

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

        except Exception as ex:

            flash(
                f"❌ فشل رفع الملف: {ex}"
            )

            return redirect(
                url_for("index")
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

        for prog in sorted(
            os.listdir(upload_root),
            reverse=True
        ):

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

    program = secure_filename(
        program
    )

    if not program:
        return "Invalid program.", 400

    filename = os.path.basename(
        filename
    )

    if not filename:
        return "Invalid filename.", 400

    program_folder = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program
    )

    if not os.path.isdir(
        program_folder
    ):
        return "Program not found.", 404

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

    program = secure_filename(
        program
    )

    filename = os.path.basename(
        filename
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

            flash(
                f"🗑️ تم حذف {filename} بنجاح."
            )

        except Exception as ex:

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

    # --------------------------------------------------------
    # Program
    # --------------------------------------------------------

    program_name = (
        request.form.get(
            "program_name",
            DEFAULT_PROGRAM
        ).strip()
    )

    if not program_name:
        program_name = DEFAULT_PROGRAM

    program_name = secure_filename(
        program_name
    )

    if not program_name:
        program_name = DEFAULT_PROGRAM

    # --------------------------------------------------------
    # Version
    # --------------------------------------------------------

    raw_release_version = request.form.get(
        "version",
        ""
    )

    release_version = normalize_version(
        raw_release_version
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
    # ZIP
    # --------------------------------------------------------

    file = request.files.get(
        "update_file"
    )

    if not file or not file.filename:

        flash(
            "❌ يجب اختيار ملف ZIP للتحديث."
        )

        return redirect(
            url_for("index")
        )

    original_filename = secure_filename(
        file.filename
    )

    if not original_filename.lower().endswith(
        ".zip"
    ):

        flash(
            "❌ ملف التحديث يجب أن يكون ZIP."
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
    # Update Filename
    # --------------------------------------------------------

    filename = (
        f"Devspark-{release_version}.zip"
    )

    file_path = os.path.join(
        program_folder,
        filename
    )

    # --------------------------------------------------------
    # Current Manifest
    # --------------------------------------------------------

    current_manifest = load_manifest(
        program_name
    )

    if current_manifest:

        current_version_text = normalize_version(
            current_manifest.get(
                "version",
                "0.0.0"
            )
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
    # Save ZIP
    # --------------------------------------------------------

    try:

        file.save(
            file_path
        )

    except Exception as ex:

        flash(
            f"❌ فشل حفظ ملف التحديث: {ex}"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # Validate ZIP Size
    # --------------------------------------------------------

    try:

        file_size = get_file_size(
            file_path
        )

        if file_size <= 0:

            raise ValueError(
                "ملف ZIP فارغ."
            )

    except Exception as ex:

        try:
            os.remove(
                file_path
            )
        except Exception:
            pass

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
            file_path
        )

    except Exception as ex:

        try:
            os.remove(
                file_path
            )
        except Exception:
            pass

        flash(
            f"❌ فشل حساب SHA-256: {ex}"
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

    # تأكيد إضافي
    if not package_url.startswith(
        "https://"
    ):

        try:
            os.remove(
                file_path
            )
        except Exception:
            pass

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
            "Devspark ERP",

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
    # Save Manifest
    # --------------------------------------------------------

    try:

        save_manifest(
            manifest_data,
            program_name
        )

    except Exception as ex:

        try:
            os.remove(
                file_path
            )
        except Exception:
            pass

        flash(
            f"❌ فشل إنشاء manifest.json: {ex}"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

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

    if not current_manifest:

        return jsonify({

            "product":
                "Devspark ERP",

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
    # حماية إضافية:
    # إذا كان Manifest قديمًا ويحتوي HTTP،
    # نقوم بتصحيح روابطه عند عرضه.
    # --------------------------------------------------------

    fixed_manifest = dict(
        current_manifest
    )

    filename = fixed_manifest.get(
        "package"
    ) or fixed_manifest.get(
        "fileName"
    )

    if filename:

        fixed_url = build_download_url(
            program_name,
            filename
        )

        fixed_manifest[
            "packageUrl"
        ] = fixed_url

        fixed_manifest[
            "downloadUrl"
        ] = fixed_url

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

    program_name = secure_filename(
        program_name
    )

    if not program_name:

        return jsonify({

            "latest_version":
                "0.0.0",

            "download_url":
                ""
        })

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
                ""
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

        download_url = ""

        if filename:

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
    # Legacy
    # --------------------------------------------------------

    latest_file = None

    latest_ver = version.parse(
        "0.0.0"
    )

    pattern = re.compile(
        r"_v(\d+\.\d+\.\d+)"
        r"\.(exe|setup|msi|zip|rar)$",
        re.IGNORECASE
    )

    try:

        filenames = os.listdir(
            program_folder
        )

    except Exception:

        filenames = []

    for filename in filenames:

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
                ""
        })

    download_url = build_download_url(
        program_name,
        latest_file
    )

    return jsonify({

        "latest_version":
            str(latest_ver),

        "download_url":
            download_url
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
            PUBLIC_BASE_URL
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

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
