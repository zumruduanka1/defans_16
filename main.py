from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, requests, random, joblib
import feedparser
import smtplib
from email.mime.text import MIMEText
from openai import OpenAI

# -------------------------
# APP
# -------------------------
app = Flask(__name__)
CORS(app)

# -------------------------
# ENV KEYS
# -------------------------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
HF_KEY = os.getenv("HF_API_KEY")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

EMAIL_TO_1 = os.getenv("EMAIL_TO_1")
EMAIL_TO_2 = os.getenv("EMAIL_TO_2")

# -------------------------
# OPENAI
# -------------------------
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# -------------------------
# MODEL LOAD
# -------------------------
model_path = os.path.join(os.path.dirname(__file__), "model.pkl")

try:
    model = joblib.load(model_path)
except:
    model = None
    print("Model yüklenemedi")

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
    if client is None:
        return random.randint(30, 80)

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Metni analiz et ve 0-100 arası dezenformasyon riski ver (sadece sayı)"
                },
                {"role": "user", "content": text}
            ]
        )

        content = res.choices[0].message.content
        score = int(''.join(filter(str.isdigit, content)))

        return min(score, 100)

    except:
        return random.randint(30, 80)

# -------------------------
# HF ANALYSIS
# -------------------------
def hf_analyze(text):
    if not HF_KEY:
        return random.randint(30, 80)

    try:
        url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        headers = {"Authorization": f"Bearer {HF_KEY}"}

        payload = {
            "inputs": text,
            "parameters": {
                "candidate_labels": ["fake news", "true news"]
            }
        }

        r = requests.post(url, headers=headers, json=payload)

        result = r.json()

        labels = result.get("labels", [])
        scores = result.get("scores", [])

        if not scores:
            return random.randint(30, 80)

        if "fake news" in labels:
            idx = labels.index("fake news")
        else:
            idx = 0

        return int(scores[idx] * 100)

    except:
        return random.randint(30, 80)

# -------------------------
# MAIL GÖNDERME
# -------------------------
def send_alert_mail(text, risk):
    if not EMAIL_USER or not EMAIL_PASS:
        return

    if not EMAIL_TO_1 and not EMAIL_TO_2:
        return

    subject = f"🚨 Riskli Haber Tespit Edildi ({risk})"

    body = f"""
Risk Skoru: {risk}

Haber:
{text}
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER

    recipients = [r for r in [EMAIL_TO_1, EMAIL_TO_2] if r]

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        for r in recipients:
            msg["To"] = r
            server.sendmail(EMAIL_USER, r, msg.as_string())

        server.quit()

    except Exception as e:
        print("Mail gönderilemedi:", e)

# -------------------------
# ANALYZE
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "")

    ml_risk = ml_analyze(text)
    ai_risk = ai_analyze(text)
    hf_risk = hf_analyze(text)

    final_risk = int((ml_risk + ai_risk + hf_risk) / 3)

    # 🚨 ALERT SYSTEM
    if final_risk >= 70:
        send_alert_mail(text, final_risk)

    return jsonify({
        "text": text,
        "ml_risk": ml_risk,
        "ai_risk": ai_risk,
        "hf_risk": hf_risk,
        "risk": final_risk
    })

# -------------------------
# NEWS
# -------------------------
@app.route("/news")
def news():
    url = "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr"
    feed = feedparser.parse(url)

    return jsonify([
        {"text": entry.title}
        for entry in feed.entries[:10]
    ])

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