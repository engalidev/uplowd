from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# صفحة البداية
@app.route('/')
def index():
    return render_template('index.html')

# رابط التحميل
@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'downloads'), filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
