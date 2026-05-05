from flask import Flask, request, jsonify, send_from_directory
import os
import requests

app = Flask(__name__, static_folder="static", static_url_path="")

# 🧠 Basit ama stabil analiz
def analyze_text(text):
    if not text or len(text) < 20:
        return {"risk": 0, "guven": 0, "yorum": "Metin çok kısa"}

    text_lower = text.lower()

    # 🚨 fake news keyword sistemi
    risk_words = [
        "öldü", "savaş", "patlama", "son dakika", "skandal",
        "ifşa", "şok", "gizli", "yasaklandı"
    ]

    risk_score = sum(1 for w in risk_words if w in text_lower)

    risk = min(risk_score * 20, 100)
    guven = 100 - risk

    return {
        "risk": risk,
        "guven": guven,
        "yorum": "Analiz tamamlandı"
    }

# 🌐 URL analiz
def analyze_url(url):
    try:
        r = requests.get(url, timeout=5)
        return analyze_text(r.text[:2000])
    except:
        return {"risk": 0, "guven": 0, "yorum": "URL okunamadı"}

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json

    if data.get("text"):
        return jsonify(analyze_text(data["text"]))

    if data.get("url"):
        return jsonify(analyze_url(data["url"]))

    return jsonify({"error": "veri yok"})

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)