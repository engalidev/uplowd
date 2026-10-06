
from flask import Blueprint


# ============================================================
# Admin Blueprint
# ============================================================

admin = Blueprint(
    "admin",
    __name__
)


# ============================================================
# Admin Routes
# ============================================================

from routes.admin import login
from routes.admin import dashboard
from routes.admin import uploads
