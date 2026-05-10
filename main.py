from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder='templates')
CORS(app)

# Ayarlar
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 4, "risk": 0, "safe": 1}

def ai_engine(text):
    risk = 25
    if any(w in text.lower() for w in ["iddia", "yalan", "şok", "gizli", "sızıntı"]):
        risk += 20
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": text, "parameters": {"candidate_labels": ["manipulative", "fact-based"]}}
            res = requests.post(url, headers=headers, json=payload, timeout=5).json()
            if 'scores' in res: risk = int(res['scores'][0] * 100)
        except: pass
    return min(risk, 98)

def send_report(text, risk):
    if not MAIL_USER or not MAIL_PASS: return
    try:
        msg = MIMEText(f"DEFANS PRO ANALİZ\n\nİçerik: {text}\nRisk: %{risk}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS BİLDİRİM: %{risk}"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
    except: pass

@app.route("/")
def home(): return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    text = request.json.get("text", "")
    risk = ai_engine(text)
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    send_report(text, risk)
    return jsonify({"text": text, "risk": risk, "stats": stats})

@app.route("/feed")
def feed():
    # TikTok, Facebook ve X APISIZ Tarama
    query = "site:tiktok.com OR site:facebook.com OR site:x.com 'iddia ediliyor'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr"
    results = []
    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        for item in root.findall('.//item')[:10]:
            title = item.find('title').text.split(" - ")[0]
            results.append({"text": title, "risk": ai_engine(title)})
    except: pass
    return jsonify(results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))