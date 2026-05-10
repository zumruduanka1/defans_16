from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib, xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder='templates')
CORS(app)

# Global İstatistikler
stats = {"total": 4, "risk": 0, "safe": 1}
sent_intel = set()

def ai_engine(text):
    risk = 20
    scam_keywords = ["iddia", "yalan", "şok", "gizli", "sızıntı", "flaş", "gerçek mi"]
    for word in scam_keywords:
        if word in text.lower(): risk += 15
    
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f"Bearer {hf_token}"}
            payload = {"inputs": text, "parameters": {"candidate_labels": ["manipulative", "fact-based"]}}
            res = requests.post(url, headers=headers, json=payload, timeout=5).json()
            if 'scores' in res:
                risk = int(res['scores'][0] * 100)
        except: pass
    return min(risk, 98)

def send_mail(content, risk):
    user = os.getenv("MAIL_USER")
    pw = os.getenv("MAIL_PASS")
    to = os.getenv("MAIL_TO")
    if not user or not pw or risk < 30: return
    try:
        msg = MIMEText(f"DEFANS PRO ANALİZ\n\nİçerik: {content}\nRisk Skoru: %{risk}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS RAPORU: %{risk}"
        msg["From"] = user
        msg["To"] = to
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, pw)
        server.sendmail(user, [to], msg.as_string())
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
    send_mail(text, risk)
    return jsonify({"text": text, "risk": risk, "stats": stats})

@app.route("/feed")
def feed():
    # TikTok, Facebook, X ve Instagram Tarayıcı
    query = "site:tiktok.com OR site:facebook.com OR site:x.com OR site:instagram.com 'iddia ediliyor' OR 'yalanlandı'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    results = []
    try:
        resp = requests.get(url, timeout=7)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:12]:
            title = item.find('title').text.split(" - ")[0]
            risk = ai_engine(title)
            results.append({"text": title, "risk": risk})
    except: pass
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)