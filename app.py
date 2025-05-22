# 📸 ระบบถ่ายภาพ + แชร์ภาพด้วย QR Code (เหมือน Piufoto)
# เวอร์ชันสมบูรณ์ขั้นสูง (Gallery + ค้นหา + Email แชร์ + รองรับวิดีโอ)

from flask import Flask, request, send_file, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
import qrcode
from PIL import Image, ImageDraw
import uuid
import smtplib
from email.message import EmailMessage
import mimetypes
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
QR_FOLDER = 'qrcodes'
TEMPLATES_FOLDER = 'templates'
BRANDING_IMAGE = 'frame.png'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'mov', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return redirect(url_for('gallery'))

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    email = request.form.get('email')
    if file and allowed_file(file.filename):
        uid = str(uuid.uuid4())[:8]
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{uid}.{ext}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        if ext in {'jpg', 'jpeg', 'png'}:
            final_image = add_branding(filepath)
            final_image.save(filepath)

        img_url = url_for('download_image', filename=filename, _external=True)
        qr_img_path = os.path.join(QR_FOLDER, uid + ".png")
        qrcode.make(img_url).save(qr_img_path)

        if email:
            send_email_with_attachment(email, filepath)

        return redirect(url_for('show_qr', filename=filename, qr_file=uid + ".png"))
    return "Invalid file", 400

@app.route('/download/<filename>')
def download_image(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/qr/<filename>/<qr_file>')
def show_qr(filename, qr_file):
    return render_template('qr_page.html', filename=filename, qr_path=f'qrcodes/{qr_file}')

@app.route('/gallery')
def gallery():
    search = request.args.get('search', '').lower()
    files = [f for f in os.listdir(UPLOAD_FOLDER) if search in f.lower()]
    return render_template('gallery.html', files=sorted(files, reverse=True))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_branding(img_path):
    base = Image.open(img_path).convert("RGBA")
    overlay = Image.open(BRANDING_IMAGE).convert("RGBA")
    overlay = overlay.resize(base.size)
    combined = Image.alpha_composite(base, overlay)
    return combined

def send_email_with_attachment(to_email, file_path):
    msg = EmailMessage()
    msg['Subject'] = 'Your Photo from Event'
    msg['From'] = 'noreply@yourdomain.com'
    msg['To'] = to_email

    msg.set_content('Thank you for joining our event! Find your photo attached.')

    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type, mime_subtype = mime_type.split('/')

    with open(file_path, 'rb') as f:
        msg.add_attachment(
            f.read(),
            maintype=mime_type,
            subtype=mime_subtype,
            filename=os.path.basename(file_path)
        )

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('your_email@gmail.com', 'your_email_password')  # ปรับให้ใช้ env var จริง
        smtp.send_message(msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
