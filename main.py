from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import random
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app) # Tüm kaynaklardan erişime izin verir (Render hatasını önler)

# =====================================================
# ENV - Render panelinden girilecek
# =====================================================
HF_TOKEN = os.getenv("HF_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWITTER_BEARER = os.getenv("TWITTER_BEARER")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# =====================================================
# MAİL SİSTEMİ
# =====================================================
def send_risk_report(content, risk_score, platform="Sistem Analizi"):
    if not MAIL_USER or risk_score < 50:
        return
    try:
        msg = MIMEText(f"Platform: {platform}\nRisk: %{risk_score}\n\nİçerik:\n{content}", "plain", "utf-8")
        msg["Subject"] = f"⚠️ DEFANS PRO: %{risk_score} Risk Tespit Edildi"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, MAIL_TO, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Mail Hatası: {e}")

# =====================================================
# ANALİZ MOTORU
# =====================================================
def analyze_engine(text):
    text = text.lower().strip()
    if len(text) < 5: return 0, "Geçersiz"

    score = random.randint(10, 25)
    trigger_words = {"şok": 20, "ifşa": 25, "öldü": 30, "sızdırıldı": 20, "deepfake": 35, "iddia": 15}
    
    for word, boost in trigger_words.items():
        if word in text: score += boost

    if any(x in text for x in [".jpg", ".mp4", "http"]): score += 15
    score = min(score, 100)
    
    status = "✅ Güvenli"
    if score > 75: status = "🚨 Dezenformasyon Riski"
    elif score > 45: status = "⚠️ Şüpheli"
    
    return score, status

# =====================================================
# ROUTES
# =====================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    content = data.get("text", "")
    risk, status = analyze_engine(content)
    if risk >= 50: send_risk_report(content, risk, "Kullanıcı Sorgusu")
    return jsonify({"risk": risk, "status": status})

@app.route("/feed")
def feed():
    posts = []
    # Haber API Sorgusu
    if NEWS_API_KEY:
        try:
            url = f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={NEWS_API_KEY}"
            r = requests.get(url, timeout=5)
            articles = r.json().get("articles", [])
            for a in articles[:8]:
                posts.append({"text": a['title'], "platform": "news"})
        except: pass

    # Eğer API'ler boşsa veya çalışmıyorsa dummy veri üret (Arayüz boş kalmasın)
    if not posts:
        posts = [
            {"text": "Sosyal medyada yayılan son dakika haberleri inceleniyor.", "platform": "twitter"},
            {"text": "Yapay zeka ile oluşturulan görsellere karşı uyarı yapıldı.", "platform": "news"}
        ]

    result = []
    for p in posts:
        risk, _ = analyze_engine(p['text'])
        result.append({"text": p['text'], "platform": p['platform'], "risk": risk})
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))