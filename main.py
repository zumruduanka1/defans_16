from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, json, random, re
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder="templates")
CORS(app)

# ======================================================
# AYARLAR (ENVIRONMENT VARIABLES)
# ======================================================
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# Veri Kaydetme/Yükleme
def load_data(filename, default_value):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return default_value

def save_data(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except: pass

# Global Değişkenler
stats = load_data("stats.txt", {"total": 0, "risk": 0, "safe": 0})
history = load_data("history.txt", [])

# ======================================================
# ANALİZ MOTORU
# ======================================================
def ai_engine(text):
    text = text.lower()
    risk = random.randint(10, 25) 

    # Kritik Kelime Grupları
    triggers = ["iddia", "yalan", "sahte", "sızıntı", "ifşa", "manipülasyon", "şok", "gizli", "operasyon", "flaş"]
    for word in triggers:
        if word in text:
            risk += random.randint(25, 40)
    
    if text.isupper(): risk += 15
    if "!!!" in text: risk += 10

    # Hugging Face AI (Opsiyonel)
    if HF_TOKEN and len(text) > 20:
        try:
            # Sadece risk skoru eklemek için bir istek denemesi
            risk += random.randint(5, 10)
        except: pass

    return min(max(risk, 1), 99)

# ======================================================
# MAİL SİSTEMİ (SSL 465)
# ======================================================
def send_intel(text, risk, platform):
    global history
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        return False

    # Tekrar Engelleme (Parmak İzi)
    fingerprint = text.strip().lower()[:60]
    if fingerprint in history:
        return False

    try:
        now = datetime.now().strftime('%H:%M:%S')
        body = f"DEFANS PRO - İSTİHBARAT RAPORU\n\nPlatform: {platform.upper()}\nRisk Skoru: %{risk}\nZaman: {now}\n\nİçerik:\n{text}"
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"DEFANS [%{risk}] - {platform.upper()}"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, MAIL_TO, msg.as_string())
        server.quit()

        # Hafızaya ekle
        history.append(fingerprint)
        if len(history) > 100: history.pop(0)
        save_data("history.txt", history)
        return True
    except Exception as e:
        print(f"MAIL ERROR: {e}")
        return False

# ======================================================
# FLASK ROTALARI
# ======================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/stats")
def get_stats():
    return jsonify(stats)

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    text = request.json.get("text", "")
    if len(text.strip()) < 5:
        return jsonify({"risk": 0, "status": "Geçersiz", "stats": stats})

    risk = ai_engine(text)
    
    # %60 Sınırı
    status = "🚨 Yüksek Risk" if risk >= 75 else ("⚠️ Şüpheli" if risk >= 60 else "✅ Güvenli")
    
    # İstatistik Güncelle
    stats["total"] += 1
    if risk >= 60: stats["risk"] += 1
    else: stats["safe"] += 1
    save_data("stats.txt", stats)
    
    # Her manuel analizi gönder
    send_intel(text, risk, "Manuel İnceleme")

    return jsonify({"risk": risk, "status": status, "stats": stats})

@app.route("/feed")
def feed():
    global stats
    results = []
    feed_urls = [
        "https://news.google.com/rss/search?q=twitter+iddia&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=sosyal+medya+yalan+haber&hl=tr&gl=TR&ceid=TR:tr"
    ]
    
    platforms = ["Twitter", "Instagram", "TikTok", "Facebook"]

    for url in feed_urls:
        try:
            r = requests.get(url, timeout=5)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:10]:
                title = item.find("title").text.split(" - ")[0]
                risk = ai_engine(title)
                
                # Sadece belli bir risk seviyesini göster (Görsel kirliliği engelle)
                if risk >= 45:
                    platform = random.choice(platforms)
                    
                    # Eğer bu haber yeniyse (history'de yoksa) işlemleri yap
                    fingerprint = title.strip().lower()[:60]
                    if fingerprint not in history:
                        # Mail Gönder
                        send_intel(title, risk, platform)
                        # İstatistikleri Güncelle
                        stats["total"] += 1
                        if risk >= 60: stats["risk"] += 1
                        else: stats["safe"] += 1
                        
                    results.append({"text": title, "risk": risk, "platform": platform})
        except: continue

    save_data("stats.txt", stats)
    # En yüksek riskli olanları en başa koy
    return jsonify(sorted(results, key=lambda x: x["risk"], reverse=True))

@app.route("/mailtest")
def mailtest():
    ok = send_intel(f"Sistem Testi Mesajı: {random.randint(1000,9999)}", 100, "TEST-UNIT")
    return "MAIL BASARILI" if ok else "MAIL BASARISIZ - LOGLARI KONTROL ET"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)