import os
import random
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = Flask(__name__, template_folder="templates")

# =====================
# ANA SAYFA
# =====================
@app.route("/")
def home():
    return render_template("index.html")

# =====================
# ANALİZ (AI SIMULATED)
# =====================
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")
    email = data.get("email", "")

    risk = random.randint(20, 95)

    if "öldü" in text.lower() or "şok" in text.lower():
        risk += 15

    risk = min(risk, 100)

    if risk > 70:
        status = "Tehlikeli"
    elif risk < 40:
        status = "Güvenli"
    else:
        status = "Şüpheli"

    # MAIL
    if email and risk > 70:
        try:
            send_mail(email, text, risk, status)
        except Exception as e:
            print("Mail hata:", e)

    return jsonify({"risk": risk, "status": status})

# =====================
# SOSYAL MEDYA
# =====================
@app.route("/api/social")
def social():
    data = [
        {"platform": "twitter", "text": "Seçim sonuçları değiştirildi iddiası", "risk": 82},
        {"platform": "instagram", "text": "Ünlü kişi öldü haberi", "risk": 65},
        {"platform": "tiktok", "text": "Gizli teknoloji videosu", "risk": 45},
        {"platform": "facebook", "text": "Aşı zararlı iddiası", "risk": 78}
    ]
    return jsonify(data)

# =====================
# VIDEO ANALİZ
# =====================
@app.route("/api/video", methods=["POST"])
def video():
    return jsonify({
        "score": random.randint(30, 95)
    })

# =====================
# MAIL
# =====================
def send_mail(to_email, text, risk, status):
    sender = os.getenv("MAIL_USER")
    password = os.getenv("MAIL_PASS")

    if not sender or not password:
        return

    msg = MIMEText(f"""
DEFANS PRO ANALİZ

Metin:
{text}

Risk: %{risk}
Durum: {status}
""")

    msg["Subject"] = "⚠️ Riskli İçerik"
    msg["From"] = sender
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()

# =====================
# RUN
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)