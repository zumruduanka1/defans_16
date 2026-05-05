from flask import Flask, render_template, request, jsonify
import os
import sys

# 🔧 path fix (import hatası çözüm)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.analyzer import analyze_text
from services.social import get_social_data
from services.mailer import send_alert

app = Flask(__name__)

# basit hafıza (son analizler)
history = []

# 🏠 HOME
@app.route("/")
def home():
    return render_template("index.html")


# 🧠 METİN ANALİZ
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "").strip()

    result = analyze_text(text)

    history.append({
        "text": text,
        "risk": result["risk"],
        "label": result["label"]
    })

    # 🚨 riskliyse mail
    if result["risk"] >= 70:
        send_alert(text)

    return jsonify(result)


# 🌐 URL ANALİZ
@app.route("/analyze_url", methods=["POST"])
def analyze_url():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"risk": 0, "safe": 0, "label": "URL yok"})

    result = analyze_text(url)

    history.append({
        "text": url,
        "risk": result["risk"],
        "label": result["label"]
    })

    if result["risk"] >= 70:
        send_alert(url)

    return jsonify(result)


# 🌍 SOSYAL MEDYA
@app.route("/social")
def social():
    posts = get_social_data()

    analyzed = []

    for p in posts:
        result = analyze_text(p["text"])

        item = {
            "platform": p.get("platform", "Unknown"),
            "text": p.get("text", ""),
            "url": p.get("url", "#"),
            "risk": result["risk"],
            "label": result["label"]
        }

        # 🚨 riskliyse mail
        if result["risk"] >= 70:
            send_alert(p["text"])

        analyzed.append(item)

    return jsonify(analyzed)


# 📊 GEÇMİŞ
@app.route("/history")
def get_history():
    return jsonify(history[-20:])  # son 20 kayıt


# ❤️ HEALTH CHECK (Render için)
@app.route("/health")
def health():
    return "OK"


# 🚀 START
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)