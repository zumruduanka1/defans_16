from flask import Flask, render_template, request, jsonify
import os
import random

app = Flask(__name__)

# 🔥 ANA SAYFA (404 FIX)
@app.route("/")
def home():
    return render_template("index.html")


# 🔥 ANALİZ API
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")
    email = data.get("email", "")

    risk = random.randint(10, 95)

    status = "Şüpheli"
    if risk > 70:
        status = "Tehlikeli"
    elif risk < 40:
        status = "Güvenli"

    return jsonify({
        "risk": risk,
        "status": status
    })


# 🔥 SOSYAL MEDYA MOCK (GERÇEK API YOKSA)
@app.route("/api/social")
def social():
    data = [
        {"platform": "twitter", "text": "Seçim sonuçları değiştirildi iddiası", "risk": 82},
        {"platform": "instagram", "text": "Ünlü kişi öldü haberi", "risk": 65},
        {"platform": "tiktok", "text": "Gizli teknoloji videosu", "risk": 40},
        {"platform": "facebook", "text": "Sağlıkla ilgili yanlış bilgi", "risk": 78}
    ]
    return jsonify(data)


# 🔥 VIDEO (DEEPFAKE MOCK)
@app.route("/api/video", methods=["POST"])
def video():
    return jsonify({
        "score": random.randint(20, 90)
    })


# 🔥 PORT FIX (RENDER İÇİN)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)