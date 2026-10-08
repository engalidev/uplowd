from flask import abort, flash, redirect, render_template, request, url_for

from routes.admin import admin, ajax_redirect, login_required
from services import storage as st
from services.storage import StorageError

CATEGORIES = ["إدارة مبيعات", "تعليم ومدارس", "صيدليات", "محاسبة", "مخازن", "مطاعم", "موارد بشرية", "أخرى"]


def _fields():
    f = request.form
    return (f.get("name", ""), f.get("description", ""), f.get("category", ""), f.get("icon", ""))


@admin.route("/programs")
@login_required
def programs():
    return render_template("admin/admin_programs.html",
                           programs=st.list_programs(), categories=CATEGORIES)


@admin.route("/programs/new", methods=["POST"])
@login_required
def program_create():
    name, description, category, icon = _fields()
    try:
        slug = st.create_program(name, request.form.get("slug", ""), description, category, icon)
    except StorageError as ex:
        flash(str(ex), "error")
        return redirect(url_for("admin.programs"))
    flash("تم إنشاء البرنامج. ارفع أول إصدار له الآن.", "success")
    return redirect(url_for("admin.program_detail", slug=slug))


@admin.route("/programs/<slug>")
@login_required
def program_detail(slug):
    program = st.get_program(slug)
    if not program:
        abort(404)
    return render_template("admin/admin_program_detail.html",
                           p=program, categories=CATEGORIES)


@admin.route("/programs/<slug>/edit", methods=["POST"])
@login_required
def program_edit(slug):
    name, description, category, icon = _fields()
    try:
        st.update_program(slug, name, description, category, icon)
        flash("تم حفظ بيانات البرنامج.", "success")
    except StorageError as ex:
        flash(str(ex), "error")
    return redirect(url_for("admin.program_detail", slug=slug))


@admin.route("/programs/<slug>/delete", methods=["POST"])
@login_required
def program_delete(slug):
    program = st.get_program(slug)
    if not program:
        abort(404)
    if request.form.get("confirm", "").strip().lower() != program["slug"].lower():
        flash("لم يتم الحذف: المعرّف المكتوب غير مطابق.", "error")
        return redirect(url_for("admin.program_detail", slug=slug))
    st.delete_program(slug)
    flash(f"تم حذف البرنامج «{program['name']}» وجميع إصداراته.", "success")
    return redirect(url_for("admin.programs"))


@admin.route("/programs/<slug>/release", methods=["POST"])
@login_required
def release_publish(slug):
    program = st.get_program(slug)
    if not program:
        abort(404)
    f = request.form
    try:
        rec = st.publish_release(
            program["slug"],
            request.files.get("update_file"),
            f.get("version", ""),
            f.get("minimum_version", ""),
            f.get("release_notes", ""),
            f.get("requires_restart") == "on",
            f.get("requires_database_migration") == "on",
        )
        flash(f"تم نشر «{program['name']}» بالإصدار {rec['version']}.", "success")
    except StorageError as ex:
        flash(str(ex), "error")
    except Exception as ex:  # noqa: BLE001
        print("[PUBLISH] unexpected error:", repr(ex), flush=True)
        flash("حدث خطأ غير متوقع أثناء النشر. راجع سجلات الخادم.", "error")
    return ajax_redirect(url_for("admin.program_detail", slug=program["slug"]))


@admin.route("/programs/<slug>/releases/<version>/delete", methods=["POST"])
@login_required
def release_delete(slug, version):
    try:
        st.delete_release(slug, version)
        flash(f"تم حذف الإصدار {version}.", "success")
    except StorageError as ex:
        flash(str(ex), "error")
    return redirect(url_for("admin.program_detail", slug=slug))
