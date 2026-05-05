from flask import Flask, request, jsonify, send_from_directory
import os
from dotenv import load_dotenv

from services.analyzer import analyze_content
from services.social_fetcher import get_twitter_data
from services.news_fetcher import get_news
from services.mailer import send_mail

load_dotenv()

app = Flask(__name__, static_folder="static")

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json

    result = analyze_content(
        text=data.get("text"),
        url=data.get("url"),
        image=data.get("image")
    )

    if result["risk"] > 75:
        send_mail("⚠️ Riskli içerik", str(result))

    return jsonify(result)

@app.route("/api/social")
def social():
    return jsonify(get_twitter_data())

@app.route("/api/news")
def news():
    return jsonify(get_news())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)