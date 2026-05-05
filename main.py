from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import smtplib
from email.mime.text import MIMEText
import feedparser

app = Flask(__name__, static_folder="static", static_url_path="")

# 📧 MAIL AYARLARI (GMAIL)
EMAIL_SENDER = "seninmail@gmail.com"
EMAIL_PASSWORD = "uygulama_sifresi"
EMAIL_RECEIVERS = ["seninmail@gmail.com", "arkadas@gmail.com"]

def send_mail(text, risk):
    try:
        msg = MIMEText(f"Riskli içerik bulundu:\n\n{text}\n\nRisk: {risk}")
        msg["Subject"] = "⚠️ DEFANS UYARI"
        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(EMAIL_RECEIVERS)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVERS, msg.as_string())
        server.quit()
    except Exception as e:
        print("Mail hatası:", e)

# 🧠 ANALİZ
def analyze_text(text):
    if len(text) < 20:
        return {"risk": 0, "guven": 0, "yorum": "çok kısa"}

    risk_words = [
        "öldü","patlama","savaş","son dakika",
        "ifşa","şok","yasaklandı","skandal"
    ]

    score = sum(1 for w in risk_words if w in text.lower())
    risk = min(score * 20, 100)
    guven = 100 - risk

    # 🚨 yüksek risk → mail at
    if risk >= 60:
        send_mail(text, risk)

    return {"risk": risk, "guven": guven, "yorum": "analiz tamam"}

# 🌐 SOSYAL MEDYA (RSS ile)
def get_social_news():
    feed = feedparser.parse("https://rss.app/feeds/twitter/elonmusk.rss")
    results = []

    for entry in feed.entries[:5]:
        analiz = analyze_text(entry.title)
        results.append({
            "text": entry.title,
            "risk": analiz["risk"],
            "guven": analiz["guven"]
        })

    return results

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json

    if data.get("text"):
        return jsonify(analyze_text(data["text"]))

    if data.get("url"):
        try:
            r = requests.get(data["url"])
            return jsonify(analyze_text(r.text[:2000]))
        except:
            return jsonify({"error": "url okunamadı"})

    return jsonify({"error": "veri yok"})

@app.route("/api/social")
def social():
    return jsonify(get_social_news())

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)