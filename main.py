from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Sayaçlar
stats = {"total": 0, "risk": 0, "safe": 0}

# AYARLAR (Render Panelinden Girilmeli)
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER") # Gmail adresin
MAIL_PASS = os.getenv("MAIL_PASS") # 16 haneli Uygulama Şifresi
MAIL_TO = os.getenv("MAIL_TO")     # Raporun gideceği diğer mail

def ai_engine(text):
    text_l = text.lower()
    score = 30
    triggers = ["şok", "iddia", "ifşa", "gizli", "flaş", "deepfake", "öldü", "yasak", "tıkla", "acil"]
    for word in triggers:
        if word in text_l: score += 12
    
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": text, "parameters": {"candidate_labels": ["fake", "real"]}}
            res = requests.post(url, headers=headers, json=payload, timeout=5).json()
            if 'scores' in res:
                score = int(res['scores'][0] * 100) if res['labels'][0] == 'fake' else 20
        except: pass
    
    score = min(score, 100)
    status = "🚨 Yüksek Risk" if score > 70 else ("⚠️ Şüpheli" if score > 45 else "✅ Güvenli")
    return score, status

def send_mail(content, risk, status):
    # Bilgiler eksikse göndermeyi deneme bile
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        print("HATA: Mail bilgileri eksik (MAIL_USER, MAIL_PASS veya MAIL_TO)")
        return
        
    try:
        subject = f"🚨 DEFANS ANALİZ: %{risk} Risk"
        body = f"İçerik: {content}\n\nDurum: {status}\nRisk Skoru: %{risk}\nTarih: {datetime.now()}"
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"Defans Analiz <{MAIL_USER}>"
        msg["To"] = MAIL_TO

        # Gmail için en güvenli bağlantı metodu
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
        print("BAŞARILI: Mail iletildi.")
    except Exception as e:
        print(f"SMTP HATASI: {str(e)}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    global stats
    data = request.json
    content = data.get("text", "")
    risk, status = ai_engine(content)
    
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    
    send_mail(content, risk, status)
    
    return jsonify({"risk": risk, "status": status, "current_stats": stats})

@app.route("/feed")
def feed():
    # DAHA FAZLA KAYNAK EKLEDİM
    sources = [
        {"t": "X (Twitter): Yapay zeka ile üretilmiş sahte bir siyasi video yayılıyor.", "p": "Twitter"},
        {"t": "Instagram: 'Ücretsiz tatil' çekilişi adı altında kimlik hırsızlığı yapılıyor.", "p": "Instagram"},
        {"t": "TikTok: Deepfake teknolojisiyle ünlülerin sesi taklit ediliyor.", "p": "TikTok"},
        {"t": "WhatsApp: Şehir efsanesi tadındaki ses kayıtları gruplarda hızla paylaşılıyor.", "p": "WhatsApp"},
        {"t": "Facebook: Eski haberler yeniymiş gibi servis edilerek panik yaratılıyor.", "p": "Facebook"},
        {"t": "Telegram: Kripto piyasasını manipüle eden asılsız 'balina' haberleri.", "p": "Telegram"}
    ]
    posts = []
    for s in sources:
        risk, _ = ai_engine(s['t'])
        posts.append({"text": s['t'], "platform": s['p'], "risk": risk})
    return jsonify(posts)

if __name__ == "__main__":
    app.run(debug=True)