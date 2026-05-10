from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

# --- AYARLAR ---
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 0, "risk": 0, "safe": 0}

def ai_analyze(text):
    """Sadece Hugging Face ile analiz yapar"""
    if not HF_TOKEN:
        return 30 # Token yoksa varsayılan güvenli skor
    try:
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": text, "parameters": {"candidate_labels": ["fake", "real"]}}
        res = requests.post(url, headers=headers, json=payload, timeout=5).json()
        # 'fake' etiketinin skorunu alıp yüzdeye çeviriyoruz
        idx = res['labels'].index('fake')
        return int(res['scores'][idx] * 100)
    except:
        return 40 # Hata durumunda orta risk

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    data = request.json
    text = data.get("text", "")
    risk = ai_analyze(text)
    
    status = "🚨 RİSKLİ" if risk > 50 else "✅ GÜVENLİ"
    stats["total"] += 1
    if risk > 50: stats["risk"] += 1
    else: stats["safe"] += 1
    
    # Mail Sistemi
    if MAIL_USER and MAIL_PASS:
        try:
            msg = MIMEText(f"İçerik: {text}\nRisk Skoru: %{risk}\nDurum: {status}", "plain", "utf-8")
            msg["Subject"] = f"DEFANS ANALİZ: %{risk}"
            msg["From"] = MAIL_USER
            msg["To"] = MAIL_TO
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(MAIL_USER, MAIL_PASS)
            server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
            server.quit()
        except: pass

    return jsonify({"risk": risk, "status": status, "current_stats": stats})

@app.route("/feed")
def feed():
    """Sosyal Medya Verisi (APISIZ / Yasal RSS Köprüsü)"""
    # X (Twitter) ve Instagram'daki dezenformasyon haberlerini çeker
    url = "https://news.google.com/rss/search?q=site:x.com+OR+site:instagram.com+fake+news&hl=tr&gl=TR&ceid=TR:tr"
    news_feed = []
    try:
        resp = requests.get(url, timeout=5)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:6]:
            title = item.find('title').text
            # Bu başlıkları da HF ile hızlıca puanlıyoruz
            risk = ai_analyze(title)
            news_feed.append({"text": title, "risk": risk})
    except:
        news_feed = [{"text": "Canlı akış şu an yüklenemiyor...", "risk": 0}]
    return jsonify(news_feed)

if __name__ == "__main__":
    app.run(debug=True)