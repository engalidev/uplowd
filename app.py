from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import uuid

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # ضروري لـ flash

# مكان حفظ الملفات المرفوعة
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# صفحة البداية + رفع الملفات
@app.route('/', methods=['GET', 'POST'])
def index():
    download_link = None
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    uploaded_files.sort(reverse=True)  # عرض أحدث الملفات أولاً

    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            # إعطاء الملف اسم فريد لتجنب الكتابة على الملفات السابقة
            unique_filename = str(uuid.uuid4()) + "_" + file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            flash(f"تم رفع الملف بنجاح: {file.filename}")
            return redirect(url_for('index'))  # إعادة تحميل الصفحة لتحديث القائمة

    return render_template('index.html', files=uploaded_files)

# رابط التحميل
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
