import os
import random
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = Flask(__name__, template_folder="templates")
CORS(app)

# =========================
# 🔥 ANA SAYFA (404 FIX)
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# 🔥 AI ANALİZ
# =========================
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")
    email = data.get("email", "")

    # Fake AI risk (istersen sonra gerçek AI bağlarız)
    risk = random.randint(10, 95)

    if risk > 70:
        status = "Tehlikeli"
    elif risk < 40:
        status = "Güvenli"
    else:
        status = "Şüpheli"

    # 📧 MAIL GÖNDER
    try:
        send_mail(email, text, risk, status)
    except Exception as e:
        print("Mail hatası:", e)

    return jsonify({
        "risk": risk,
        "status": status
    })

# =========================
# 🔥 SOSYAL MEDYA (API’siz)
# =========================
@app.route("/api/social")
def social():
    posts = [
        {"platform": "twitter", "text": "Şok haber! büyük olay oldu", "risk": random.randint(40,90)},
        {"platform": "instagram", "text": "Breaking news dünya karıştı", "risk": random.randint(20,80)},
        {"platform": "tiktok", "text": "Bu videoyu kaldırmadan izle", "risk": random.randint(50,95)},
        {"platform": "facebook", "text": "Resmi açıklama geldi", "risk": random.randint(10,60)}
    ]

    return jsonify(posts)

# =========================
# 🎥 DEEPFAKE (Simülasyon)
# =========================
@app.route("/api/video", methods=["POST"])
def video():
    data = request.json
    url = data.get("url")

    score = random.randint(30, 99)

    return jsonify({
        "score": score,
        "result": "Deepfake olabilir" if score > 60 else "Temiz görünüyor"
    })

# =========================
# 📧 MAIL SİSTEMİ (ENV)
# =========================
def send_mail(to_email, text, risk, status):
    sender = os.getenv("MAIL_USER")
    password = os.getenv("MAIL_PASS")

    if not sender or not password:
        print("Mail env yok")
        return

    msg = MIMEText(f"""
Analiz Sonucu:

Metin:
{text}

Risk: %{risk}
Durum: {status}
""")

    msg["Subject"] = "DEFANS PRO Analiz Sonucu"
    msg["From"] = sender
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()

# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)