# main.py dosyanın tamamını bununla değiştir
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app)

HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 4, "risk": 0, "safe": 1}
sent_intel = set()

def ai_engine(text):
    if not HF_TOKEN:
        indicators = ["iddia", "sızıntı", "yalanlandı", "gerçek mi", "şok", "ifşa", "facebook", "tiktok"]
        score = 25
        for word in indicators:
            if word in text.lower(): score += 15
        return min(score, 90)
    try:
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": text, "parameters": {"candidate_labels": ["manipulative", "fact-based", "propaganda", "clickbait"]}}
        res = requests.post(url, headers=headers, json=payload, timeout=8).json()
        scores = dict(zip(res['labels'], res['scores']))
        risk = (scores.get('manipulative', 0) + scores.get('propaganda', 0) + scores.get('clickbait', 0)) * 100
        return int(risk)
    except: return 35

def send_intel_report(content, risk, label):
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO or risk < 30: return
    try:
        tag = "KRITIK" if risk > 70 else "SUPHELI"
        body = f"KAYNAK: {label}\nSKOR: %{risk}\n\nICERIK:\n{content}"
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"DEFANS {tag}: %{risk}"
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
    data = request.json
    text = data.get("text", "")
    risk = ai_engine(text)
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    send_intel_report(text, risk, "KULLANICI SORGUSU")
    return jsonify({"text": text, "risk": risk, "status": "Şüpheli" if risk > 45 else "Güvenli", "current_stats": stats})

@app.route("/feed")
def feed():
    global sent_intel
    # Facebook, TikTok ve X odaklı temiz veri çekme
    query = "site:facebook.com OR site:tiktok.com OR site:x.com 'iddia' OR 'yalanlandı'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    results = []
    try:
        resp = requests.get(url, timeout=7)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:15]:
            title = item.find('title').text.split(" - ")[0] # Kaynak ismini başlıktan temizle
            risk = ai_engine(title)
            if title not in sent_intel:
                send_intel_report(title, risk, "OTOMATIK TARAMA")
                sent_intel.add(title)
            results.append({"text": title, "risk": risk, "time": datetime.now().strftime('%H:%M')})
    except:
        results = [{"text": "Haber akışı yüklenemedi.", "risk": 0, "time": "00:00"}]
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)