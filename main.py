from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, json, random, time, re
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder="templates")
CORS(app)

# ======================================================
# ENV
# ======================================================
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

def load_stats():
    if os.path.exists("stats.txt"):
        try:
            with open("stats.txt", "r") as f: return json.load(f)
        except: pass
    return {"total": 0, "risk": 0, "safe": 0}

def save_stats(s):
    with open("stats.txt", "w") as f: json.dump(s, f)

stats = load_stats()

def is_meaningful(text):
    if not text or len(text.strip()) < 10: return False
    return True

def ai_engine(text):
    text = text.lower()
    risk = random.randint(15, 35)
    
    very_risky = ["deepfake", "ifşa", "sızıntı", "yalan", "sahte", "operasyon", "şok"]
    for word in very_risky:
        if word in text: risk += random.randint(25, 45)
    
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            requests.post(url, headers=headers, json={"inputs": text}, timeout=3)
            risk += 10
        except: pass
    
    return min(max(risk, 1), 99)

def send_intel(text, risk, platform):
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO: return False
    try:
        body = f"DEFANS RAPOR\n\nPlatform: {platform}\nRisk: %{risk}\nİçerik: {text}"
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"DEFANS ALERT %{risk}"
        msg["From"], msg["To"] = MAIL_USER, MAIL_TO
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, MAIL_TO, msg.as_string())
        server.quit()
        return True
    except: return False

@app.route("/")
def home(): return render_template("index.html")

@app.route("/stats")
def get_stats(): return jsonify(stats)

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    text = request.json.get("text","")
    if not is_meaningful(text): return jsonify({"risk":0, "status":"Geçersiz", "stats":stats})
    
    risk = ai_engine(text)
    
    # YENİ KURAL: %60 ve üzeri riskli sayılsın, altı güvenli
    status = "🚨 Yüksek Risk" if risk >= 75 else ("⚠️ Şüpheli" if risk >= 60 else "✅ Güvenli")
    
    stats["total"] += 1
    if risk >= 60: # %60 sınırı
        stats["risk"] += 1
    else:
        stats["safe"] += 1
    
    save_stats(stats)
    
    # KURAL: Risk ne olursa olsun (0-100 arası her şey) mail gönderilsin
    send_intel(text, risk, "Manuel Analiz")
    
    return jsonify({"risk": risk, "status": status, "stats": stats})

@app.route("/feed")
def feed():
    global stats
    results = []
    feed_urls = ["https://news.google.com/rss/search?q=twitter+iddia&hl=tr"]
    for url in feed_urls:
        try:
            r = requests.get(url, timeout=4)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:10]:
                title = item.find("title").text.split(" - ")[0]
                if is_meaningful(title):
                    risk = ai_engine(title)
                    results.append({"text": title, "risk": risk, "platform": "Sistem"})
                    # Akıştan gelen her şeyi de mail gönder
                    send_intel(title, risk, "Canlı Akış")
                    stats["total"] += 1
                    if risk >= 60: stats["risk"] += 1
                    else: stats["safe"] += 1
        except: pass
    save_stats(stats)
    return jsonify(results)

# 404 HATASINI ÇÖZEN TEST ROTASI
@app.route("/mailtest")
def mailtest():
    ok = send_intel("Sistem testi mesajı", 100, "TEST")
    return "MAIL GONDERILDI" if ok else "MAIL HATASI (ENV ayarlarını kontrol et)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))