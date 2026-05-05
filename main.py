from flask import Flask, request, jsonify, send_from_directory
from services.analyzer import analyze_content
from services.social_fetcher import get_social_posts
from services.mailer import send_mail
import os

app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json

    result = analyze_content(text=data.get("text"))

    if result["risk"] > 70:
        send_mail("⚠️ Riskli içerik bulundu", str(data))

    return jsonify(result)

@app.route("/api/social")
def social():
    return jsonify(get_social_posts())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)