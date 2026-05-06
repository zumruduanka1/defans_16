from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, random
import feedparser
from openai import OpenAI
import joblib
import os
model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
model = joblib.load(model_path)

model = joblib.load("fake_news_model.pkl")

def ml_analyze(text):
    prob = model.predict_proba([text])[0][1]  # fake olasılığı
    risk = int(prob * 100)
    return risk

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# AI ANALİZ (GERÇEK)
# -------------------------
def ai_analyze(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Metni analiz et ve 0-100 arası dezenformasyon riski ver"},
                {"role": "user", "content": text}
            ]
        )

        score = int(''.join(filter(str.isdigit, response.choices[0].message.content)))
        return min(score,100)

    except:
        return random.randint(30,80)

# -------------------------
# ANALİZ
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text","")

    risk = ml_analyze(text)

    return jsonify({"risk": risk})

# -------------------------
# HABER SCRAPING (RSS)
# -------------------------
@app.route("/news")
def news():
    url = "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr"
    feed = feedparser.parse(url)

    data = []
    for entry in feed.entries[:10]:
        data.append({
            "text": entry.title
        })

    return jsonify(data)

# -------------------------
# TWITTER (OPSİYONEL)
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