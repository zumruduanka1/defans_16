# main.py - Akıllı Filtreleme Sürümü
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, smtplib
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, template_folder='templates')
CORS(app)

# Ayarlar (Render'dan tanımlanmalı)
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 4, "risk": 0, "safe": 1}
sent_intel = set()

# DEZENFORMASYON İŞARETLERİ (Bu kelimeler yoksa analiz yapma)
INTEL_KEYWORDS = [
    "iddia", "sızıntı", "yalanlandı", "gerçek mi", "şok", "ifşa", 
    "operasyon", "gizli", "provokasyon", "manipülasyon", "servis edildi"
]

def is_suspicious(text):
    """Metin analiz edilmeye değer mi? (Ön Filtre)"""
    text_lower = text.lower()
    return any(word in text_lower for word in INTEL_KEYWORDS)

def ai_engine(text):
    if not is_suspicious(text):
        return 10 # Şüpheli kelime yoksa düşük risk ver ve geç
    
    try:
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": text, "parameters": {"candidate_labels": ["manipulative", "news", "propaganda"]}}
        res = requests.post(url, headers=headers, json=payload, timeout=8).json()
        scores = dict(zip(res['labels'], res['scores']))
        return int((scores.get('manipulative', 0) + scores.get('propaganda', 0)) * 100)
    except: return 35

def send_intel_report(content, risk, label):
    # Eşik: %30 ve üzeri, sadece şüpheli etiketli içerikler
    if not MAIL_USER or not MAIL_PASS or risk < 30: return
    try:
        msg = MIMEText(f"KAYNAK: {label}\nSKOR: %{risk}\n\nİÇERİK: {content}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS TESPİT: %{risk}"
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
    return jsonify({"text": text, "risk": risk, "current_stats": stats})

@app.route("/feed")
def feed():
    global sent_intel
    # Aramayı daha spesifik yapıyoruz (Her şeyi çekme)
    query = "site:x.com OR site:facebook.com 'iddia ediliyor' OR 'yalanlandı' OR 'provokasyon'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    results = []
    try:
        resp = requests.get(url, timeout=7)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:15]:
            title = item.find('title').text.split(" - ")[0]
            # ÖNEMLİ: Sadece şüpheli kelime içerenleri analiz et ve listeye ekle
            if is_suspicious(title):
                risk = ai_engine(title)
                if title not in sent_intel and risk >= 30:
                    send_intel_report(title, risk, "OTOMATIK TARAMA")
                    sent_intel.add(title)
                results.append({"text": title, "risk": risk})
    except: pass
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)