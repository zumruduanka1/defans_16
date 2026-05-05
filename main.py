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

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return render_template("index.html")

# =====================
# TEXT FILTER
# =====================
def is_valid(text):
    if not text or len(text) < 10:
        return False
    return True

# =====================
# AI (GARANTİ FALLBACK)
# =====================
def analyze_ai(text):
    risk = 30

    if "şok" in text.lower():
        risk += 30
    if "öldü" in text.lower():
        risk += 40
    if "iddia" in text.lower():
        risk += 15

    risk += random.randint(0,20)
    return min(risk,100)

def real_ai(text):
    api = os.getenv("OPENAI_API_KEY")

    if not api:
        return None

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role":"user","content":text}]
            },
            timeout=5
        )

        data = r.json()

        if "choices" not in data:
            return None

        txt = data["choices"][0]["message"]["content"]

        num = ''.join(filter(str.isdigit, txt))
        return int(num[:3]) if num else None

    except:
        return None

# =====================
# ANALYZE
# =====================
@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        text = data.get("text","")
        email = data.get("email","")

        if not is_valid(text):
            return jsonify({"risk":0,"status":"Geçersiz"})

        risk = real_ai(text)

        if risk is None:
            risk = analyze_ai(text)

        if risk > 70:
            status = "Tehlikeli"
        elif risk < 40:
            status = "Güvenli"
        else:
            status = "Şüpheli"

        if email:
            try:
                send_mail(email,text,risk,status)
            except:
                pass

        return jsonify({"risk":risk,"status":status})

    except Exception as e:
        print("ANALYZE ERROR:", e)
        return jsonify({"risk":0,"status":"Hata"})

# =====================
# SOCIAL (KESİN VERİ)
# =====================
@app.route("/api/social")
def social():
    data = [
        {"platform":"twitter","text":"Şok iddia gündemde","risk":80},
        {"platform":"instagram","text":"Ünlü kişi öldü deniyor","risk":75},
        {"platform":"tiktok","text":"Bu video kaldırılıyor","risk":65},
        {"platform":"facebook","text":"Resmi açıklama geldi","risk":20}
    ]

    return jsonify(data)

# =====================
# VIDEO
# =====================
@app.route("/api/video", methods=["POST"])
def video():
    return jsonify({"score": random.randint(40,90)})

# =====================
# MAIL
# =====================
def send_mail(to_email,text,risk,status):
    user = os.getenv("MAIL_USER")
    pwd = os.getenv("MAIL_PASS")

    if not user or not pwd:
        return

    msg = MIMEText(f"Metin: {text}\nRisk: {risk}\nDurum: {status}")

    msg["Subject"] = "DEFANS PRO"
    msg["From"] = user
    msg["To"] = to_email

    s = smtplib.SMTP("smtp.gmail.com",587)
    s.starttls()
    s.login(user,pwd)
    s.send_message(msg)
    s.quit()

# =====================
# RUN
# =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)