"""Public website and per-program update API."""
import os
from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, render_template, send_from_directory
from services import storage as st

main = Blueprint("main", __name__)


def _json(data):
    resp = jsonify(data)
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _empty_manifest(name="", program_key=""):
    return {"product": name, "program": program_key, "programKey": program_key,
            "version": "0.0.0", "minimumVersion": "0.0.0",
            "package": "", "packageUrl": "", "downloadUrl": "", "fileName": "",
            "size": 0, "sha256": "", "releaseDate": "", "releaseNotes": "",
            "requiresRestart": False, "requiresDatabaseMigration": False}


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


def _send_release(slug, version, filename):
    # Maintain physical slug downloads for already-published manifests.
    if (not st.valid_slug(slug) or not st.VERSION_RE.fullmatch(version or "")
            or not filename or filename.startswith(".")
            or os.path.basename(filename) != filename):
        abort(404)
    path = st.program_dir(slug)
    if not path:
        abort(404)
    rdir = os.path.join(path, "releases", version)
    rec = st.read_json(os.path.join(rdir, "release.json"))
    if not rec or rec.get("fileName") != filename:
        abort(404)
    if not os.path.isfile(os.path.join(rdir, filename)):
        abort(404)
    return send_from_directory(rdir, filename, as_attachment=True,
                               conditional=True)


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


# New fixed identity endpoint. Never guess by program order.
@main.route("/api/updates/<program_key>/manifest.json")
def program_update_manifest(program_key):
    program = st.get_program_by_key(program_key)
    if not program:
        abort(404)
    data = st.manifest_for(program["slug"])
    if not data:
        return _json(_empty_manifest(program["name"], program["programKey"]))
    return _json(data)


# Legacy global endpoint: only the configured default identity is allowed.
@main.route("/manifest.json")
def manifest():
    program = st.get_program_by_key(st.DEFAULT_PROGRAM)
    if not program:
        return _json(_empty_manifest(program_key=st.DEFAULT_PROGRAM))
    return _json(st.manifest_for(program["slug"]) or
                 _empty_manifest(program["name"], program["programKey"]))


@main.route("/api/programs")
def api_programs():
    return _json({"programs": [
        {"slug": p["slug"], "programKey": p.get("programKey", ""),
         "name": p["name"], "category": p.get("category", ""),
         "description": p.get("description", ""),
         "version": p["latest"]["version"] if p["latest"] else None}
        for p in st.list_programs()]})


@main.route("/api/programs/<slug>/manifest.json")
def api_manifest(slug):
    program = st.get_program(slug)
    if not program:
        abort(404)
    return _json(st.manifest_for(program["slug"]) or
                 _empty_manifest(program["name"], program.get("programKey", "")))


@main.route("/latest_version/<slug>")
def latest_version(slug):
    program = st.get_program(slug)
    latest = program["latest"] if program else None
    if not latest:
        return _json({"program": slug, "version": "0.0.0", "downloadUrl": "",
                      "sha256": "", "size": 0})
    return _json({"program": program.get("programKey") or program["slug"],
                  "version": latest["version"],
                  "downloadUrl": st.download_url(program["slug"], latest["version"],
                                                 latest["fileName"]),
                  "sha256": latest.get("sha256", ""), "size": latest.get("size", 0)})


@main.route("/health")
def health():
    return _json({"status": "ok", "service": "BETACODE Update Server",
                  "time": datetime.now(timezone.utc).isoformat(),
                  "publicBaseUrl": st.PUBLIC_BASE_URL})
