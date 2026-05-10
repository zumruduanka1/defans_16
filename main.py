from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- AYARLAR (Render veya .env üzerinden okunur) ---
stats = {"total": 0, "risk": 0, "safe": 0}
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")
SERPAPI_KEY = os.getenv("SERPAPI_KEY") # Aldığın key'i buraya tanımla

# --- YAPAY ZEKA ANALİZ MOTORU ---
def ai_engine(text):
    score = 25
    text_l = text.lower()
    # Şüpheli terimler kataloğu
    triggers = ["iddia", "şok", "flaş", "gerçek mi", "deepfake", "yalanlandı", "sızıntı", "acil paylaş"]
    for word in triggers:
        if word in text_l: score += 15
    
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": text, "parameters": {"candidate_labels": ["fake", "real"]}}
            res = requests.post(url, headers=headers, json=payload, timeout=5).json()
            if 'scores' in res:
                idx = res['labels'].index('fake')
                score = int(res['scores'][idx] * 100)
        except: pass
    
    score = min(score, 100)
    status = "🚨 Yüksek Risk" if score > 70 else ("⚠️ Şüpheli" if score > 45 else "✅ Güvenli")
    return score, status

# --- GÜVENLİ MAİL GÖNDERİMİ ---
def send_mail(content, risk, status):
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        print("Sistem Notu: Mail bilgileri eksik olduğu için gönderim yapılmadı.")
        return
    try:
        msg = MIMEText(f"Sistem Analizi: {status}\nRisk Skoru: %{risk}\n\nİçerik:\n{content}", "plain", "utf-8")
        msg["Subject"] = f"DEFANS PRO ANALİZ: %{risk}"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Mail hatası: {e}")

# --- GERÇEK ZAMANLI İNTERNET TARAYICI (SERPAPI) ---
def fetch_real_web_data():
    if not SERPAPI_KEY:
        return [{"text": "Sistem Notu: SerpApi anahtarı eksik!", "platform": "Sistem", "risk": 0}]

    query = "site:x.com OR site:instagram.com OR site:facebook.com 'dezenformasyon' OR 'yalan haber'"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "tbm": "nws", # Haberler sekmesinde ara
        "num": 10
    }
    
    final_feed = []
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=10).json()
        results = r.get("news_results", [])
        
        for item in results:
            title = item.get("title")
            source = item.get("source", "Web")
            risk, _ = ai_engine(title)
            final_feed.append({"text": title, "platform": source, "risk": risk})
            
    except Exception as e:
        print(f"Tarama Hatası: {e}")
        final_feed = [{"text": "Veri çekilemedi, bağlantı hatası.", "platform": "Hata", "risk": 0}]
        
    return final_feed

# --- FLASK YOLLARI ---
@app.route("/")
def index(): return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    data = request.json
    text = data.get("text", "")
    risk, status = ai_engine(text)
    
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    
    send_mail(text, risk, status)
    return jsonify({"risk": risk, "status": status, "current_stats": stats})

@app.route("/feed")
def feed():
    return jsonify(fetch_real_web_data())

if __name__ == "__main__":
    app.run(debug=True)