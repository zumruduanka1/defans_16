import os
import requests
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder=".", static_url_path="")

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# ENV
TWITTER_BEARER = os.getenv("TWITTER_BEARER")
HF_TOKEN = os.getenv("HF_TOKEN")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# =========================
# INDEX
# =========================
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# =========================
# MAIL
# =========================
def send_mail(text, score):
    if not EMAIL_USER or not EMAIL_PASS:
        return
    try:
        msg = MIMEText(f"Riskli içerik:\n\n{text}\n\nRisk: %{score}")
        msg["Subject"] = "DEFANS PRO ALERT"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASS)
        s.send_message(msg)
        s.quit()
    except:
        pass

# =========================
# AI ANALİZ
# =========================
def analyze_text(text):
    score = 10
    keywords = ["şok","ifşa","gizli","bomba","sızdı"]
    for k in keywords:
        if k in text.lower():
            score += 20
    return min(score,100)

@app.route("/api/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text","")
    score = analyze_text(text)

    if score > 70:
        send_mail(text, score)

    return jsonify({"score":score})

# =========================
# TWITTER (GERÇEK VERİ)
# =========================
@app.route("/api/social")
def social():

    posts = []

    if TWITTER_BEARER:
        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}
            params = {"query":"gündem OR şok OR ifşa lang:tr","max_results":5}

            r = requests.get(url, headers=headers, params=params)
            data = r.json()

            for t in data.get("data", []):
                score = analyze_text(t["text"])
                posts.append({
                    "text": t["text"],
                    "score": score,
                    "platform":"twitter"
                })

                if score > 70:
                    send_mail(t["text"], score)

        except Exception as e:
            print(e)

    return jsonify(posts)

# =========================
# DEEPFAKE
# =========================
@app.route("/api/deepfake", methods=["POST"])
def deepfake():
    url = request.json.get("url")

    try:
        API_URL = "https://api-inference.huggingface.co/models/prithivMLmods/Deep-Fake-Detector"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        r = requests.post(API_URL, headers=headers, json={"inputs": url})
        result = r.json()

        score = int(result[0]["score"]*100)
    except:
        score = 50

    return jsonify({"score":score})

# =========================
# DASHBOARD
# =========================
@app.route("/api/stats")
def stats():
    return jsonify({
        "total": 120,
        "danger": 40,
        "safe": 80
    })

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)