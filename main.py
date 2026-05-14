from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, json, random, time, re
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder="templates")
CORS(app)

# ======================================================
# AYARLAR
# ======================================================
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# İstatistikleri ve Gönderilenleri Sakla
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return default

stats = load_data("stats.txt", {"total": 0, "risk": 0, "safe": 0})
# Aynı haberlerin tekrar etmemesi için hafıza dosyası
sent_news = load_data("sent_news.txt", [])

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f)

# ======================================================
# GELİŞMİŞ ANALİZ & FİLTRE
# ======================================================
def ai_engine(text):
    text = text.lower()
    # Baz puanı düşük tuttuk ki sadece "yalan/iddia" içerenler yükselsin
    risk = random.randint(5, 15) 
    
    # Çok Riskli Kelimeler (Bunlar varsa risk uçar)
    triggers = ["iddia", "yalan", "sahte", "sızıntı", "ifşa", "manipülasyon", "şok", "gizli", "operasyon"]
    for word in triggers:
        if word in text: risk += random.randint(30, 50)
    
    if "!!!" in text or text.isupper(): risk += 15
    return min(max(risk, 1), 99)

# ======================================================
# GÜÇLENDİRİLMİŞ MAIL SİSTEMİ
# ======================================================
def send_intel(text, risk, platform):
    global sent_news
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO: return False
    
    # TEKRAR ENGELLEME: Eğer bu metin daha önce gönderildiyse (ilk 30 karakter kontrolü) dur.
    fingerprint = text.strip()[:40].lower()
    if fingerprint in sent_news:
        return False

    try:
        msg = MIMEText(f"DEFANS PRO ANALİZ\n\nPlatform: {platform}\nRisk: %{risk}\nİçerik: {text}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS TESPİT [%{risk}]"
        msg["From"], msg["To"] = MAIL_USER, MAIL_TO
        
        # SSL ile bağlan ve hemen gönder
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, MAIL_TO, msg.as_string())
        server.quit()
        
        # Hafızaya ekle ve kaydet
        sent_news.append(fingerprint)
        if len(sent_news) > 200: sent_news.pop(0) # Hafıza çok şişmesin
        save_data("sent_news.txt", sent_news)
        return True
    except Exception as e:
        print(f"MAIL HATASI: {e}")
        return False

# ======================================================
# ROTALAR
# ======================================================
@app.route("/")
def home(): return render_template("index.html")

@app.route("/stats")
def get_stats(): return jsonify(stats)

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    text = request.json.get("text","")
    if len(text) < 10: return jsonify({"risk":0, "status":"Kısa İçerik", "stats":stats})
    
    risk = ai_engine(text)
    
    # %60 altı güvenli sayılıyor
    status = "🚨 Yüksek Risk" if risk >= 75 else ("⚠️ Şüpheli" if risk >= 60 else "✅ Güvenli")
    
    stats["total"] += 1
    if risk >= 60: stats["risk"] += 1
    else: stats["safe"] += 1
    save_stats("stats.txt", stats)
    
    # Her manuel analizi gönder
    send_intel(text, risk, "Manuel")
    
    return jsonify({"risk": risk, "status": status, "stats": stats})

@app.route("/feed")
def feed():
    global stats
    results = []
    # Daha spesifik yalan haber aramaları
    urls = [
        "https://news.google.com/rss/search?q=iddia+ediliyor+sosyal+medya&hl=tr",
        "https://news.google.com/rss/search?q=yalan+haber+x.com&hl=tr"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:15]:
                title = item.find("title").text.split(" - ")[0]
                risk = ai_engine(title)
                
                # SEÇİCİ FİLTRE: Sadece riski %50'den büyük olanları akışa al
                if risk >= 50:
                    fingerprint = title.strip()[:40].lower()
                    if fingerprint not in sent_news:
                        results.append({"text": title, "risk": risk, "platform": "Canlı"})
                        send_intel(title, risk, "Otomatik Akış")
                        stats["total"] += 1
                        stats["risk"] += 1 if risk >= 60 else 0
                        stats["safe"] += 1 if risk < 60 else 0
        except: pass
    save_data("stats.txt", stats)
    return jsonify(sorted(results, key=lambda x: x["risk"], reverse=True))

@app.route("/mailtest")
def mailtest():
    ok = send_intel(f"Sistem Testi - {random.randint(100,999)}", 100, "TEST")
    return "MAIL BASARILI" if ok else "MAIL BASARISIZ (Loglara bak)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))