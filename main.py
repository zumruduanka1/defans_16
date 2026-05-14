from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, json, random, re
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

def load_data(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return default

def save_data(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f: json.dump(data, f)
    except: pass

# Hafızayı Yükle
stats = load_data("stats.txt", {"total": 0, "risk": 0, "safe": 0})
history = load_data("history.txt", [])

# ======================================================
# ANALİZ MOTORU
# ======================================================
def ai_engine(text):
    text = text.lower()
    risk = random.randint(10, 20)
    triggers = ["iddia", "yalan", "sahte", "sızıntı", "ifşa", "manipülasyon", "şok", "gizli", "operasyon"]
    
    for word in triggers:
        if word in text: risk += random.randint(30, 45)
    
    if text.isupper(): risk += 15
    if "!!!" in text: risk += 10
    
    return min(max(risk, 1), 99)

# ======================================================
# MAİL SİSTEMİ
# ======================================================
def send_intel(text, risk, platform):
    global history
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO: return False

    # Tekrar engelleme (İlk 50 karakter)
    fingerprint = text.strip().lower()[:50]
    if fingerprint in history: return False

    try:
        msg = MIMEText(f"Platform: {platform.upper()}\nRisk: %{risk}\nİçerik: {text}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS TESPİT [%{risk}]"
        msg["From"], msg["To"] = MAIL_USER, MAIL_TO

        # En güvenli SSL bağlantısı
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, MAIL_TO, msg.as_string())
        server.quit()

        # Hafızayı güncelle
        history.append(fingerprint)
        if len(history) > 100: history.pop(0)
        save_data("history.txt", history)
        return True
    except Exception as e:
        print(f"BAĞLANTI HATASI: {e}")
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
    text = request.json.get("text", "")
    if len(text.strip()) < 5: return jsonify({"risk":0, "status":"Geçersiz", "stats":stats})

    risk = ai_engine(text)
    status = "🚨 Yüksek Risk" if risk >= 75 else ("⚠️ Şüpheli" if risk >= 60 else "✅ Güvenli")

    # İstatistikleri sadece bir kez artır
    stats["total"] += 1
    if risk >= 60: stats["risk"] += 1
    else: stats["safe"] += 1
    save_data("stats.txt", stats)

    send_intel(text, risk, "Manuel Analiz")
    return jsonify({"risk": risk, "status": status, "stats": stats})

@app.route("/feed")
def feed():
    global stats
    results = []
    urls = ["https://news.google.com/rss/search?q=twitter+iddia&hl=tr"]
    
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:15]:
                title = item.find("title").text.split(" - ")[0]
                risk = ai_engine(title)
                
                if risk >= 50:
                    platform = random.choice(["Twitter", "Instagram", "Facebook", "TikTok"])
                    results.append({"text": title, "risk": risk, "platform": platform})
                    
                    # Eğer yeni bir haber ise mail at ve istatistiğe ekle
                    fingerprint = title.strip().lower()[:50]
                    if fingerprint not in history:
                        send_intel(title, risk, platform)
                        stats["total"] += 1
                        if risk >= 60: stats["risk"] += 1
                        else: stats["safe"] += 1
        except: pass
    
    save_data("stats.txt", stats)
    return jsonify(sorted(results, key=lambda x: x["risk"], reverse=True))

@app.route("/mailtest")
def mailtest():
    ok = send_intel("Sistem Test Mesajı", 100, "TEST")
    return "MAIL BASARILI" if ok else "MAIL BASARISIZ (Loglara ve Uygulama Şifresine bakın)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))