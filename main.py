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

# --- YAPILANDIRMA (Render/Environment üzerinden okunur) ---
HF_TOKEN = os.getenv("HF_TOKEN")
MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS") # Gmail Uygulama Şifresi (16 haneli)
MAIL_TO = os.getenv("MAIL_TO")

# İstatistik Takibi ve Mail Hafızası
stats = {"total": 0, "risk": 0, "safe": 0}
sent_intel = set() # Aynı başlığı tekrar mail atmamak için

def ai_engine(text):
    """Metni Hugging Face AI ile Manipülasyon ve Dezenformasyon açısından analiz eder"""
    if not HF_TOKEN:
        # Token tanımlı değilse; şüpheli anahtar kelimelere göre temel puanlama yapar
        indicators = ["iddia", "sızıntı", "flaş", "yalanlandı", "gizli", "şok", "gerçek mi"]
        score = 20
        for word in indicators:
            if word in text.lower(): score += 15
        return min(score, 90)

    try:
        # Gerçek zamanlı NLP Analiz Modeli
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": ["manipulative", "fact-based news", "propaganda", "clickbait"]}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8).json()
        
        # Risk faktörlerini (manipülasyon, propaganda, tık tuzağı) birleştirerek hesapla
        scores = dict(zip(res['labels'], res['scores']))
        risk_val = (scores.get('manipulative', 0) + scores.get('propaganda', 0) + scores.get('clickbait', 0)) * 100
        return int(risk_val)
    except:
        return 35 # Hata durumunda bile 'şüpheli' sınırında raporlama yapması için

def send_intel_report(content, risk, label):
    """
    Rapor Gönderici: %30 Eşiği Aktif.
    Hem manuel sorguları hem otomatik bulguları raporlar.
    """
    if not MAIL_USER or not MAIL_PASS or not MAIL_TO:
        return
    
    # %30 risk eşiği kontrolü
    if risk < 30:
        return

    try:
        # Risk seviyesine göre konu başlığını renklendir/etiketle
        if risk > 75: tag = "🔴 KRİTİK DEZENFORMASYON"
        elif risk > 50: tag = "🟠 YÜKSEK ŞÜPHE"
        else: tag = "🟡 DÜŞÜK SEVİYE ŞÜPHE (ERKEN UYARI)"

        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        subject = f"DEFANS {tag}: %{risk}"
        
        body = f"""
        -------------------------------------------
        DEFANS PRO | İSTİHBARAT RAPORU
        -------------------------------------------
        KAYNAK TÜRÜ: {label}
        ZAMAN: {timestamp}
        RİSK SKORU: %{risk}
        DURUM: {tag}
        
        ANALİZ EDİLEN İÇERİK:
        {content}
        -------------------------------------------
        Bu rapor %30 hassasiyet eşiğiyle otomatik oluşturulmuştur.
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
        print(f"Mail Raporlama Hatası: {e}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    """Kullanıcının manuel girdiği metinlerin analizi"""
    global stats
    data = request.json
    text = data.get("text", "")
    risk = ai_engine(text)
    
    # İstatistikleri güncelle
    stats["total"] += 1
    if risk > 45: stats["risk"] += 1
    else: stats["safe"] += 1
    
    # Kullanıcı sorgusunu her zaman mail at (Risk %30 üzerindeyse)
    send_intel_report(text, risk, "KULLANICI SORGUSU")
    
    return jsonify({
        "risk": risk, 
        "status": "RİSKLİ/ŞÜPHELİ" if risk > 45 else "GÜVENLİ", 
        "current_stats": stats
    })

@app.route("/feed")
def feed():
    """
    İnternet Tarayıcı: X, Instagram ve Haber kaynaklarını tarar.
    %30 ve üzeri tüm yeni bulguları mail atar.
    """
    global sent_intel
    # Yalan haberlerin embryo aşamasını (iddia, sızıntı vb.) yakalamak için optimize sorgu
    query = "site:x.com OR site:instagram.com 'iddia ediliyor' OR 'sızıntı' OR 'gerçek dışı'"
    url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr"
    
    results = []
    try:
        resp = requests.get(url, timeout=7)
        root = ET.fromstring(resp.content)
        
        for item in root.findall('.//item')[:12]:
            title = item.find('title').text
            risk = ai_engine(title)
            
            # Daha önce raporlanmamış içerikleri raporla
            if title not in sent_intel:
                send_intel_report(title, risk, "OTOMATİK TARAMA BULGUSU")
                sent_intel.add(title)
            
            results.append({"text": title, "risk": risk})
    except Exception as e:
        results = [{"text": "Veri akışı şu an sağlanamıyor...", "risk": 0}]
        
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)