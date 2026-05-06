from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
import os, time, random, requests

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# -------------------
# MEMORY
# -------------------
logs = []
last_req = {}

# -------------------
# RATE LIMIT
# -------------------
def rate(ip):
    now = time.time()
    if ip in last_req and now - last_req[ip] < 0.6:
        return False
    last_req[ip] = now
    return True

# -------------------
# SOCIAL DETECTION
# -------------------
def is_social(text):
    text = text.lower()
    keys = [
        "http", "x.com", "twitter", "instagram",
        "tiktok", "youtube", "facebook",
        "haber", "news"
    ]
    return any(k in text for k in keys)

# -------------------
# AI SCORE (MOCK / SAFE)
# -------------------
def ai_score(text):
    return random.randint(25, 95)

def ai_explain(text):
    return "İçerik sosyal medya kaynaklı analiz edildi."

# -------------------
# TREND FETCH (REAL SOURCES)
# -------------------

# Google News RSS (TR)
def get_google_news():
    try:
        url = "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr"
        feed = requests.get(url, timeout=5).text
        return [{"text": "Google News feed active"}]
    except:
        return []

# Reddit trend (public)
def get_reddit():
    try:
        url = "https://www.reddit.com/r/worldnews/top.json?limit=5"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5).json()

        return [
            {"text": x["data"]["title"]}
            for x in r["data"]["children"]
        ]
    except:
        return []

# TikTok / Instagram (SIMULATION SAFE MODE)
def get_social_mock():
    return [
        {"text": "TikTok viral içerik trend analizi"},
        {"text": "Instagram gündem: sahte haber tartışması"},
    ]

# -------------------
# ANALYZE
# -------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    ip = request.remote_addr

    if not rate(ip):
        return jsonify({"error": "rate limit"}), 429

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "empty"}), 400

    if not is_social(text):
        return jsonify({
            "risk": 0,
            "why": "Sosyal medya/haber içeriği algılanmadı"
        })

    risk = ai_score(text)

    result = {
        "text": text,
        "risk": risk,
        "why": ai_explain(text)
    }

    logs.append(result)
    if len(logs) > 50:
        logs.pop(0)

    socketio.emit("live", result)

    if risk > 70:
        socketio.emit("alert", result)

    return jsonify(result)

# -------------------
# TREND API
# -------------------
@app.route("/trend")
def trend():
    data = []

    data += get_google_news()
    data += get_reddit()
    data += get_social_mock()

    return jsonify(data)

# -------------------
# HOME
# -------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------
# LIVE STREAM SIMULATION
# -------------------
def push_live():
    while True:
        time.sleep(5)

        sample = random.choice([
            "Instagram viral içerik",
            "X.com gündem haberi",
            "TikTok trend sahte haber"
        ])

        data = {
            "text": sample,
            "risk": random.randint(20, 95)
        }

        socketio.emit("live", data)

# -------------------
# START
# -------------------
if __name__ == "__main__":
    socketio.start_background_task(push_live)

    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )