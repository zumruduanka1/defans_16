from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global Sayaçlar (Sunucu çalıştığı sürece rakamları tutar)
stats = {
    "total": 0,
    "risk": 0,
    "safe": 0
}

# ENV YAPILANDIRMASI
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

def ai_analysis_engine(text):
    # Basit bir kelime bazlı puanlama + HF kontrolü
    score = 25
    bad_words = ["şok", "iddia", "ifşa", "gizlenen", "deepfake", "öldü", "manipülasyon"]
    for word in bad_words:
        if word in text.lower(): score += 15
    
    if HF_TOKEN:
        try:
            API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": text, "parameters": {"candidate_labels": ["fake", "real"]}}
            res = requests.post(API_URL, headers=headers, json=payload, timeout=5).json()
            if 'scores' in res:
                score = int(res['scores'][0] * 100) if res['labels'][0] == 'fake' else 20
        except: pass

    score = min(score, 100)
    status = "🚨 Yüksek Risk" if score > 70 else ("⚠️ Şüpheli" if score > 45 else "✅ Güvenli")
    return score, status

def send_ai_report(content, risk, status):
    if not MAIL_USER or not MAIL_TO: return
    try:
        msg = MIMEText(f"Analiz: {status}\nSkor: %{risk}\n\nİçerik:\n{content}", "plain", "utf-8")
        msg["Subject"] = f"🤖 DEFANS RAPORU: %{risk} Risk"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
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
    content = data.get("text", "")
    risk, status = ai_analysis_engine(content)
    
    # Sayaçları Güncelle
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    
    send_ai_report(content, risk, status)
    
    return jsonify({
        "risk": risk, 
        "status": status,
        "current_stats": stats # Güncel rakamları frontend'e gönderiyoruz
    })

@app.route("/feed")
def feed():
    sim_data = [
        "Twitter: Yeni bir bot operasyonu saptandı.",
        "WhatsApp: 'Yarın sular kesilecek' haberi yalan çıktı.",
        "Sosyal Medya: Yapay zeka ile üretilmiş sahte görüntüler yayılıyor."
    ]
    posts = []
    for t in sim_data:
        risk, _ = ai_analysis_engine(t)
        posts.append({"text": t, "platform": "Sosyal Medya", "risk": risk})
    return jsonify(posts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))