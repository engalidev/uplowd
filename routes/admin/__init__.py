from flask import Blueprint


# ============================================================
# Admin Blueprint
# ============================================================

print("")
print("=" * 70)
print("DEVSPARK ADMIN BLUEPRINT STARTUP")
print("=" * 70)


admin = Blueprint(
    "admin",
    __name__
)


print("")
print("[ADMIN] Blueprint created successfully.")
print("[ADMIN] Blueprint name:")
print(admin.name)

print("")
print("[ADMIN] Blueprint import name:")
print(admin.import_name)


# ============================================================
# Admin Routes
# ============================================================

print("")
print("[ADMIN] Loading admin route modules...")


# ------------------------------------------------------------
# Login Routes
# ------------------------------------------------------------

try:

    from routes.admin import login

    print("")
    print("[ADMIN] OK: login.py loaded.")
    print("[ADMIN] Login module:")
    print(login.__file__)

except Exception as ex:

    print("")
    print("[ADMIN] ERROR: Failed to load login.py")
    print("[ADMIN] Exception:")
    print(repr(ex))

    raise


# ------------------------------------------------------------
# Dashboard Routes
# ------------------------------------------------------------

try:

    from routes.admin import dashboard

    print("")
    print("[ADMIN] OK: dashboard.py loaded.")
    print("[ADMIN] Dashboard module:")
    print(dashboard.__file__)

except Exception as ex:

    print("")
    print("[ADMIN] ERROR: Failed to load dashboard.py")
    print("[ADMIN] Exception:")
    print(repr(ex))

    raise


# ------------------------------------------------------------
# Upload Routes
# ------------------------------------------------------------

try:

    from routes.admin import uploads

    print("")
    print("[ADMIN] OK: uploads.py loaded.")
    print("[ADMIN] Uploads module:")
    print(uploads.__file__)

except Exception as ex:

    print("")
    print("[ADMIN] ERROR: Failed to load uploads.py")
    print("[ADMIN] Exception:")
    print(repr(ex))

    raise


# ============================================================
# Admin Blueprint Complete
# ============================================================

print("")
print("=" * 70)
print("DEVSPARK ADMIN BLUEPRINT LOADED SUCCESSFULLY")
print("=" * 70)
print("")
