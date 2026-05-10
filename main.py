from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, json, xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder='templates')
CORS(app)

# İstatistikleri Kalıcı Yapma (Otomatik Yazma)
def load_stats():
    if os.path.exists("stats.txt"):
        try:
            with open("stats.txt", "r") as f: return json.load(f)
        except: pass
    return {"total": 1240, "risk": 380, "safe": 860}

def save_stats(s):
    with open("stats.txt", "w") as f: json.dump(s, f)

stats = load_stats()

def ai_engine(text):
    risk = 25
    if any(w in text.lower() for w in ["iddia", "yalan", "şok", "sızıntı"]): risk += 20
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            res = requests.post(url, headers={"Authorization": f"Bearer {hf_token}"}, 
                                json={"inputs": text, "parameters": {"candidate_labels": ["manipulative", "fact-based"]}}, timeout=5).json()
            risk = int(res['scores'][0] * 100)
        except: pass
    return min(risk, 98)

def send_intel(text, risk):
    user, pw, to = os.getenv("MAIL_USER"), os.getenv("MAIL_PASS"), os.getenv("MAIL_TO")
    if not all([user, pw, to]): return
    try:
        msg = MIMEText(f"DEFANS ANALİZ RAPORU\n\nİçerik: {text}\nRisk Skoru: %{risk}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS TESPİT: %{risk}"
        msg["From"], msg["To"] = user, to
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, pw)
        server.sendmail(user, [to], msg.as_string())
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
    save_stats(stats)
    send_intel(text, risk)
    return jsonify({"text": text, "risk": risk, "stats": stats})

@app.route("/feed")
def feed():
    query = "site:tiktok.com OR site:facebook.com OR site:x.com 'iddia ediliyor'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr"
    results = []
    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        for item in root.findall('.//item')[:12]:
            title = item.find('title').text.split(" - ")[0]
            results.append({"text": title, "risk": ai_engine(title)})
    except: pass
    return jsonify(results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))