from flask import Flask

from config import *

# ============================================================
# Routes
# ============================================================

from routes.admin import admin
from routes.user.main_routes import main


# ============================================================
# Flask Application
# ============================================================

app = Flask(__name__)

app.config.from_object("config")

app.secret_key = "ThisIsASecretKeyForSessions123!"


# ============================================================
# User Routes
# ============================================================

app.register_blueprint(main)


# ============================================================
# Admin Routes
# ============================================================

app.register_blueprint(
    admin,
    url_prefix="/admin"
)


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
