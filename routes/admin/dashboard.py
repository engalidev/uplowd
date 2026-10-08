from flask import render_template

from routes.admin import admin, login_required
from services import storage as st


@admin.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "admin/admin_dashboard.html",
        stats=st.stats(),
        programs=st.list_programs()[:6],
        recent=st.recent_releases(6),
    )
