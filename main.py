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
# ENV YAPILANDIRMASI
# =====================================================
# MAIL_USER: Gönderen Gmail (Uygulama şifresi alınmış olan)
# MAIL_PASS: Gönderen Gmail'in 16 haneli uygulama şifresi
# MAIL_TO: Raporların gideceği DİĞER hesap adresi
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO") 
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# =====================================================
# ÖZEL MAİL GÖNDERİM SİSTEMİ
# =====================================================
def send_report(content, risk_score, platform="Sosyal Medya Takibi"):
    if not MAIL_USER or not MAIL_TO:
        return
    
    try:
        subject = f"⚠️ RİSKLİ İÇERİK: %{risk_score} [{platform}]"
        body = f"""
        DEFANS PRO - OTOMATİK RAPOR
        -------------------------------------------
        Tespit Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        Kaynak: {platform}
        Analiz Skoru: %{risk_score}
        
        İçerik:
        "{content}"
        
        -------------------------------------------
        Bu içerik sistem tarafından otomatik olarak riskli kategorisine alınmıştır.
        """
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"DEFANS PRO ANALİZ <{MAIL_USER}>"
        msg["To"] = MAIL_TO

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Mail gönderim hatası: {e}")

# =====================================================
# ANALİZ MOTORU
# =====================================================
def get_risk_analysis(text):
    text = text.lower()
    score = random.randint(15, 40)
    
    # Sosyal medya yalan haber anahtar kelimeleri
    bad_words = ["şok", "iddia", "gizlenen", "gerçekler", "patladı", "öldü", "flaş", "deepfake", "yapay zeka", "video kaydı"]
    for word in bad_words:
        if word in text: score += 15
        
    if "http" in text or "t.co" in text: score += 10
    score = min(score, 100)
    
    status = "✅ Güvenli"
    if score > 70: status = "🚨 Dezenformasyon / Yüksek Risk"
    elif score > 45: status = "⚠️ Şüpheli / Doğrulanmalı"
    
    return score, status

# =====================================================
# VERİ AKIŞI (Zenginleştirilmiş Sosyal Medya Kaynakları)
# =====================================================
@app.route("/feed")
def feed():
    final_feed = []
    
    # 1. Kaynak: Haber API (Varsa)
    if NEWS_API_KEY:
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={NEWS_API_KEY}", timeout=5)
            articles = r.json().get("articles", [])
            for a in articles[:5]:
                s, _ = get_risk_analysis(a['title'])
                final_feed.append({"text": a['title'], "platform": "Haber Kaynağı", "risk": s})
        except: pass

    # 2. Kaynak: Sosyal Medya Simülasyon Verileri (Veri azlığı için ekleme)
    sim_data = [
        "X/Twitter: Yeni bir manipülasyon kampanyası tespit edildi.",
        "WhatsApp: 'Hastanelerde yer kalmadı' iddiası hızla yayılıyor.",
        "TikTok: Yapay zeka ile üretilmiş siyasetçi videosu gündemde.",
        "Instagram: Dolandırıcılık amaçlı 'Bedava bilet' paylaşımları arttı.",
        "Facebook: Eski bir olay yeniymiş gibi servis ediliyor.",
        "Telegram: Kripto varlıklarla ilgili asılsız panik haberleri.",
        "Sosyal Medya: Seçim sonuçlarını etkilemeye yönelik bot hesap faaliyetleri.",
        "X: Onaylı hesaplardan yayılan sahte kaza görüntüleri."
    ]
    
    for item in sim_data:
        s, _ = get_risk_analysis(item)
        final_feed.append({"text": item, "platform": "Sosyal Medya", "risk": s})

    # Her veri çekildiğinde içlerinden en riskli olanı mail olarak raporla
    riskiest = max(final_feed, key=lambda x: x['risk'])
    if riskiest['risk'] > 60:
        send_report(riskiest['text'], riskiest['risk'], "Otomatik Tarama")

    return jsonify(final_feed)

@app.route("/")
def index(): return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    content = data.get("text", "")
    risk, status = get_risk_analysis(content)
    
    # Manuel analizi her zaman mail at (İstediğin özellik)
    send_report(content, risk, "Kullanıcı Manuel Analizi")
    
    return jsonify({"risk": risk, "status": status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))