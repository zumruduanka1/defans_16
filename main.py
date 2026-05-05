from flask import Flask, request, jsonify, send_from_directory
import os, random, smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# =========================
# ANA SAYFA
# =========================
@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# =========================
# ANALİZ (AI SIMULATION)
# =========================
def analyze_text(text):
    text = text.lower()

    risk = 20

    if any(x in text for x in ["şok", "inanılmaz", "ifşa", "gizli", "yalan"]):
        risk += 40

    if "kaynak yok" in text or "iddia" in text:
        risk += 20

    risk += random.randint(0, 20)

    status = "Tehlikeli" if risk > 70 else "Şüpheli" if risk > 40 else "Güvenli"

    return risk, status


# =========================
# MAIL GÖNDER
# =========================
def send_mail(to_email, text, risk, status):
    try:
        user = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASS")

        msg = MIMEText(f"""
Yeni Riskli İçerik Tespit Edildi!

İçerik:
{text}

Risk Skoru: %{risk}
Durum: {status}
""")

        msg["Subject"] = "⚠️ DEFANS PRO UYARI"
        msg["From"] = user
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Mail hatası:", e)


# =========================
# API ANALYZE
# =========================
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")
    email = data.get("email", "")

    risk, status = analyze_text(text)

    if risk > 70 and email:
        send_mail(email, text, risk, status)

    return jsonify({
        "risk": risk,
        "status": status
    })


# =========================
# SOSYAL MEDYA (SIMULATED)
# =========================
@app.route("/api/social")
def social():
    posts = [
        {"platform": "twitter", "text": "Şok gelişme! gizli belge sızdı"},
        {"platform": "instagram", "text": "Yeni haber gündem oldu"},
        {"platform": "tiktok", "text": "İnanılmaz gerçek ortaya çıktı"},
        {"platform": "facebook", "text": "Bu bilgi doğru mu?"},
    ]

    result = []

    for p in posts:
        risk, status = analyze_text(p["text"])

        result.append({
            "platform": p["platform"],
            "text": p["text"],
            "risk": risk,
            "status": status
        })

    return jsonify(result)


# =========================
# VIDEO ANALİZ (DEEPFAKE SIM)
# =========================
@app.route("/api/video", methods=["POST"])
def video():
    data = request.json
    url = data.get("url")

    # fake deepfake detection
    score = random.randint(10, 95)

    return jsonify({
        "score": score,
        "status": "Deepfake olabilir" if score > 60 else "Temiz"
    })


# =========================
# SERVER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)