from flask import Flask
import os


# ============================================================
# Routes
# ============================================================

from routes.admin import admin
from routes.user.main import main


# ============================================================
# Flask Application
# ============================================================

app = Flask(__name__)


# ============================================================
# Session Secret Key
# ============================================================

app.secret_key = "ThisIsASecretKeyForSessions123!"


# ============================================================
# Debug / Diagnostic Information
# ============================================================

print("")
print("=" * 70)
print("DEVSPARK FLASK STARTUP DIAGNOSTIC")
print("=" * 70)

# ------------------------------------------------------------
# Current Working Directory
# ------------------------------------------------------------

print("")
print("[1] Current Working Directory:")
print(os.getcwd())

# ------------------------------------------------------------
# Python File Location
# ------------------------------------------------------------

print("")
print("[2] app.py Location:")
print(os.path.abspath(__file__))

# ------------------------------------------------------------
# Application Root Path
# ------------------------------------------------------------

print("")
print("[3] Flask app.root_path:")
print(app.root_path)

# ------------------------------------------------------------
# Template Folder
# ------------------------------------------------------------

print("")
print("[4] Flask Template Folder:")
print(app.template_folder)

template_path = os.path.join(
    app.root_path,
    app.template_folder
)

print("")
print("[5] Full Template Path:")
print(os.path.abspath(template_path))

print("")
print("[6] Template Folder Exists:")
print(os.path.exists(template_path))

# ============================================================
# Check Admin Templates
# ============================================================

print("")
print("=" * 70)
print("ADMIN TEMPLATE CHECK")
print("=" * 70)

admin_template_folder = os.path.join(
    template_path,
    "admin"
)

print("")
print("[7] Admin Template Folder:")
print(os.path.abspath(admin_template_folder))

print("")
print("[8] Admin Template Folder Exists:")
print(os.path.exists(admin_template_folder))


# ------------------------------------------------------------
# Admin Login Template
# ------------------------------------------------------------

admin_login_template = os.path.join(
    admin_template_folder,
    "admin_login.html"
)

print("")
print("[9] Admin Login Template:")
print(os.path.abspath(admin_login_template))

print("")
print("[10] Admin Login Template Exists:")
print(os.path.isfile(admin_login_template))


# ------------------------------------------------------------
# List Admin Templates
# ------------------------------------------------------------

print("")
print("[11] Admin Template Files:")

if os.path.isdir(admin_template_folder):

    try:

        admin_files = os.listdir(
            admin_template_folder
        )

        if admin_files:

            for filename in sorted(admin_files):

                full_path = os.path.join(
                    admin_template_folder,
                    filename
                )

                print(
                    "   - "
                    + filename
                    + " | "
                    + (
                        "FILE"
                        if os.path.isfile(full_path)
                        else "DIRECTORY"
                    )
                )

        else:

            print("   (EMPTY)")

    except Exception as ex:

        print(
            "   ERROR READING FOLDER:"
        )

        print(
            repr(ex)
        )

else:

    print(
        "   ADMIN TEMPLATE FOLDER DOES NOT EXIST!"
    )


# ============================================================
# Check All Templates
# ============================================================

print("")
print("=" * 70)
print("ALL TEMPLATE FILES")
print("=" * 70)

if os.path.isdir(template_path):

    for root, dirs, files in os.walk(
        template_path
    ):

        for filename in sorted(files):

            full_path = os.path.join(
                root,
                filename
            )

            relative_path = os.path.relpath(
                full_path,
                template_path
            )

            print(
                "   - "
                + relative_path
            )

else:

    print(
        "   TEMPLATE DIRECTORY DOES NOT EXIST!"
    )


# ============================================================
# Register User Routes
# ============================================================

app.register_blueprint(
    main
)


# ============================================================
# Register Admin Routes
# ============================================================

app.register_blueprint(
    admin,
    url_prefix="/admin"
)


# ============================================================
# Flask Registered Routes
# ============================================================

print("")
print("=" * 70)
print("REGISTERED FLASK ROUTES")
print("=" * 70)

for rule in sorted(
    app.url_map.iter_rules(),
    key=lambda x: str(x)
):

    methods = sorted(
        rule.methods
    )

    print(
        f"   {str(rule):<40} "
        f"{methods}"
    )


# ============================================================
# Final Diagnostic
# ============================================================

print("")
print("=" * 70)
print("FINAL DIAGNOSTIC RESULT")
print("=" * 70)

if os.path.isfile(admin_login_template):

    print("")
    print(
        "OK: admin_login.html EXISTS"
    )

    print(
        os.path.abspath(
            admin_login_template
        )
    )

else:

    print("")
    print(
        "ERROR: admin_login.html DOES NOT EXIST!"
    )

    print(
        "Flask will NOT be able to render:"
    )

    print(
        "admin/admin_login.html"
    )

print("")
print("=" * 70)
print("DEVSPARK FLASK STARTUP COMPLETE")
print("=" * 70)
print("")


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
