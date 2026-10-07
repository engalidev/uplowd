from flask import Flask
import os

from routes.admin import admin
from routes.user.main import main


# ============================================================
# Flask App
# ============================================================

app = Flask(__name__)

app.secret_key = "ThisIsASecretKeyForSessions123!"


# ============================================================
# RAILWAY FILE SYSTEM DIAGNOSTIC
# ============================================================

print("")
print("=" * 80)
print("DEVSPARK RAILWAY FILE SYSTEM DIAGNOSTIC")
print("=" * 80)

print("")
print("[1] Current Working Directory:")
print(os.getcwd())

print("")
print("[2] app.py Location:")
print(os.path.abspath(__file__))

print("")
print("[3] Flask Root Path:")
print(app.root_path)

print("")
print("[4] Flask Template Folder:")
print(app.template_folder)


# ============================================================
# /app CONTENT
# ============================================================

print("")
print("=" * 80)
print("PROJECT ROOT CONTENT")
print("=" * 80)

try:

    for item in sorted(os.listdir("/app")):

        full_path = os.path.join(
            "/app",
            item
        )

        if os.path.isdir(full_path):
            print(
                "[DIR ]",
                item
            )
        else:
            print(
                "[FILE]",
                item
            )

except Exception as ex:

    print("")
    print("[ERROR] Cannot read /app")
    print(repr(ex))


# ============================================================
# TEMPLATES DIRECTORY
# ============================================================

template_path = os.path.join(
    app.root_path,
    app.template_folder
)

print("")
print("=" * 80)
print("TEMPLATES DIRECTORY CHECK")
print("=" * 80)

print("")
print("[5] Template Path:")
print(
    os.path.abspath(template_path)
)

print("")
print("[6] Template Directory Exists:")

print(
    os.path.isdir(template_path)
)


# ============================================================
# ADMIN TEMPLATE DIRECTORY
# ============================================================

admin_template_path = os.path.join(
    template_path,
    "admin"
)

print("")
print("=" * 80)
print("ADMIN TEMPLATE DIRECTORY CHECK")
print("=" * 80)

print("")
print("[7] Admin Template Path:")

print(
    os.path.abspath(
        admin_template_path
    )
)

print("")
print("[8] Admin Directory Exists:")

print(
    os.path.isdir(
        admin_template_path
    )
)


# ============================================================
# ADMIN LOGIN TEMPLATE
# ============================================================

admin_login_path = os.path.join(
    admin_template_path,
    "admin_login.html"
)

print("")
print("=" * 80)
print("ADMIN LOGIN TEMPLATE CHECK")
print("=" * 80)

print("")
print("[9] Expected File:")

print(
    os.path.abspath(
        admin_login_path
    )
)

print("")
print("[10] File Exists:")

print(
    os.path.isfile(
        admin_login_path
    )
)


# ============================================================
# LIST ADMIN TEMPLATES
# ============================================================

print("")
print("=" * 80)
print("ADMIN TEMPLATE FILES")
print("=" * 80)

if os.path.isdir(admin_template_path):

    try:

        files = sorted(
            os.listdir(
                admin_template_path
            )
        )

        if not files:

            print("")
            print(
                "[ADMIN] Directory is EMPTY."
            )

        else:

            for filename in files:

                full_path = os.path.join(
                    admin_template_path,
                    filename
                )

                if os.path.isfile(full_path):

                    print(
                        "[FILE]",
                        filename
                    )

                elif os.path.isdir(full_path):

                    print(
                        "[DIR ]",
                        filename
                    )

    except Exception as ex:

        print("")
        print(
            "[ERROR] Cannot read admin templates."
        )

        print(
            repr(ex)
        )

else:

    print("")
    print(
        "[ERROR] templates/admin DOES NOT EXIST!"
    )


# ============================================================
# ALL TEMPLATES RECURSIVELY
# ============================================================

print("")
print("=" * 80)
print("ALL TEMPLATE FILES RECURSIVELY")
print("=" * 80)

if os.path.isdir(template_path):

    try:

        found_templates = False

        for root, dirs, files in os.walk(
            template_path
        ):

            for filename in sorted(files):

                found_templates = True

                full_path = os.path.join(
                    root,
                    filename
                )

                relative_path = os.path.relpath(
                    full_path,
                    template_path
                )

                print(
                    "[TEMPLATE]",
                    relative_path
                )

        if not found_templates:

            print("")
            print(
                "[ERROR] No template files found!"
            )

    except Exception as ex:

        print("")
        print(
            "[ERROR] Failed to scan templates."
        )

        print(
            repr(ex)
        )

else:

    print("")
    print(
        "[ERROR] Template directory does not exist."
    )


# ============================================================
# REGISTER BLUEPRINTS
# ============================================================

print("")
print("=" * 80)
print("REGISTERING BLUEPRINTS")
print("=" * 80)

app.register_blueprint(main)

app.register_blueprint(
    admin,
    url_prefix="/admin"
)

print("")
print("[OK] Main blueprint registered.")

print(
    "[OK] Admin blueprint registered."
)


# ============================================================
# ROUTES
# ============================================================

print("")
print("=" * 80)
print("REGISTERED ROUTES")
print("=" * 80)

for rule in sorted(
    app.url_map.iter_rules(),
    key=lambda x: str(x)
):

    print(
        str(rule),
        sorted(rule.methods)
    )


# ============================================================
# FINAL RESULT
# ============================================================

print("")
print("=" * 80)
print("FINAL TEMPLATE DIAGNOSTIC")
print("=" * 80)

if os.path.isfile(admin_login_path):

    print("")
    print(
        "SUCCESS: admin_login.html EXISTS IN RAILWAY."
    )

    print(
        os.path.abspath(
            admin_login_path
        )
    )

else:

    print("")
    print(
        "ERROR: admin_login.html DOES NOT EXIST IN RAILWAY."
    )

    print("")
    print(
        "Expected:"
    )

    print(
        os.path.abspath(
            admin_login_path
        )
    )

print("")
print("=" * 80)
print("DEVSPARK RAILWAY DIAGNOSTIC COMPLETE")
print("=" * 80)
print("")


# ============================================================
# LOCAL RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
