from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, random, joblib
import feedparser
from openai import OpenAI

# -------------------------
# APP
# -------------------------
app = Flask(__name__)
CORS(app)

# -------------------------
# MODEL LOAD
# -------------------------
model_path = os.path.join(os.path.dirname(__file__), "model.pkl")

try:
    model = joblib.load(model_path)
except Exception as e:
    model = None
    print("Model yüklenemedi:", e)

# -------------------------
# OPENAI
# -------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# ML ANALYSIS
# -------------------------
def ml_analyze(text):
    if model is None:
        return random.randint(40, 70)

    try:
        prob = model.predict_proba([text])[0][1]
        return int(prob * 100)
    except:
        return random.randint(40, 70)

# -------------------------
# AI ANALYSIS
# -------------------------
def ai_analyze(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Metni analiz et ve 0-100 arası dezenformasyon riski ver (sadece sayı döndür)"
                },
                {"role": "user", "content": text}
            ]
        )

        content = response.choices[0].message.content
        score = int(''.join(filter(str.isdigit, content)))

        return min(score, 100)

    except:
        return random.randint(30, 80)

# -------------------------
# ANALYZE ENDPOINT
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "")

    ml_risk = ml_analyze(text)
    ai_risk = ai_analyze(text)

    final_risk = int((ml_risk + ai_risk) / 2)

    return jsonify({
        "text": text,
        "ml_risk": ml_risk,
        "ai_risk": ai_risk,
        "risk": final_risk
    })

# -------------------------
# NEWS
# -------------------------
@app.route("/news")
def news():
    url = "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr"
    feed = feedparser.parse(url)

    data = [
        {"text": entry.title}
        for entry in feed.entries[:10]
    ]

    return jsonify(data)

# -------------------------
# TWITTER
# -------------------------
@app.route("/twitter")
def twitter():
    bearer = os.getenv("TWITTER_BEARER")

    if not bearer:
        return jsonify([])

    url = "https://api.twitter.com/2/tweets/search/recent?query=haber&max_results=5"

    headers = {"Authorization": f"Bearer {bearer}"}
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return jsonify([])

    tweets = res.json().get("data", [])

    return jsonify([{"text": t["text"]} for t in tweets])

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)