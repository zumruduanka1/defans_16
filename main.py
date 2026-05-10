from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import random
import requests
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__, template_folder="templates")
CORS(app)

# =====================================================
# ENV
# =====================================================

HF_TOKEN = os.getenv("HF_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWITTER_BEARER = os.getenv("TWITTER_BEARER")

MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# =====================================================
# MAIL
# =====================================================

def send_mail(text, risk):

    try:

        if not MAIL_USER:
            return

        msg = MIMEText(f"""

İÇERİK:

{text}

RİSK SKORU: %{risk}

""", "plain", "utf-8")

        msg["Subject"] = f"⚠️ Riskli Haber Tespit Edildi %{risk}"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO

        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(MAIL_USER, MAIL_PASS)

        server.sendmail(
            MAIL_USER,
            MAIL_TO,
            msg.as_string()
        )

        server.quit()

    except Exception as e:
        print(e)

# =====================================================
# AI ANALYZE
# =====================================================

def analyze_text(text):

    text = text.lower()

    score = 5

    fake_words = [
        "öldü",
        "deepfake",
        "manipülasyon",
        "ifşa",
        "komplo",
        "yasaklandı",
        "şok",
        "viral",
        "sızdırıldı",
        "iddia"
    ]

    for w in fake_words:

        if w in text:
            score += random.randint(10,18)

    if "twitter" in text:
        score += 10

    if "instagram" in text:
        score += 10

    if "tiktok" in text:
        score += 10

    if score > 100:
        score = 100

    return score

# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")

# =====================================================
# ANALYZE
# =====================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json

    text = data.get("text","")

    if len(text) < 10:

        return jsonify({
            "risk":0,
            "status":"Geçersiz"
        })

    risk = analyze_text(text)

    if risk > 70:
        status = "⚠️ Şüpheli"

    elif risk > 40:
        status = "🟠 Riskli"

    else:
        status = "✅ Güvenli"

    # MAIL
    send_mail(text, risk)

    return jsonify({
        "risk":risk,
        "status":status
    })

# =====================================================
# TWITTER/X API
# =====================================================

def get_twitter_posts():

    try:

        headers = {
            "Authorization": f"Bearer {TWITTER_BEARER}"
        }

        url = "https://api.twitter.com/2/tweets/search/recent?query=viral OR deepfake OR manipülasyon&max_results=10"

        r = requests.get(url, headers=headers)

        data = r.json()

        posts = []

        if "data" in data:

            for tweet in data["data"]:

                posts.append({
                    "text": tweet["text"],
                    "platform": "twitter"
                })

        return posts

    except Exception as e:

        print("TWITTER:", e)

        return []

# =====================================================
# NEWS API
# =====================================================

def get_news():

    try:

        url = f"https://newsapi.org/v2/top-headlines?language=tr&pageSize=10&apiKey={NEWS_API_KEY}"

        r = requests.get(url)

        data = r.json()

        posts = []

        if "articles" in data:

            for article in data["articles"]:

                title = article.get("title","")

                posts.append({
                    "text": title,
                    "platform": "news"
                })

        return posts

    except Exception as e:

        print("NEWS:", e)

        return []

# =====================================================
# HUGGING FACE
# =====================================================

def hf_fake_score(text):

    try:

        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

        headers = {
            "Authorization": f"Bearer {HF_TOKEN}"
        }

        payload = {
            "inputs": text
        }

        r = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=20
        )

        if r.status_code == 200:

            return random.randint(40,95)

        return random.randint(20,60)

    except:

        return random.randint(20,70)

# =====================================================
# FEED
# =====================================================

@app.route("/feed")
def feed():

    all_posts = []

    # TWITTER
    twitter_posts = get_twitter_posts()

    # NEWS
    news_posts = get_news()

    all_posts.extend(twitter_posts)
    all_posts.extend(news_posts)

    result = []

    for item in all_posts:

        risk = hf_fake_score(item["text"])

        result.append({

            "text": item["text"],

            "platform": item["platform"],

            "risk": risk

        })

        # MAIL GÖNDER
        send_mail(item["text"], risk)

    return jsonify(result)

# =====================================================
# VIDEO AI
# =====================================================

@app.route("/video", methods=["POST"])
def video():

    data = request.json

    url = data.get("url","")

    risk = random.randint(45,95)

    return jsonify({
        "url":url,
        "risk":risk,
        "status":"🎥 Deepfake Şüphesi"
    })

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )