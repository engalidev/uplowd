```python
from flask import Flask
from config import *
from models import db, Admin

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
# Database
# ============================================================

db.init_app(app)


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
# Database Initialization
# ============================================================

with app.app_context():

    db.create_all()

    # إنشاء المدير الافتراضي إذا لم يكن موجودًا
    if not Admin.query.first():

        default_admin = Admin(
            username="admin",
            password="1234"
        )

        db.session.add(default_admin)
        db.session.commit()

        print("Admin Created")


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
```
