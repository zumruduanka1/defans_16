from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, os, smtplib
from email.mime.text import MIMEText

app = Flask(__name__, static_folder="static")
CORS(app)

# 🔐 ENV
HF_TOKEN = os.getenv("HF_TOKEN")
X_BEARER = os.getenv("X_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MY_EMAIL = os.getenv("MY_EMAIL")
FRIEND_EMAIL = os.getenv("FRIEND_EMAIL")

# 🧠 HuggingFace (hafif kullanım)
HF_API_URL = "https://api-inference.huggingface.co/models/savasy/bert-base-turkish-sentiment-cased"

headers_hf = {
    "Authorization": f"Bearer {HF_TOKEN}"
} if HF_TOKEN else {}

# 🌐 FRONTEND
@app.route("/")
def home():
    return send_from_directory("static", "index.html")

# 🧠 ANALİZ (SADECE API → RAM YEMEZ)
def analyze_text(text):
    try:
        res = requests.post(
            HF_API_URL,
            headers=headers_hf,
            json={"inputs": text},
            timeout=15
        )

        data = res.json()

        if isinstance(data, list):
            result = data[0][0]
            score = int(result["score"] * 100)

            if result["label"] == "NEGATIVE":
                return {"risk": score, "safe": 100 - score}
            else:
                return {"risk": 100 - score, "safe": score}

    except Exception as e:
        print("HF ERROR:", e)

    return {"risk": 50, "safe": 50}

@app.route("/api/analyze", methods=["POST"])
def analyze_api():
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "Boş metin"}), 400

    return jsonify(analyze_text(text))

# 📰 HABER
@app.route("/api/news")
def news():
    try:
        if not NEWS_API_KEY:
            return jsonify([])

        url = f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()

        return jsonify([
            {"title": a["title"], "url": a["url"]}
            for a in res.get("articles", [])
        ])
    except:
        return jsonify([])

# 🐦 SOSYAL MEDYA (X)
@app.route("/api/social")
def social():
    try:
        if not X_BEARER:
            return jsonify([])

        url = "https://api.twitter.com/2/tweets/search/recent"

        headers = {
            "Authorization": f"Bearer {X_BEARER}"
        }

        params = {
            "query": "haber OR gündem -is:retweet lang:tr",
            "max_results": 10,
            "tweet.fields": "created_at,text"
        }

        res = requests.get(url, headers=headers, params=params).json()

        return jsonify([
            {"text": t["text"], "time": t["created_at"]}
            for t in res.get("data", [])
        ])
    except:
        return jsonify([])

# 📧 2 MAİLE GÖNDER
def send_mail_multi(subject, content):
    try:
        recipients = [e for e in [MY_EMAIL, FRIEND_EMAIL] if e]

        if not recipients:
            return "Mail yok"

        msg = MIMEText(content)
        msg["Subject"] = subject
        msg["From"] = MAIL_USER
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_USER, MAIL_PASS)
            server.sendmail(MAIL_USER, recipients, msg.as_string())

        return "Mail gönderildi"

    except Exception as e:
        return str(e)

@app.route("/api/notify", methods=["POST"])
def notify():
    data = request.get_json()
    text = data.get("text", "")

    result = analyze_text(text)

    content = f"""
DEFANS SONUÇ

Risk: {result['risk']}
Güvenli: {result['safe']}

Metin:
{text}
"""

    status = send_mail_multi("DEFANS RAPOR", content)

    return jsonify({"status": status, "result": result})

# 🚀 RUN (Render uyumlu)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)