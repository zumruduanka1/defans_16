from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, json, random, re
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder="templates")
CORS(app)

# Ayarlar
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

def load_data(f, d):
    if os.path.exists(f):
        try:
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        except: pass
    return d

def save_data(f, data):
    try:
        with open(f, "w", encoding="utf-8") as file: json.dump(data, file)
    except: pass

stats = load_data("stats.txt", {"total": 0, "risk": 0, "safe": 0})
history = load_data("history.txt", [])

def ai_engine(text):
    text = text.lower()
    risk = random.randint(10, 20)
    triggers = ["iddia", "yalan", "sahte", "sızıntı", "ifşa", "manipülasyon", "şok", "gizli", "operasyon"]
    for word in triggers:
        if word in text: risk += random.randint(30, 45)
    return min(max(risk, 1), 99)

def send_intel(text, risk, platform):
    global history
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO: return False
    fp = text.strip().lower()[:50]
    if fp in history: return False
    try:
        msg = MIMEText(f"Platform: {platform}\nRisk: %{risk}\nİçerik: {text}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS [%{risk}] - {platform}"
        msg["From"], msg["To"] = MAIL_USER, MAIL_TO
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, MAIL_TO, msg.as_string())
        server.quit()
        history.append(fp)
        if len(history) > 100: history.pop(0)
        save_data("history.txt", history)
        return True
    except: return False

@app.route("/")
def home(): return render_template("index.html")

@app.route("/stats")
def get_stats(): return jsonify(stats)

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    text = request.json.get("text", "")
    risk = ai_engine(text)
    status = "🚨 Yüksek Risk" if risk >= 75 else ("⚠️ Şüpheli" if risk >= 60 else "✅ Güvenli")
    stats["total"] += 1
    if risk >= 60: stats["risk"] += 1
    else: stats["safe"] += 1
    save_data("stats.txt", stats)
    send_intel(text, risk, "Manuel")
    return jsonify({"risk": risk, "status": status, "stats": stats})

@app.route("/feed")
def feed():
    global stats
    results = []
    try:
        r = requests.get("https://news.google.com/rss/search?q=twitter+iddia&hl=tr", timeout=5)
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:10]:
            title = item.find("title").text.split(" - ")[0]
            risk = ai_engine(title)
            if risk >= 50:
                p = random.choice(["Twitter", "Instagram", "Facebook", "TikTok"])
                results.append({"text": title, "risk": risk, "platform": p})
                if title.strip().lower()[:50] not in history:
                    send_intel(title, risk, p)
                    stats["total"] += 1
                    if risk >= 60: stats["risk"] += 1
                    else: stats["safe"] += 1
    except: pass
    save_data("stats.txt", stats)
    return jsonify(sorted(results, key=lambda x: x["risk"], reverse=True))

@app.route("/mailtest")
def mailtest():
    return "MAIL BASARILI" if send_intel("Test", 100, "SISTEM") else "MAIL HATASI"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))