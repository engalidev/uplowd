import os
from datetime import datetime, timezone

from flask import (Blueprint, abort, jsonify, render_template,
                   send_from_directory)

from services import storage as st

main = Blueprint("main", __name__)


def _json(data):
    resp = jsonify(data)
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _default_slug():
    path = st.program_dir(st.DEFAULT_PROGRAM)
    if path:
        return os.path.basename(path)
    items = st.list_programs()
    return items[0]["slug"] if items else None


def _empty_manifest(name="", slug=""):
    return {
        "product": name, "program": slug, "version": "0.0.0", "minimumVersion": "0.0.0",
        "package": "", "packageUrl": "", "downloadUrl": "", "fileName": "",
        "size": 0, "sha256": "", "releaseDate": "", "releaseNotes": "",
        "requiresRestart": False, "requiresDatabaseMigration": False,
    }


# ------------------------------------------------------------------ Pages
@main.route("/")
def index():
    programs = st.list_programs()
    return render_template("user/index.html", programs=programs[:6],
                           recent=st.recent_releases(6), stats=st.stats())


@main.route("/programs")
def programs_page():
    items = st.list_programs()
    categories = sorted({p["category"] for p in items if p.get("category")})
    return render_template("user/programs.html", programs=items, categories=categories)


@main.route("/programs/<slug>")
def program_page(slug):
    program = st.get_program(slug)
    if not program:
        abort(404)
    return render_template("user/program_detail.html", p=program)


@main.route("/updates")
def updates():
    return render_template("user/updates.html", releases=st.recent_releases(100))


# ------------------------------------------------------------------ Downloads
def _send_release(slug, version, filename):
    path = st.program_dir(slug)
    if not path or filename.startswith("."):
        abort(404)
    rdir = os.path.join(path, "releases", os.path.basename(version))
    rec = st.read_json(os.path.join(rdir, "release.json"))
    if not rec or rec.get("fileName") != filename:
        abort(404)
    return send_from_directory(rdir, filename, as_attachment=True)


@main.route("/download/<slug>/<version>/<filename>")
def download(slug, version, filename):
    return _send_release(slug, version, filename)


@main.route("/download/<slug>/<filename>")
def download_legacy(slug, filename):
    program = st.get_program(slug)
    if not program:
        abort(404)
    for rel in program["releases"]:
        if rel["fileName"] == filename:
            return _send_release(program["slug"], rel["version"], filename)
    abort(404)


# ------------------------------------------------------------------ API
@main.route("/manifest.json")
def manifest():
    slug = _default_slug()
    data = st.manifest_for(slug) if slug else None
    return _json(data or _empty_manifest(slug=slug or ""))


@main.route("/api/programs")
def api_programs():
    return _json({"programs": [
        {"slug": p["slug"], "name": p["name"], "category": p.get("category", ""),
         "description": p.get("description", ""),
         "version": p["latest"]["version"] if p["latest"] else None}
        for p in st.list_programs()
    ]})


@main.route("/api/programs/<slug>/manifest.json")
def api_manifest(slug):
    program = st.get_program(slug)
    if not program:
        abort(404)
    data = st.manifest_for(program["slug"])
    return _json(data or _empty_manifest(program["name"], program["slug"]))


@main.route("/latest_version/<slug>")
def latest_version(slug):
    program = st.get_program(slug)
    latest = program["latest"] if program else None
    if not latest:
        return _json({"program": slug, "version": "0.0.0", "downloadUrl": "", "sha256": "", "size": 0})
    return _json({
        "program": program["slug"],
        "version": latest["version"],
        "downloadUrl": st.download_url(program["slug"], latest["version"], latest["fileName"]),
        "sha256": latest.get("sha256", ""),
        "size": latest.get("size", 0),
    })


@main.route("/health")
def health():
    return _json({
        "status": "ok",
        "service": "Devspark Update Server",
        "time": datetime.now(timezone.utc).isoformat(),
        "publicBaseUrl": st.PUBLIC_BASE_URL,
    })
