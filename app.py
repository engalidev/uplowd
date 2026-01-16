from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import uuid

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
        file = request.files.get("file")
        if file:
            filename = f"{uuid.uuid4()}_{file.filename}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            flash("✅ تم رفع البرنامج بنجاح")
        return redirect(url_for("index"))

    files = sorted(os.listdir(app.config["UPLOAD_FOLDER"]), reverse=True)
    return render_template("index.html", files=files)


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
    
@app.route("/latest_version")
def latest_version():
    files = sorted(os.listdir(app.config["UPLOAD_FOLDER"]), reverse=True)
    if not files:
        return json.dumps({"latest_version": "1.0.0", "download_url": ""})
    
    latest_file = files[0]  # آخر نسخة مرفوعة
    version = latest_file.split("_")[-1].replace(".exe", "")  # مثلا لو الملف باسم unique_hash_v1.2.3.exe

    download_url = url_for("download_file", filename=latest_file, _external=True)

    return json.dumps({
        "latest_version": version,
        "download_url": download_url
    })

if __name__ == "__main__":
    app.run(debug=True)
