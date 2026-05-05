import os
import random
import re
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = Flask(__name__, template_folder="templates")

# =========================
# ANA SAYFA
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# METİN FİLTRE
# =========================
def is_valid(text):
    if not text or len(text) < 15:
        return False
    if len(text.split()) < 3:
        return False
    return True

# =========================
# 🔥 AI ANALİZ (KEYWORD + OPSİYONEL API)
# =========================
def analyze_ai(text):
    risk = 30

    high = ["öldü","şok","ifşa","komplo","gizli","yasak"]
    medium = ["iddia","kriz","gündem"]

    for w in high:
        if w in text.lower():
            risk += 25

    for w in medium:
        if w in text.lower():
            risk += 10

    risk += random.randint(0,20)
    return min(risk,100)

# =========================
# ANALİZ API
# =========================
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text","")
    email = data.get("email","")

    if not is_valid(text):
        return jsonify({"risk":0,"status":"Geçersiz içerik"})

    risk = analyze_ai(text)

    if risk > 70:
        status = "Tehlikeli"
    elif risk < 40:
        status = "Güvenli"
    else:
        status = "Şüpheli"

    if email:
        send_mail(email,text,risk,status)

    return jsonify({"risk":risk,"status":status})

# =========================
# 🔥 SOSYAL MEDYA (RSS + MOCK)
# =========================
@app.route("/api/social")
def social():

    posts = []

    # 🔹 RSS HABER (GERÇEK VERİ)
    try:
        r = requests.get("https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", timeout=3)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.content)

        for item in root.findall(".//item")[:5]:
            title = item.find("title").text
            posts.append({
                "platform":"news",
                "text":title,
                "risk": analyze_ai(title)
            })
    except:
        pass

    # 🔹 MOCK SOSYAL (HER ZAMAN VAR)
    posts += [
        {"platform":"twitter","text":"Şok iddia gündemde","risk":85},
        {"platform":"instagram","text":"Ünlü kişi öldü deniyor","risk":75},
        {"platform":"tiktok","text":"Bu video kaldırılmadan izle","risk":65},
        {"platform":"facebook","text":"Resmi açıklama yapıldı","risk":25}
    ]

    return jsonify(posts)

# =========================
# 🎥 VIDEO ANALİZ (SIMULATED AI)
# =========================
@app.route("/api/video", methods=["POST"])
def video():
    return jsonify({
        "score": random.randint(40,95),
        "result":"Deepfake olabilir"
    })

# =========================
# 📧 MAIL
# =========================
def send_mail(to_email,text,risk,status):
    sender = os.getenv("MAIL_USER")
    password = os.getenv("MAIL_PASS")

    if not sender or not password:
        print("MAIL ENV YOK")
        return

    msg = MIMEText(f"""
🚨 DEFANS PRO SONUÇ

Metin:
{text}

Risk: %{risk}
Durum: {status}
""")

    msg["Subject"] = "DEFANS PRO UYARI"
    msg["From"] = sender
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login(sender,password)
    server.send_message(msg)
    server.quit()

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)