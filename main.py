from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder='templates') # Klasörü netleştirdik
CORS(app)

# Ayarlar
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 4, "risk": 0, "safe": 1}
sent_intel = set()

def ai_engine(text):
    try:
        if not HF_TOKEN: return 35
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": text, "parameters": {"candidate_labels": ["manipulative", "fact-based", "propaganda", "clickbait"]}}
        res = requests.post(url, headers=headers, json=payload, timeout=8).json()
        scores = dict(zip(res['labels'], res['scores']))
        return int((scores.get('manipulative', 0) + scores.get('propaganda', 0) + scores.get('clickbait', 0)) * 100)
    except: return 35

def send_intel_report(content, risk, label):
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO or risk < 30: return
    try:
        msg = MIMEText(f"KAYNAK: {label}\nSKOR: %{risk}\n\n{content}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS TESPİT: %{risk}"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
    except: pass

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    data = request.json
    text = data.get("text", "")
    risk = ai_engine(text)
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    send_intel_report(text, risk, "MANUEL")
    return jsonify({"text": text, "risk": risk, "current_stats": stats})

@app.route("/feed")
def feed():
    global sent_intel
    query = "site:facebook.com OR site:tiktok.com OR site:x.com 'iddia' OR 'yalanlandı'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    results = []
    try:
        resp = requests.get(url, timeout=7)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:10]:
            title = item.find('title').text.split(" - ")[0]
            risk = ai_engine(title)
            if title not in sent_intel:
                send_intel_report(title, risk, "OTOMATIK")
                sent_intel.add(title)
            results.append({"text": title, "risk": risk})
    except: pass
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)