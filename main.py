from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import random

app = Flask(__name__, template_folder="templates")
CORS(app)

# -----------------------------
# AI ANALİZ
# -----------------------------
def analyze_text(text):

    text = text.lower()

    risk = 5

    fake_words = [
        "öldü",
        "ifşa",
        "şok",
        "skandal",
        "manipülasyon",
        "yasaklandı",
        "gizli",
        "iddia",
        "son dakika",
        "sızdırıldı",
        "deepfake"
    ]

    for word in fake_words:
        if word in text:
            risk += random.randint(10, 18)

    if "http" in text:
        risk += 10

    if "twitter.com" in text or "x.com" in text:
        risk += 10

    if "instagram.com" in text:
        risk += 10

    if risk > 100:
        risk = 100

    return risk


# -----------------------------
# ANA SAYFA
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# ANALİZ API
# -----------------------------
@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json
    text = data.get("text", "")

    # SAÇMA TEXT ENGELİ
    keywords = [
        "haber",
        "iddia",
        "son dakika",
        "tweet",
        "video",
        "sosyal medya",
        "ölü",
        "deepfake",
        "seçim",
        "ifşa",
        "manipülasyon"
    ]

    valid = any(k in text.lower() for k in keywords)

    if len(text) < 15 or not valid:
        return jsonify({
            "risk": 0,
            "status": "Geçersiz içerik"
        })

    risk = analyze_text(text)

    if risk > 70:
        status = "Şüpheli"
    elif risk > 40:
        status = "Riskli"
    else:
        status = "Güvenli"

    return jsonify({
        "risk": risk,
        "status": status
    })


# -----------------------------
# SOSYAL MEDYA FEED
# -----------------------------
@app.route("/feed")
def feed():

    data = [
        {
            "text": "Seçim sonuçları manipüle edildi iddiası sosyal medyada yayıldı",
            "platform": "twitter"
        },
        {
            "text": "Ünlü oyuncunun öldüğü iddiası gündem oldu",
            "platform": "instagram"
        },
        {
            "text": "Gizli belge ifşa edildi paylaşımı yayıldı",
            "platform": "facebook"
        },
        {
            "text": "Deepfake video sosyal medyada viral oldu",
            "platform": "youtube"
        },
        {
            "text": "TikTok üzerinde yayılan görüntü tartışma yarattı",
            "platform": "tiktok"
        }
    ]

    return jsonify(data)


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )