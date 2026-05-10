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

# --- AYARLAR ---
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS") # 16 haneli Gmail Uygulama Şifresi
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 4, "risk": 0, "safe": 1} # Görseldeki başlangıç değerlerin
sent_intel = set()

def ai_engine(text):
    """Manipülasyon ve Yalan Haber Analizi"""
    if not HF_TOKEN:
        indicators = ["iddia", "sızıntı", "yalanlandı", "gerçek mi", "şok", "ifşa"]
        score = 25
        for word in indicators:
            if word in text.lower(): score += 15
        return min(score, 90)
    try:
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": ["manipulative", "fact-based news", "propaganda", "clickbait"]}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8).json()
        scores = dict(zip(res['labels'], res['scores']))
        risk = (scores.get('manipulative', 0) + scores.get('propaganda', 0) + scores.get('clickbait', 0)) * 100
        return int(risk)
    except: return 35

def send_intel_report(content, risk, label):
    """Mail Gönderme Fonksiyonu (Fix Edildi)"""
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        print("Sistem Notu: Mail ayarları eksik.")
        return
    
    if risk < 30: return # En ufak şüpheyi bile yakalar

    try:
        tag = "🔴 KRİTİK" if risk > 70 else "🟡 ŞÜPHELİ"
        subject = f"DEFANS TESPİT {tag}: %{risk} ({label})"
        
        body = f"""
        DEFANS PRO ANALİZ RAPORU
        ---------------------------
        KAYNAK: {label}
        ZAMAN: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        RİSK SKORU: %{risk}
        
        İÇERİK:
        {content}
        ---------------------------
        """
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO

        # Gmail için en güvenli bağlantı metodu
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
        print("Rapor mail olarak gönderildi.")
    except Exception as e:
        print(f"Mail Hatası: {str(e)}")

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
    
    # Her analizde mail tetiklenir (Eşik %30)
    send_intel_report(text, risk, "KULLANICI SORGUSU")
    
    return jsonify({"risk": risk, "status": "Şüpheli" if risk > 45 else "Güvenli", "current_stats": stats})

@app.route("/feed")
def feed():
    """TikTok, Facebook, Instagram ve X Tarayıcı (APISIZ)"""
    global sent_intel
    # TikTok, Facebook, Instagram ve X üzerindeki iddiaları yakalamak için genişletilmiş sorgu
    query = "site:tiktok.com OR site:facebook.com OR site:x.com OR site:instagram.com 'iddia ediliyor' OR 'gerçek mi'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    
    results = []
    try:
        resp = requests.get(url, timeout=7)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:12]:
            title = item.find('title').text
            risk = ai_engine(title)
            
            if title not in sent_intel:
                send_intel_report(title, risk, "OTOMATİK SOSYAL TARAMA")
                sent_intel.add(title)
            
            results.append({"text": title, "risk": risk})
    except:
        results = [{"text": "Canlı akış bekleniyor...", "risk": 0}]
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)