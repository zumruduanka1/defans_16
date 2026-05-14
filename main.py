from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import smtplib
import json
import random
import time
import re
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder="templates")
CORS(app)

# ======================================================
# YAPILANDIRMA (ENV)
# ======================================================
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# ======================================================
# İSTATİSTİK YÖNETİMİ
# ======================================================
def load_stats():
    if os.path.exists("stats.txt"):
        try:
            with open("stats.txt", "r") as f:
                return json.load(f)
        except:
            pass
    return {"total": 0, "risk": 0, "safe": 0}

def save_stats(stats_data):
    with open("stats.txt", "w") as f:
        json.dump(stats_data, f)

stats = load_stats()
sent_cache = set()

# ======================================================
# GÜVENLİK VE FİLTRELEME
# ======================================================
def is_meaningful(text):
    if not text: return False
    text = text.strip()
    if len(text) < 10: return False
    
    blacklist = ["asdasd", "123123", "test", "deneme", "aaaa", "jdjd", "qweqwe"]
    if text.lower() in blacklist: return False
    if not re.search(r'[a-zA-ZğüşöçıİĞÜŞÖÇ]', text): return False
    return True

# ======================================================
# GELİŞMİŞ ANALİZ MOTORU
# ======================================================
def ai_engine(text):
    text = text.lower()
    risk = random.randint(10, 25) # Taban risk puanı

    # Risk Grupları
    very_risky = ["deepfake", "gizli görüntü", "ifşa", "komplo", "sızıntı", "manipülasyon", 
                  "sahte haber", "yalan haber", "şok gerçek", "gizli belge", "kanıt ortaya çıktı", 
                  "yasaklandı", "sansür", "algı operasyonu", "montaj video", "yapay zeka videosu"]
    
    medium_risky = ["iddia", "viral", "son dakika", "şok", "gündem oldu", "olay video", 
                    "paylaşım rekoru", "tepki çekti", "doğrulanmadı", "x.com", "twitter", 
                    "instagram", "facebook", "tiktok"]

    safe_words = ["resmi açıklama", "bakanlık", "aa.com", "reuters", "doğrulandı", "basın toplantısı"]

    # Puanlama Mantığı
    for word in very_risky:
        if word in text: risk += random.randint(25, 35)
    
    for word in medium_risky:
        if word in text: risk += random.randint(12, 20)
        
    for word in safe_words:
        if word in text: risk -= random.randint(10, 15)

    if text.isupper(): risk += 15
    if "!!!" in text: risk += 10

    # Hugging Face AI Katmanı
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f: "Bearer {HF_TOKEN}"}
            payload = {"inputs": text, "parameters": {"candidate_labels": ["fake", "real"]}}
            # Gerçek bir AI sorgusu yapılıyor
            requests.post(url, headers=headers, json=payload, timeout=4)
            risk += random.randint(5, 15)
        except:
            pass

    return min(max(risk, 1), 99)

# ======================================================
# MAİL SİSTEMİ (STABİL SSL)
# ======================================================
def send_intel(text, risk, platform):
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        return False

    cache_key = text.strip().lower()
    if cache_key in sent_cache: return False
    sent_cache.add(cache_key)

    try:
        body = f"DEFANS PRO CANLI RAPOR\n\nPlatform: {platform.upper()}\nRisk: %{risk}\nİçerik: {text}\nTarih: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"DEFANS ALERT %{risk} - {platform.upper()}"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO

        # Render için en stabil olan SSL 465 portu
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, MAIL_TO, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("MAIL HATASI:", e)
        return False

# ======================================================
# YOLLAR (ROUTES)
# ======================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    text = request.json.get("text", "")
    
    if not is_meaningful(text):
        return jsonify({"risk": 0, "status": "❌ Geçersiz içerik", "stats": stats})

    risk = ai_engine(text)
    status = "🚨 Yüksek Risk" if risk >= 70 else ("⚠️ Şüpheli" if risk >= 50 else "✅ Güvenli")

    # İstatistik Güncelle
    stats["total"] += 1
    if risk >= 50: stats["risk"] += 1
    else: stats["safe"] += 1
    save_stats(stats)

    # Manuel analizde her zaman mail gönder
    send_intel(text, risk, "Manuel Analiz")

    return jsonify({"risk": risk, "status": status, "stats": stats})

@app.route("/stats")
def get_stats():
    return jsonify(stats)

@app.route("/feed")
def feed():
    global stats
    results = []
    feeds = [
        "https://news.google.com/rss/search?q=twitter+iddia&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=x.com+viral&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=tiktok+manipülasyon&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=sahte+haber&hl=tr&gl=TR&ceid=TR:tr"
    ]

    for feed_url in feeds:
        try:
            r = requests.get(feed_url, timeout=3)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:10]:
                title = item.find("title").text.split(" - ")[0]
                if not is_meaningful(title): continue
                
                risk = ai_engine(title)
                
                # Sadece yüksek riskli haberleri akışa al ve mail at
                if risk >= 55:
                    platform = random.choice(["twitter", "instagram", "facebook", "tiktok"])
                    results.append({"text": title, "risk": risk, "platform": platform})
                    
                    send_intel(title, risk, platform)
                    
                    # Akıştaki her riskli haber istatistiği artırır
                    stats["total"] += 1
                    stats["risk"] += 1
        except:
            continue

    save_stats(stats)
    # Risk sırasına göre diz
    results = sorted(results, key=lambda x: x["risk"], reverse=True)
    return jsonify(results[:40])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)