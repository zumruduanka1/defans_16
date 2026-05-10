from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =====================================================
# ENV KONFİGÜRASYONU
# =====================================================
HF_TOKEN = os.getenv("HF_TOKEN") # Hugging Face API Token
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# =====================================================
# YAPAY ZEKA ANALİZ MOTORU (Hugging Face API)
# =====================================================
def ai_analysis_engine(text):
    # Eğer API Token yoksa veya hata oluşursa yedek algoritmaya geçer
    if not HF_TOKEN:
        return fallback_logic(text)
    
    try:
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": ["fake news", "real news", "propaganda", "clickbait"]}
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        # AI Skoru Hesaplama
        labels = result['labels']
        scores = result['scores']
        
        # Fake news ve propaganda olasılıklarını topla
        risk_index = 0
        for label, score in zip(labels, scores):
            if label in ["fake news", "propaganda", "clickbait"]:
                risk_index += score
        
        risk_score = int(risk_index * 100)
        
        if risk_score > 70: status = "🚨 Yapay Zeka: Yüksek Dezenformasyon!"
        elif risk_score > 40: status = "⚠️ Yapay Zeka: Şüpheli İçerik"
        else: status = "✅ Yapay Zeka: Güvenli"
        
        return risk_score, status
    except:
        return fallback_logic(text)

def fallback_logic(text):
    # API hatası durumunda çalışan yedek motor
    score = 30
    bad_words = ["şok", "iddia", "ifşa", "gizlenen", "deepfake", "öldü"]
    for word in bad_words:
        if word in text.lower(): score += 15
    return min(score, 95), "⚠️ Analiz (Yedek Motor)"

# =====================================================
# OTOMATİK MAİL SİSTEMİ
# =====================================================
def send_ai_report(content, risk, status):
    if not MAIL_USER or not MAIL_TO: return
    try:
        msg = MIMEText(f"AI Analiz Sonucu: {status}\nRisk: %{risk}\n\nİçerik:\n{content}", "plain", "utf-8")
        msg["Subject"] = f"🤖 DEFANS AI RAPORU: %{risk} Risk"
        msg["From"] = f"DEFANS AI <{MAIL_USER}>"
        msg["To"] = MAIL_TO

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Mail Hatası: {e}")

# =====================================================
# ROUTES
# =====================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    content = data.get("text", "")
    risk, status = ai_analysis_engine(content)
    
    # Her analizi mail olarak gönder
    send_ai_report(content, risk, status)
    
    return jsonify({"risk": risk, "status": status})

@app.route("/feed")
def feed():
    # Sosyal medya simülasyonu
    sim_data = [
        "Twitter: Yeni bir bot operasyonu saptandı.",
        "WhatsApp: 'Yarın sular kesilecek' haberi dezenformasyon çıktı.",
        "TikTok: Siyasilere ait deepfake videolar yayılıyor."
    ]
    posts = []
    for t in sim_data:
        risk, _ = ai_analysis_engine(t)
        posts.append({"text": t, "platform": "Sosyal Medya", "risk": risk})
    return jsonify(posts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))