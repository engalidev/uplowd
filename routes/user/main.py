```python
from flask import (
    Blueprint,
    render_template,
    send_from_directory,
    jsonify,
    abort
)

import os
import re
import json

from datetime import datetime, timezone

from packaging import version


# ============================================================
# User Blueprint
# ============================================================

main = Blueprint(
    "main",
    __name__
)


# ============================================================
# Configuration
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://uplowd-production.up.railway.app"
).rstrip("/")


DEFAULT_PROGRAM = "Devspark"

DEFAULT_PRODUCT = "Devspark ERP"

SETUP_FILENAME = "Devspark_Setup.exe"


# ============================================================
# Helpers
# ============================================================

def sanitize_program_name(
    program_name
):

    program_name = str(
        program_name or ""
    ).strip()

    if not program_name:

        program_name = DEFAULT_PROGRAM

    # منع Path Traversal

    program_name = os.path.basename(
        program_name
    )

    if (
        program_name in (
            "",
            ".",
            ".."
        )
    ):

        program_name = DEFAULT_PROGRAM

    return program_name


def get_program_folder(
    program_name=DEFAULT_PROGRAM
):

    program_name = sanitize_program_name(
        program_name
    )

    return os.path.join(
        UPLOAD_FOLDER,
        program_name
    )


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

        with open(
            manifest_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if not isinstance(
            data,
            dict
        ):

            return None

        return data

    except Exception as ex:

        print(
            "Failed to load manifest:",
            ex,
            flush=True
        )

        return None


def build_download_url(
    program_name,
    filename
):

    program_name = sanitize_program_name(
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


def is_valid_exe(
    filename
):

    if not filename:

        return False

    return (
        filename.lower()
        .endswith(".exe")
    )


# ============================================================
# Home
# ============================================================

@main.route(
    "/"
)
def index():

    manifest = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "user/dashbord.html",
        manifest=manifest,
        current_year=datetime.now().year
    )


# ============================================================
# Dashboard
# ============================================================

@main.route(
    "/dashboard"
)
def dashboard():

    manifest = load_manifest(
        DEFAULT_PROGRAM
    )

    return render_template(
        "user/dashbord.html",
        manifest=manifest,
        current_year=datetime.now().year
    )


# ============================================================
# Download
# ============================================================

@main.route(
    "/download/<program>/<path:filename>"
)
def download(
    program,
    filename
):

    program = sanitize_program_name(
        program
    )

    # منع Path Traversal

    filename = os.path.basename(
        filename
    )

    if not filename:

        abort(404)

    program_folder = get_program_folder(
        program
    )

    file_path = os.path.join(
        program_folder,
        filename
    )

    if not os.path.isfile(
        file_path
    ):

        abort(404)

    return send_from_directory(
        program_folder,
        filename,
        as_attachment=True
    )


# ============================================================
# Manifest
# ============================================================

@main.route(
    "/manifest.json"
)
def manifest():

    program_name = DEFAULT_PROGRAM

    data = load_manifest(
        program_name
    )

    if not data:

        data = {

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
        }


    data = dict(
        data
    )


    # ========================================================
    # Official Package
    # ========================================================

    data["program"] = (
        program_name
    )

    data["product"] = (
        data.get(
            "product"
        )
        or
        DEFAULT_PRODUCT
    )


    filename = (
        data.get(
            "fileName"
        )
        or
        data.get(
            "package"
        )
        or
        SETUP_FILENAME
    )


    filename = os.path.basename(
        filename
    )


    # ========================================================
    # Only EXE Updates
    # ========================================================

    if not is_valid_exe(
        filename
    ):

        filename = ""

        data["package"] = ""

        data["fileName"] = ""

        data["packageUrl"] = ""

        data["downloadUrl"] = ""

        data["size"] = 0

        data["sha256"] = ""

    else:

        data["package"] = (
            filename
        )

        data["fileName"] = (
            filename
        )

        package_url = build_download_url(
            program_name,
            filename
        )

        data["packageUrl"] = (
            package_url
        )

        data["downloadUrl"] = (
            package_url
        )


        # ====================================================
        # Verify File
        # ====================================================

        file_path = os.path.join(
            get_program_folder(
                program_name
            ),
            filename
        )


        if not os.path.isfile(
            file_path
        ):

            data["package"] = ""

            data["fileName"] = ""

            data["packageUrl"] = ""

            data["downloadUrl"] = ""

            data["size"] = 0

            data["sha256"] = ""


    return jsonify(
        data
    )


# ============================================================
# Legacy Latest Version API
# ============================================================

@main.route(
    "/latest_version/<program_name>"
)
def latest_version(
    program_name
):

    program_name = sanitize_program_name(
        program_name
    )


    data = load_manifest(
        program_name
    )


    # ========================================================
    # Manifest
    # ========================================================

    if data:

        filename = (
            data.get(
                "fileName"
            )
            or
            data.get(
                "package"
            )
            or
            ""
        )


        if is_valid_exe(
            filename
        ):

            file_path = os.path.join(
                get_program_folder(
                    program_name
                ),
                os.path.basename(
                    filename
                )
            )


            if os.path.isfile(
                file_path
            ):

                return jsonify({

                    "program":
                        program_name,

                    "version":
                        normalize_version(
                            data.get(
                                "version",
                                "0.0.0"
                            )
                        ),

                    "downloadUrl":
                        build_download_url(
                            program_name,
                            filename
                        ),

                    "sha256":
                        data.get(
                            "sha256",
                            ""
                        ),

                    "size":
                        data.get(
                            "size",
                            0
                        )

                })


    # ========================================================
    # Legacy Filename Scan
    # ========================================================

    program_folder = get_program_folder(
        program_name
    )


    if not os.path.isdir(
        program_folder
    ):

        return jsonify({

            "program":
                program_name,

            "version":
                "0.0.0",

            "downloadUrl":
                "",

            "sha256":
                "",

            "size":
                0

        })


    candidates = []


    try:

        filenames = os.listdir(
            program_folder
        )

    except Exception:

        filenames = []


    # ========================================================
    # Search EXE Files
    # ========================================================

    pattern = re.compile(
        r"""
        (?:
            _|
            -|
            v
        )?
        (
            \d+
            \.\d+
            (?:\.\d+)?
        )
        """,
        re.IGNORECASE |
        re.VERBOSE
    )


    for filename in filenames:

        if not is_valid_exe(
            filename
        ):

            continue


        file_path = os.path.join(
            program_folder,
            filename
        )


        if not os.path.isfile(
            file_path
        ):

            continue


        match = pattern.search(
            filename
        )


        if not match:

            continue


        version_text = normalize_version(
            match.group(1)
        )


        try:

            parsed_version = version.parse(
                version_text
            )

        except Exception:

            continue


        candidates.append({

            "version":
                parsed_version,

            "versionText":
                version_text,

            "filename":
                filename,

            "filePath":
                file_path

        })


    # ========================================================
    # No Legacy Files
    # ========================================================

    if not candidates:

        return jsonify({

            "program":
                program_name,

            "version":
                "0.0.0",

            "downloadUrl":
                "",

            "sha256":
                "",

            "size":
                0

        })


    # ========================================================
    # Latest Legacy Version
    # ========================================================

    latest = max(
        candidates,
        key=lambda item:
            item["version"]
    )


    latest_file = (
        latest["filePath"]
    )


    size = 0


    try:

        size = os.path.getsize(
            latest_file
        )

    except Exception:
        pass


    return jsonify({

        "program":
            program_name,

        "version":
            latest["versionText"],

        "downloadUrl":
            build_download_url(
                program_name,
                latest["filename"]
            ),

        "sha256":
            "",

        "size":
            size

    })


# ============================================================
# Health
# ============================================================

@main.route(
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
```
