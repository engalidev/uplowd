from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import uuid
from packaging import version
app = Flask(__name__)
app.secret_key = "UPLOAD_MANAGER_SECRET"

# 🔐 باسورد الحذف (غيره كما تريد)
DELETE_PASSWORD = "123456"

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        program_name = request.form.get("program_name", "unnamed_program")
        program_folder = os.path.join(app.config["UPLOAD_FOLDER"], program_name)
        os.makedirs(program_folder, exist_ok=True)

        file = request.files.get("file")
        if file and file.filename:
            if file.filename.lower().endswith((".exe", ".setup", ".msi", ".zip", ".rar")):
                filename = f"{uuid.uuid4()}_{file.filename}"
                file.save(os.path.join(program_folder, filename))
                flash(f"✅ تم رفع {file.filename} بنجاح")
            else:
                flash("⚠️ امتداد الملف غير مدعوم")
        return redirect(url_for("index"))

    # عرض الملفات حسب البرامج
    programs = {}
    for prog in sorted(os.listdir(app.config["UPLOAD_FOLDER"]), reverse=True):
        prog_path = os.path.join(app.config["UPLOAD_FOLDER"], prog)
        if os.path.isdir(prog_path):
            files = sorted(os.listdir(prog_path), reverse=True)
            programs[prog] = files

    return render_template("index.html", programs=programs)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    password = request.form.get("password")

    if password != DELETE_PASSWORD:
        flash("❌ كلمة المرور غير صحيحة")
        return redirect(url_for("index"))

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash("🗑️ تم حذف البرنامج بنجاح")
    else:
        flash("⚠️ الملف غير موجود")

    return redirect(url_for("index"))
    
@app.route("/latest_version/<program_name>")
def latest_version(program_name):
    """
    إرجاع أحدث نسخة للبرنامج المحدد مع رابط التحميل
    يدعم الملفات: .exe, .setup, .msi, .zip, .rar
    """
    program_folder = os.path.join(app.config["UPLOAD_FOLDER"], program_name)
    if not os.path.exists(program_folder):
        return json.dumps({"latest_version": "0.0.0", "download_url": ""})

    files = os.listdir(program_folder)
    # نمط يبحث عن _v1.2.3.لاحقة
    pattern = r"_v(\d+\.\d+\.\d+)\.(exe|setup|msi|zip|rar)$"
    latest_ver = "0.0.0"
    latest_file = None

    for f in files:
        match = re.search(pattern, f, re.IGNORECASE)
        if match:
            ver = match.group(1)
            if version.parse(ver) > version.parse(latest_ver):
                latest_ver = ver
                latest_file = f

    if not latest_file:
        return json.dumps({"latest_version": "0.0.0", "download_url": ""})

    download_url = url_for(
        "download_file", filename=f"{program_name}/{latest_file}", _external=True
    )
    return json.dumps({
        "latest_version": latest_ver,
        "download_url": download_url
    })

if __name__ == "__main__":
    app.run(debug=True)
