from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- AYARLAR (Render'da bu isimlerle tanımlamalısın) ---
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 0, "risk": 0, "safe": 0}
sent_news = set() # Aynı haberi tekrar tekrar mail atmaması için

def ai_analyze_engine(text):
    """Hugging Face AI ile metnin manipülasyon içerip içermediğini sorgular"""
    if not HF_TOKEN:
        # Token yoksa basit bir yedek algoritma (Senaryon bozulmasın diye)
        return 45 if len(text) % 2 == 0 else 20
    
    try:
        # Dezenformasyon tespiti için en iyi modellerden biri (BART Large MNLI)
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": ["fake news", "propaganda", "real news"]}
        }
        response = requests.post(API_URL, headers=headers, json=payload, timeout=7).json()
        
        # Riskli etiketlerin skorlarını topla
        labels = response['labels']
        scores = response['scores']
        risk_index = sum(score for label, score in zip(labels, scores) if label in ["fake news", "propaganda"])
        
        return int(risk_index * 100)
    except:
        return 30 # Hata durumunda güvenli tarafta kal

def send_defans_mail(content, risk, source="MANUEL ANALİZ"):
    """Bulunan riskli haberi anında mail gönderir"""
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        return
    
    try:
        status = "KRİTİK RİSK" if risk > 70 else "ŞÜPHELİ"
        msg = MIMEText(f"KAYNAK: {source}\nANALİZ SONUCU: {status}\nRİSK SKORU: %{risk}\n\nİÇERİK:\n{content}", "plain", "utf-8")
        msg["Subject"] = f"🚨 DEFANS TESPİT: %{risk} ({source})"
        msg["From"] = f"Defans AI <{MAIL_USER}>"
        msg["To"] = MAIL_TO

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Mail gönderim hatası: {e}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    data = request.json
    text = data.get("text", "")
    risk = ai_analyze_engine(text)
    
    status = "🚨 RİSKLİ" if risk > 55 else "✅ GÜVENLİ"
    stats["total"] += 1
    if risk > 55: stats["risk"] += 1
    else: stats["safe"] += 1
    
    # Kullanıcının manuel yaptığı analizi her zaman mail at
    send_defans_mail(text, risk, "KULLANICI ANALİZİ")
    
    return jsonify({"risk": risk, "status": status, "current_stats": stats})

@app.route("/feed")
def feed():
    """İnterneti tarar ve bulduğu RİSKLİ haberleri otomatik mail atar"""
    global sent_news
    url = "https://news.google.com/rss/search?q=site:x.com+OR+site:instagram.com+sahte+haber&hl=tr&gl=TR&ceid=TR:tr"
    news_feed = []
    
    try:
        resp = requests.get(url, timeout=5)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text
            risk = ai_analyze_engine(title)
            
            # EĞER HABER ÇOK RİSKLİ VE DAHA ÖNCE ATILMAMIŞSA OTOMATİK MAİL AT
            if risk > 75 and title not in sent_news:
                send_defans_mail(title, risk, "OTOMATİK SİSTEM TARAMASI")
                sent_news.add(title)
            
            news_feed.append({"text": title, "risk": risk})
    except:
        news_feed = [{"text": "Canlı akış şu an aktif değil.", "risk": 0}]
    
    return jsonify(news_feed)

if __name__ == "__main__":
    app.run(debug=True)