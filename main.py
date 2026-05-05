from flask import Flask, request, jsonify, send_from_directory
import os
import requests
from transformers import pipeline

app = Flask(__name__, static_folder="static", static_url_path="")

# 🔥 HuggingFace modeli (küçük ve hızlı)
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# 📊 Basit analiz sistemi (saçma inputları elemek için)
def analyze_text(text):
    if len(text) < 15:
        return {"risk": 0, "guven": 0, "yorum": "Metin çok kısa"}

    if any(x in text.lower() for x in ["fjj", "asdf", "123", "xxx"]):
        return {"risk": 0, "guven": 0, "yorum": "Anlamsız içerik"}

    result = classifier(text)[0]

    if result["label"] == "NEGATIVE":
        risk = int(result["score"] * 100)
        guven = 100 - risk
    else:
        guven = int(result["score"] * 100)
        risk = 100 - guven

    return {
        "risk": risk,
        "guven": guven,
        "yorum": "Analiz tamamlandı"
    }

# 🌐 URL analiz
def analyze_url(url):
    try:
        r = requests.get(url, timeout=5)
        text = r.text[:2000]
        return analyze_text(text)
    except:
        return {"risk": 0, "guven": 0, "yorum": "URL okunamadı"}

# 🧠 API
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json

    text = data.get("text")
    url = data.get("url")

    if text:
        return jsonify(analyze_text(text))

    if url:
        return jsonify(analyze_url(url))

    return jsonify({"error": "veri yok"})

# 🌐 FRONTEND
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# 🚀 Render için PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)