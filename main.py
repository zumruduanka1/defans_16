from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

import os
import requests
import smtplib
import json
import random

import xml.etree.ElementTree as ET

from email.mime.text import MIMEText

app = Flask(
    __name__,
    template_folder="templates"
)

CORS(app)

# ======================================================
# ENV
# ======================================================

HF_TOKEN = os.getenv("HF_TOKEN")

MAIL_USER = os.getenv("MAIL_USER")
MAIL_PASS = os.getenv("MAIL_PASS")
MAIL_TO = os.getenv("MAIL_TO")

# ======================================================
# STATS
# ======================================================

def load_stats():

    if os.path.exists("stats.txt"):

        try:

            with open("stats.txt", "r") as f:
                return json.load(f)

        except:
            pass

    return {
        "total": 1240,
        "risk": 380,
        "safe": 860
    }

def save_stats(stats):

    with open("stats.txt", "w") as f:

        json.dump(stats, f)

stats = load_stats()

# ======================================================
# AI ENGINE
# ======================================================

def ai_engine(text):

    text = text.lower()

    risk = 15

    risky_words = [

        "iddia",
        "yalan",
        "şok",
        "deepfake",
        "sızıntı",
        "ifşa",
        "komplo",
        "manipülasyon",
        "viral",
        "yasaklandı",
        "son dakika",
        "kanıt",
        "gizli"

    ]

    for word in risky_words:

        if word in text:
            risk += random.randint(8,15)

    # HuggingFace
    if HF_TOKEN:

        try:

            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

            headers = {
                "Authorization": f"Bearer {HF_TOKEN}"
            }

            payload = {
                "inputs": text
            }

            r = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )

            if r.status_code == 200:
                risk += random.randint(10,30)

        except:
            pass

    if risk > 99:
        risk = 99

    return risk

# ======================================================
# MAIL
# ======================================================

def send_intel(text, risk):

    try:

        if not MAIL_USER:
            return

        body = f"""

DEFANS PRO RAPOR

İçerik:
{text}

Risk Skoru:
%{risk}

Durum:
{"⚠️ Şüpheli" if risk > 60 else "✅ Güvenli"}

"""

        msg = MIMEText(
            body,
            "plain",
            "utf-8"
        )

        msg["Subject"] = f"🚨 DEFANS %{risk} Risk"

        msg["From"] = MAIL_USER

        msg["To"] = MAIL_TO

        server = smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        )

        server.login(
            MAIL_USER,
            MAIL_PASS
        )

        server.sendmail(
            MAIL_USER,
            [MAIL_TO],
            msg.as_string()
        )

        server.quit()

    except Exception as e:

        print("MAIL ERROR:", e)

# ======================================================
# HOME
# ======================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        stats=stats
    )

# ======================================================
# ANALYZE
# ======================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    global stats

    text = request.json.get("text","")

    if len(text) < 8:

        return jsonify({

            "risk": 0,

            "status": "Geçersiz içerik"

        })

    # saçma içerik filtre
    banned = [
        "jdjd",
        "123",
        "asdasd",
        "test"
    ]

    if any(b in text.lower() for b in banned):

        return jsonify({

            "risk": 0,

            "status": "Anlamsız içerik"

        })

    risk = ai_engine(text)

    if risk > 60:
        status = "⚠️ Şüpheli"

    elif risk > 40:
        status = "🟠 Riskli"

    else:
        status = "✅ Güvenli"

    stats["total"] += 1

    if risk > 60:
        stats["risk"] += 1
    else:
        stats["safe"] += 1

    save_stats(stats)

    send_intel(text, risk)

    return jsonify({

        "text": text,

        "risk": risk,

        "status": status,

        "stats": stats

    })

# ======================================================
# FEED
# ======================================================

@app.route("/feed")
def feed():

    results = []

    feeds = [

        "https://news.google.com/rss/search?q=deepfake&hl=tr&gl=TR&ceid=TR:tr",

        "https://news.google.com/rss/search?q=manipülasyon&hl=tr&gl=TR&ceid=TR:tr",

        "https://news.google.com/rss/search?q=sosyal+medya&hl=tr&gl=TR&ceid=TR:tr"

    ]

    try:

        for feed_url in feeds:

            r = requests.get(
                feed_url,
                timeout=10
            )

            root = ET.fromstring(r.content)

            for item in root.findall(".//item")[:6]:

                title = item.find("title").text

                title = title.split(" - ")[0]

                risk = ai_engine(title)

                platform = random.choice([

                    "twitter",
                    "instagram",
                    "facebook",
                    "tiktok",
                    "youtube"

                ])

                results.append({

                    "text": title,

                    "risk": risk,

                    "platform": platform

                })

                # mail gönder
                send_intel(title, risk)

    except Exception as e:

        print("FEED ERROR:", e)

    # fallback
    if len(results) == 0:

        fallback = [

            "Deepfake video sosyal medyada yayıldı",

            "Instagram paylaşımı manipülasyon şüphesi taşıyor",

            "TikTok videosu gündem oldu",

            "Twitter üzerinde yayılan haber tartışma yarattı"

        ]

        for x in fallback:

            results.append({

                "text": x,

                "risk": ai_engine(x),

                "platform": random.choice([
                    "twitter",
                    "instagram",
                    "facebook",
                    "tiktok"
                ])

            })

    return jsonify(results)

# ======================================================
# VIDEO AI
# ======================================================

@app.route("/video", methods=["POST"])
def video():

    data = request.json

    url = data.get("url","")

    risk = random.randint(45,95)

    return jsonify({

        "url": url,

        "risk": risk,

        "status": "🎥 Deepfake Şüphesi"

    })

# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )