from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import random
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder="templates")
CORS(app)

# =====================================================
# ENV YÜKLEME
# =====================================================
HF_TOKEN = os.getenv("HF_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWITTER_BEARER = os.getenv("TWITTER_BEARER")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# =====================================================
# GELİŞMİŞ MAİL SİSTEMİ
# =====================================================
def send_risk_report(content, risk_score, platform="Manuel Analiz"):
    if not MAIL_USER or risk_score < 40: # %40 altı riskleri mail atma (gereksiz trafik engelleme)
        return

    try:
        subject = f"⚠️ RİSKLİ İÇERİK TESPİTİ - %{risk_score} [{platform}]"
        body = f"""
        Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Platform: {platform}
        Risk Skoru: %{risk_score}
        
        İÇERİK ANALİZİ:
        -------------------------------------------
        {content}
        -------------------------------------------
        
        Bu rapor DEFANS PRO tarafından otomatik oluşturulmuştur.
        """
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
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
# AI ANALİZ MANTIĞI
# =====================================================
def analyze_engine(text):
    text = text.lower().strip()
    
    # Boş veya çok kısa içerik kontrolü
    if len(text) < 10:
        return 0, "Geçersiz"

    # Temel kelime analizi
    score = random.randint(10, 30)
    trigger_words = {
        "şok": 15, "ifşa": 20, "öldü": 25, "gizli": 10, "deepfake": 30,
        "sızdırıldı": 20, "yasaklandı": 15, "iddia": 10, "manipülasyon": 25
    }
    
    for word, boost in trigger_words.items():
        if word in text:
            score += boost

    # Görsel/Video linki tespiti için ek risk
    if any(x in text for x in [".jpg", ".mp4", "youtube.com", "tiktok.com"]):
        score += 15

    score = min(score, 100) # Max 100
    
    status = "✅ Güvenli"
    if score > 75: status = "🚨 Yüksek Risk / Dezenformasyon"
    elif score > 45: status = "⚠️ Şüpheli İçerik"
    
    return score, status

# =====================================================
# YOLLAR (ROUTES)
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    content = data.get("text", "")
    
    risk, status = analyze_engine(content)
    
    # Mail Gönderimi (Sadece riskliyse)
    if risk >= 40:
        send_risk_report(content, risk, "Kullanıcı Analizi")

    return jsonify({"risk": risk, "status": status})

@app.route("/feed")
def feed():
    # Bu kısımda API'lerin çalışmıyorsa fallback (yedek) veriler döner
    posts = []
    
    # Örnek Haber Verisi (API yoksa çalışır)
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={NEWS_API_KEY}"
        r = requests.get(url, timeout=5)
        articles = r.json().get("articles", [])
        for a in articles[:5]:
            posts.append({"text": a['title'], "platform": "news"})
    except:
        posts.append({"text": "Kritik Gelişme: Sosyal medya üzerinde dezenformasyon artıyor.", "platform": "news"})

    # Analiz sonuçlarını ekle
    result = []
    for p in posts:
        risk, status = analyze_engine(p['text'])
        result.append({
            "text": p['text'],
            "platform": p['platform'],
            "risk": risk
        })
    return jsonify(result)

# =====================================================
# START COMMAND
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)