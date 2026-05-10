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

# --- YAPILANDIRMA (Render/Environment Variables) ---
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")  # 16 haneli Uygulama Şifresi
MAIL_TO = os.getenv("MAIL_TO")

# Sayaçlar ve Takip Listesi
stats = {"total": 0, "risk": 0, "safe": 0}
sent_alerts = set() # Aynı içeriği tekrar mail atmamak için hafıza

def ai_engine(text):
    """Metni Hugging Face AI üzerinden analiz eder (Doğruluk Odaklı)"""
    if not HF_TOKEN:
        # Token yoksa metin uzunluğu ve anahtar kelimelere göre mantıksal tahmin
        keywords = ["iddia", "şok", "flaş", "gizli", "ifşa", "fake", "yalan"]
        score = 25
        for k in keywords:
            if k in text.lower(): score += 15
        return min(score, 95)
    
    try:
        # Dezenformasyon ve Propaganda tespiti için gelişmiş model
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": text, 
            "parameters": {"candidate_labels": ["fake news", "propaganda", "real news"]}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8).json()
        
        # Risk skorunu hesapla (Fake News + Propaganda oranları)
        scores = dict(zip(res['labels'], res['scores']))
        risk_val = (scores.get('fake news', 0) + scores.get('propaganda', 0)) * 100
        return int(risk_val)
    except:
        return 40 # Hata durumunda nötr risk

def send_defans_mail(content, risk, source_type):
    """Her türlü içeriği rapor etiketiyle mail gönderir"""
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        return

    try:
        # Risk seviyesine göre görsel etiket
        tag = "🔴 KRİTİK" if risk > 70 else ("🟡 ŞÜPHELİ" if risk > 35 else "🟢 GÜVENLİ")
        subject = f"DEFANS RAPORU: {source_type} ({tag} - %{risk})"
        
        body = f"""
        -------------------------------------------
        DEFANS PRO | İSTİHBARAT BİLDİRİMİ
        -------------------------------------------
        KAYNAK TÜRÜ: {source_type}
        ANALİZ TARİHİ: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        RİSK SKORU: %{risk}
        DURUM: {tag}
        
        İÇERİK ÖZETİ:
        {content}
        -------------------------------------------
        Bu rapor otomatik olarak oluşturulmuştur.
        """
        
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"Defans AI <{MAIL_USER}>"
        msg["To"] = MAIL_TO

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Mail Gönderim Hatası: {e}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    """Kullanıcının bizzat kutuya yazdığı analizler"""
    global stats
    data = request.json
    text = data.get("text", "")
    risk = ai_engine(text)
    
    # İstatistikleri güncelle
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    
    # KULLANICI ANALİZİ OLARAK HER DURUMDA MAİL AT
    send_defans_mail(text, risk, "KULLANICI SORGUSU")
    
    return jsonify({
        "risk": risk, 
        "status": "RİSKLİ / ŞÜPHELİ" if risk > 45 else "GÜVENLİ", 
        "current_stats": stats
    })

@app.route("/feed")
def feed():
    """Tüm sosyal medya bulgularını raporlar (Filtreleme yok)"""
    global sent_alerts
    # X, Instagram ve Haber ağlarını kapsayan yasal RSS köprüsü
    query = "site:x.com OR site:instagram.com dezenformasyon OR 'sahte haber' OR 'iddia edildi'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    
    results = []
    try:
        resp = requests.get(url, timeout=7)
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item')[:10]: # Son 10 haber
            title = item.find('title').text
            risk = ai_engine(title)
            
            # AYNI HABERİ TEKRAR ATMAMAK İÇİN KONTROL
            if title not in sent_alerts:
                # FİLTRE KALDIRILDI: Tüm bulduklarını mail atar
                send_defans_mail(title, risk, "OTOMATİK TARAMA BULGUSU")
                sent_alerts.add(title)
            
            results.append({"text": title, "risk": risk})
    except Exception as e:
        results = [{"text": f"Tarayıcı hatası: {str(e)}", "risk": 0}]
        
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)