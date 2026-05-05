from flask import Flask, request, jsonify
import os
from analyzer import analyze_all

app = Flask(__name__)

@app.route("/")
def home():
    return "AI analiz sistemi aktif 🚀"

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json

    text = data.get("text", "")
    url = data.get("url")
    media = data.get("media", False)

    result = analyze_all(text, url, media)

    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)