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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
# Allowed files
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

    _, ext = os.path.splitext(filename.lower())

    return ext in ALLOWED_EXTENSIONS


def calculate_sha256(file_path):
    """
    حساب SHA-256 للملف.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def get_file_size(file_path):
    return os.path.getsize(file_path)


def normalize_version(value, default="0.0.0"):
    """
    تحويل الإصدار إلى صيغة آمنة مثل:
    1
    1.0
    1.0.1
    """

    if not value:
        return default

    value = str(value).strip()

    match = re.search(
        r"(\d+(?:\.\d+){0,3})",
        value
    )

    if not match:
        return default

    parts = match.group(1).split(".")

    while len(parts) < 3:
        parts.append("0")

    return ".".join(parts[:3])


def get_manifest_path(program_name="Devspark"):
    """
    مسار Manifest الخاص بالبرنامج.
    """

    program_folder = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program_name
    )

    os.makedirs(program_folder, exist_ok=True)

    return os.path.join(
        program_folder,
        "manifest.json"
    )


def load_manifest(program_name="Devspark"):
    """
    قراءة Manifest الحالي.
    """

    manifest_path = get_manifest_path(program_name)

    if not os.path.exists(manifest_path):
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


def save_manifest(manifest, program_name="Devspark"):
    """
    حفظ Manifest.
    """

    manifest_path = get_manifest_path(program_name)

    temp_path = manifest_path + ".tmp"

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

    # استبدال الملف القديم بعد نجاح الكتابة
    os.replace(
        temp_path,
        manifest_path
    )


def find_latest_zip(program_name):
    """
    البحث عن أحدث ZIP اعتمادًا على رقم الإصدار.
    """

    program_folder = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program_name
    )

    if not os.path.isdir(program_folder):
        return None, "0.0.0"

    latest_file = None
    latest_version = version.parse("0.0.0")

    pattern = re.compile(
        r"(?:^|[-_])v?(\d+\.\d+\.\d+)(?:[-_.]|$)",
        re.IGNORECASE
    )

    for filename in os.listdir(program_folder):

        if filename.lower() == "manifest.json":
            continue

        if not filename.lower().endswith(".zip"):
            continue

        match = pattern.search(filename)

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

    return latest_file, str(latest_version)


def build_download_url(program_name, filename):
    """
    إنشاء رابط تحميل صحيح.
    """

    return url_for(
        "download_file",
        program=program_name,
        filename=filename,
        _external=True
    )


# ============================================================
# Main Management Page
# ============================================================

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        program_name = (
            request.form.get(
                "program_name",
                "Devspark"
            ).strip()
        )

        if not program_name:
            program_name = "Devspark"

        program_name = secure_filename(program_name)

        if not program_name:
            program_name = "Devspark"

        program_folder = os.path.join(
            app.config["UPLOAD_FOLDER"],
            program_name
        )

        os.makedirs(
            program_folder,
            exist_ok=True
        )

        file = request.files.get("file")

        if not file or not file.filename:
            flash("⚠️ لم يتم اختيار ملف.")
            return redirect(url_for("index"))

        original_filename = secure_filename(
            file.filename
        )

        if not allowed_file(original_filename):
            flash(
                "⚠️ امتداد الملف غير مدعوم. "
                "المسموح: EXE, SETUP, MSI, ZIP, RAR"
            )

            return redirect(url_for("index"))

        # منع تكرار الاسم بإضافة UUID
        filename = (
            f"{uuid.uuid4().hex}_"
            f"{original_filename}"
        )

        file_path = os.path.join(
            program_folder,
            filename
        )

        file.save(file_path)

        flash(
            f"✅ تم رفع {original_filename} بنجاح"
        )

        return redirect(url_for("index"))

    # ========================================================
    # عرض الملفات
    # ========================================================

    programs = {}

    if os.path.isdir(
        app.config["UPLOAD_FOLDER"]
    ):

        for prog in sorted(
            os.listdir(
                app.config["UPLOAD_FOLDER"]
            ),
            reverse=True
        ):

            prog_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                prog
            )

            if not os.path.isdir(prog_path):
                continue

            files = []

            for filename in sorted(
                os.listdir(prog_path),
                reverse=True
            ):

                if filename.lower() == "manifest.json":
                    continue

                files.append(filename)

            programs[prog] = files

    # قراءة Manifest الحالي
    manifest = load_manifest("Devspark")

    return render_template(
        "index.html",
        programs=programs,
        manifest=manifest
    )


# ============================================================
# Download
# ============================================================

@app.route(
    "/download/<program>/<path:filename>"
)
def download_file(program, filename):

    program = secure_filename(program)

    # تنظيف مسار الملف
    filename = os.path.basename(filename)

    return send_from_directory(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            program
        ),
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
def delete_file(program, filename):

    password = request.form.get(
        "password",
        ""
    )

    if password != DELETE_PASSWORD:
        flash("❌ كلمة المرور غير صحيحة")
        return redirect(url_for("index"))

    program = secure_filename(program)
    filename = os.path.basename(filename)

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program,
        filename
    )

    if os.path.isfile(file_path):

        try:
            os.remove(file_path)

            flash(
                f"🗑️ تم حذف {filename} بنجاح"
            )

        except Exception as ex:

            flash(
                f"❌ فشل حذف الملف: {ex}"
            )

    else:

        flash(
            "⚠️ الملف غير موجود"
        )

    return redirect(url_for("index"))


# ============================================================
# Publish Devspark Update
# ============================================================

@app.route(
    "/publish-update",
    methods=["POST"]
)
def publish_update():

    # --------------------------------------------------------
    # معلومات الإصدار
    # --------------------------------------------------------

    program_name = (
        request.form.get(
            "program_name",
            "Devspark"
        ).strip()
    )

    if not program_name:
        program_name = "Devspark"

    program_name = secure_filename(
        program_name
    )

    if not program_name:
        program_name = "Devspark"

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

    release_notes = (
        request.form.get(
            "release_notes",
            ""
        ).strip()
    )

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
    # ملف ZIP
    # --------------------------------------------------------

    file = request.files.get(
        "update_file"
    )

    if not file or not file.filename:

        flash(
            "❌ يجب اختيار ملف ZIP للتحديث."
        )

        return redirect(url_for("index"))

    original_filename = secure_filename(
        file.filename
    )

    if not original_filename.lower().endswith(".zip"):

        flash(
            "❌ ملف التحديث يجب أن يكون ZIP."
        )

        return redirect(url_for("index"))

    # --------------------------------------------------------
    # مجلد البرنامج
    # --------------------------------------------------------

    program_folder = os.path.join(
        app.config["UPLOAD_FOLDER"],
        program_name
    )

    os.makedirs(
        program_folder,
        exist_ok=True
    )

    # --------------------------------------------------------
    # اسم الملف
    # --------------------------------------------------------

    filename = (
        f"Devspark-{release_version}.zip"
    )

    file_path = os.path.join(
        program_folder,
        filename
    )

    # --------------------------------------------------------
    # تحقق من الإصدار الحالي
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

            if version.parse(
                release_version
            ) <= version.parse(
                current_version_text
            ):

                flash(
                    f"❌ الإصدار {release_version} "
                    f"ليس أحدث من الإصدار الحالي "
                    f"{current_version_text}."
                )

                return redirect(
                    url_for("index")
                )

        except Exception:

            flash(
                "❌ تعذر مقارنة أرقام الإصدارات."
            )

            return redirect(
                url_for("index")
            )

    # --------------------------------------------------------
    # حفظ ZIP
    # --------------------------------------------------------

    try:

        file.save(file_path)

    except Exception as ex:

        flash(
            f"❌ فشل حفظ ملف التحديث: {ex}"
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

        file_size = get_file_size(
            file_path
        )

    except Exception as ex:

        try:
            os.remove(file_path)
        except Exception:
            pass

        flash(
            f"❌ فشل حساب SHA-256: {ex}"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # رابط التحميل
    # --------------------------------------------------------

    package_url = build_download_url(
        program_name,
        filename
    )

    # --------------------------------------------------------
    # تاريخ الإصدار
    # --------------------------------------------------------

    release_date = datetime.now(
        timezone.utc
    ).isoformat()

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest = {

        "product": "Devspark ERP",

        "program": program_name,

        "version": release_version,

        "minimumVersion": minimum_version,

        "package": filename,

        "packageUrl": package_url,

        "downloadUrl": package_url,

        "fileName": filename,

        "size": file_size,

        "sha256": sha256,

        "releaseDate": release_date,

        "releaseNotes": release_notes,

        "requiresRestart": requires_restart,

        "requiresDatabaseMigration":
            requires_database_migration
    }

    # --------------------------------------------------------
    # حفظ Manifest
    # --------------------------------------------------------

    try:

        save_manifest(
            manifest,
            program_name
        )

    except Exception as ex:

        # حذف ZIP إذا فشل إنشاء Manifest
        try:
            os.remove(file_path)
        except Exception:
            pass

        flash(
            f"❌ فشل إنشاء manifest.json: {ex}"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # نجاح
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

    program_name = "Devspark"

    current_manifest = load_manifest(
        program_name
    )

    if not current_manifest:

        return jsonify({

            "product": "Devspark ERP",

            "program": program_name,

            "version": "0.0.0",

            "minimumVersion": "0.0.0",

            "package": "",

            "packageUrl": "",

            "downloadUrl": "",

            "fileName": "",

            "size": 0,

            "sha256": "",

            "releaseDate": "",

            "releaseNotes": "",

            "requiresRestart": False,

            "requiresDatabaseMigration": False
        })

    return jsonify(
        current_manifest
    )


# ============================================================
# Latest Version - Legacy API
# ============================================================

@app.route(
    "/latest_version/<program_name>"
)
def latest_version(program_name):

    program_name = secure_filename(
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

            "latest_version": "0.0.0",

            "download_url": ""
        })

    # --------------------------------------------------------
    # إذا كان هناك Manifest
    # --------------------------------------------------------

    current_manifest = load_manifest(
        program_name
    )

    if current_manifest:

        return jsonify({

            "latest_version":
                current_manifest.get(
                    "version",
                    "0.0.0"
                ),

            "download_url":
                current_manifest.get(
                    "packageUrl",
                    ""
                ),

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
    # النظام القديم
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

    for filename in os.listdir(
        program_folder
    ):

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

            "latest_version": "0.0.0",

            "download_url": ""
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

        "status": "ok",

        "service":
            "Devspark Update Server",

        "time":
            datetime.now(
                timezone.utc
            ).isoformat()
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
