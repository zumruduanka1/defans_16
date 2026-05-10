from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import random
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =====================================================
# ENV - Render panelinden girilecek
# =====================================================
HF_TOKEN = os.getenv("HF_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# =====================================================
# GELİŞMİŞ MAİL SİSTEMİ
# =====================================================
def send_report(content, risk_score, platform="Sosyal Medya"):
    # Mail bilgileri eksikse veya risk çok düşükse (spam engelleme) gönderme
    if not MAIL_USER or risk_score < 30:
        return
    try:
        subject = f"⚠️ DEFANS PRO TESPİTİ: %{risk_score} Risk [{platform}]"
        body = f"""
        Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Kaynak: {platform}
        Analiz Skoru: %{risk_score}
        
        İçerik:
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
# DEZENFORMASYON ANALİZ MOTORU
# =====================================================
def analyze_content(text):
    text = text.lower().strip()
    if len(text) < 5: return 0, "Geçersiz"

    score = random.randint(15, 35) # Başlangıç riski
    
    # Yalan haber tetikleyicileri
    triggers = {
        "şok": 20, "iddia": 15, "sızdırıldı": 20, "gizlenen": 15, 
        "deepfake": 35, "öldü": 30, "manipülasyon": 25, "ifşa": 20,
        "aslında": 10, "kimse bilmiyor": 20, "acil paylaş": 25
    }
    
    for word, boost in triggers.items():
        if word in text: score += boost

    # Link içeren paylaşımlar sosyal medyada daha risklidir
    if "http" in text or "t.co" in text: score += 15
    
    score = min(score, 100)
    
    if score > 75: status = "🚨 Yüksek Dezenformasyon Riski"
    elif score > 45: status = "⚠️ Şüpheli İçerik"
    else: status = "✅ Güvenli Görünüyor"
    
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
    risk, status = analyze_content(content)
    
    # Her manuel analizi mail at
    send_report(content, risk, "Kullanıcı Sorgusu")
    
    return jsonify({"risk": risk, "status": status})

@app.route("/feed")
def feed():
    social_posts = []
    
    # API'den haberleri çekip "Sosyal Medya" formatına sokuyoruz
    if NEWS_API_KEY:
        try:
            url = f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={NEWS_API_KEY}"
            r = requests.get(url, timeout=5)
            articles = r.json().get("articles", [])
            for a in articles[:10]:
                title = a.get('title', '')
                risk, _ = analyze_content(title)
                
                post_data = {"text": title, "platform": "Sosyal Medya", "risk": risk}
                social_posts.append(post_data)
                
                # Her bulunan akış haberini mail olarak yolla
                send_report(title, risk, "Canlı Akış")
        except: pass

    # Yedek veri (API çalışmazsa)
    if not social_posts:
        social_posts = [
            {"text": "X platformunda yayılan yeni bir manipülasyon kampanyası tespit edildi.", "platform": "Sosyal Medya", "risk": 85},
            {"text": "WhatsApp gruplarında paylaşılan ses kaydı asılsız çıktı.", "platform": "Sosyal Medya", "risk": 90}
        ]
        for p in social_posts: send_report(p['text'], p['risk'], "Yedek Akış")

    return jsonify(social_posts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))