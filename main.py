from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, os, smtplib, re
from email.mime.text import MIMEText

app = Flask(__name__, static_folder="static")
CORS(app)

# ENV
HF_TOKEN = os.getenv("HF_TOKEN")
X_BEARER = os.getenv("X_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MY_EMAIL = os.getenv("MY_EMAIL")
FRIEND_EMAIL = os.getenv("FRIEND_EMAIL")

headers_hf = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

history = []

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

# 🧠 GELİŞMİŞ ANALİZ
def analyze_text(text):
    text_lower = text.lower()

    risk = 0

    # 🚨 clickbait / fake pattern
    patterns = [
        "şok", "inanamayacaksınız", "acil", "hemen paylaş",
        "gizli gerçek", "yasaklandı", "ifşa", "bomba haber",
        "herkes bunu konuşuyor"
    ]

    for p in patterns:
        if p in text_lower:
            risk += 15

    # 🔗 kaynak kontrol
    if "http" not in text_lower:
        risk += 10

    # 🧠 HF zero-shot (daha doğru yaklaşım)
    try:
        res = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
            headers=headers_hf,
            json={
                "inputs": text,
                "parameters": {
                    "candidate_labels": ["gerçek haber", "yalan haber", "manipülasyon"]
                }
            },
            timeout=15
        )
        data = res.json()

        if "scores" in data:
            fake_score = int(data["scores"][1] * 100)
            risk += fake_score // 2

    except:
        pass

    risk = min(risk, 100)
    safe = 100 - risk

    return {"risk": risk, "safe": safe}

@app.route("/api/analyze", methods=["POST"])
def analyze_api():
    data = request.get_json()
    text = data.get("text", "")

    result = analyze_text(text)

    history.append({
        "text": text[:50],
        "risk": result["risk"]
    })

    return jsonify(result)

@app.route("/api/history")
def get_history():
    return jsonify(history[-10:][::-1])

# 📰 HABER (fallback)
@app.route("/api/news")
def news():
    try:
        if NEWS_API_KEY:
            url = f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={NEWS_API_KEY}"
            res = requests.get(url).json()

            articles = [
                {"title": a["title"], "url": a["url"]}
                for a in res.get("articles", [])
            ]

            if articles:
                return jsonify(articles)

    except:
        pass

    # fallback
    return jsonify([
        {"title": "Türkiye gündemi yoğun", "url": "#"},
        {"title": "Ekonomi gelişmeleri takip ediliyor", "url": "#"}
    ])

# 🐦 SOSYAL (fallback)
@app.route("/api/social")
def social():
    try:
        if X_BEARER:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {"Authorization": f"Bearer {X_BEARER}"}

            params = {
                "query": "gündem OR haber -is:retweet lang:tr",
                "max_results": 5
            }

            res = requests.get(url, headers=headers, params=params).json()

            tweets = [t["text"] for t in res.get("data", [])]

            if tweets:
                return jsonify(tweets)

    except:
        pass

    # fallback
    return jsonify([
        "Gündemde yeni gelişmeler var",
        "Sosyal medyada tartışmalar büyüyor"
    ])

# 📧 MAIL
def send_mail(content):
    try:
        recipients = [MY_EMAIL, FRIEND_EMAIL]

        msg = MIMEText(content)
        msg["Subject"] = "DEFANS SONUÇ"
        msg["From"] = MAIL_USER
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_USER, MAIL_PASS)
            server.sendmail(MAIL_USER, recipients, msg.as_string())

        return "Gönderildi"
    except Exception as e:
        return str(e)

@app.route("/api/notify", methods=["POST"])
def notify():
    data = request.get_json()
    text = data.get("text", "")

    result = analyze_text(text)

    content = f"""
RİSK: {result['risk']}
GÜVENLİ: {result['safe']}

{text}
"""
    status = send_mail(content)

    return jsonify({"status": status})

# RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)