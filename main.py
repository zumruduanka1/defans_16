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

# --- YAPILANDIRMA ---
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

stats = {"total": 0, "risk": 0, "safe": 0}
sent_alerts = set() # Aynı internet haberini tekrar atmamak için

def ai_engine(text):
    """Hugging Face AI ile Dezenformasyon Analizi"""
    if not HF_TOKEN: return 40 # Token yoksa sabit orta risk
    try:
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": text, "parameters": {"candidate_labels": ["fake news", "real news"]}}
        res = requests.post(url, headers=headers, json=payload, timeout=5).json()
        idx = res['labels'].index('fake news')
        return int(res['scores'][idx] * 100)
    except: return 40

def send_intel_mail(content, risk, source_type):
    """
    Rapor Gönderici
    source_type: 'Kullanıcı Analizi' veya 'Otomatik Tarama'
    """
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO: return
    
    try:
        status = "🚨 YÜKSEK RİSK" if risk > 70 else ("⚠️ ŞÜPHELİ" if risk > 40 else "✅ GÜVENLİ")
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        subject = f"DEFANS {source_type}: %{risk}"
        body = f"""
        DEFANS PRO İSTİHBARAT RAPORU
        ---------------------------
        KAYNAK: {source_type}
        ZAMAN: {timestamp}
        SKOR: %{risk}
        DURUM: {status}
        
        İÇERİK:
        {content}
        ---------------------------
        """
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"Defans AI <{MAIL_USER}>"
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
    """Kullanıcının butona basarak yaptığı tüm analizleri mail atar"""
    global stats
    data = request.json
    text = data.get("text", "")
    risk = ai_engine(text)
    
    # İstatistik Güncelleme
    stats["total"] += 1
    if risk > 50: stats["risk"] += 1
    else: stats["safe"] += 1
    
    # Kullanıcı analizini her durumda (belirterek) mail at
    send_intel_mail(text, risk, "KULLANICI ANALİZİ")
    
    return jsonify({
        "risk": risk, 
        "status": "RİSKLİ" if risk > 50 else "GÜVENLİ", 
        "current_stats": stats
    })

@app.route("/feed")
def feed():
    """İnterneti tarar ve SADECE yalan olma ihtimali olanları mail atar"""
    global sent_alerts
    # Sosyal medya ve haber sitelerindeki sahte haber içeriklerini tarayan yasal köprü
    query = "site:x.com OR site:instagram.com 'iddia' OR 'fake news' OR 'yalan haber'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    
    results = []
    try:
        resp = requests.get(url, timeout=5)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:8]:
            title = item.find('title').text
            risk = ai_engine(title)
            
            # KRİTİK FİLTRE: Sadece yalan haber olma ihtimali %60+ olanları mail at
            if risk > 60 and title not in sent_alerts:
                send_intel_mail(title, risk, "OTOMATİK TARAMA (YALAN HABER TESPİTİ)")
                sent_alerts.add(title)
            
            results.append({"text": title, "risk": risk})
    except:
        results = [{"text": "Canlı akış şu an yüklenemiyor.", "risk": 0}]
        
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)