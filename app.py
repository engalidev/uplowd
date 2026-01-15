from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import uuid  # لإنشاء أسماء فريدة للملفات

app = Flask(__name__)

# مكان حفظ الملفات المرفوعة
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# صفحة البداية + رفع الملفات
@app.route('/', methods=['GET', 'POST'])
def index():
    download_link = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            # إعطاء الملف اسم فريد لتجنب الكتابة على الملفات السابقة
            filename = str(uuid.uuid4()) + "_" + file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # إنشاء رابط التحميل
            download_link = url_for('download_file', filename=filename)
    return render_template('index.html', download_link=download_link)

# رابط التحميل
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
