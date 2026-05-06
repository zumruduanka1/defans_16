from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import os

app = Flask(__name__, template_folder="templates")
CORS(app)

# Ana sayfa
@app.route("/")
def home():
    return render_template("index.html")

# AI ANALİZ
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    # Fake AI ama mantıklı
    risk = random.randint(10, 90)

    if any(x in text.lower() for x in ["öldü", "saldırı", "epstein", "yamyam"]):
        risk = random.randint(60, 95)

    status = "Güvenli"
    if risk > 70:
        status = "Tehlikeli"
    elif risk > 40:
        status = "Şüpheli"

    return jsonify({
        "risk": risk,
        "status": status
    })


# 🔥 SOSYAL MEDYA VERİSİ (ASLA BOŞ DÖNMEZ)
@app.route("/api/social")
def social():

    fake_data = [
        {"text": "Ünlü iş insanı öldü iddiası sosyal medyada yayıldı", "risk": 82},
        {"text": "Yeni teknoloji haberi paylaşıldı", "risk": 25},
        {"text": "Seçim sonuçları manipüle edildi iddiası", "risk": 78},
        {"text": "Bilim insanları yeni keşif yaptı", "risk": 15},
        {"text": "Ünlüler gizli listeye dahil edildi iddiası", "risk": 88},
    ]

    result = []
    for item in fake_data:
        status = "Güvenli"
        if item["risk"] > 70:
            status = "⚠️ Şüpheli"
        elif item["risk"] > 40:
            status = "⚠️ Orta Risk"

        result.append({
            "text": item["text"],
            "risk": item["risk"],
            "status": status
        })

    return jsonify(result)


# Video analizi
@app.route("/api/video", methods=["POST"])
def video():
    return jsonify({
        "score": random.randint(20, 95)
    })


# Render için
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)