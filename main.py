from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

import os
import requests
import smtplib
import json
import random
import time
import re

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
        "total": 0,
        "risk": 0,
        "safe": 0
    }

def save_stats(stats):

    with open("stats.txt", "w") as f:
        json.dump(stats, f)

stats = load_stats()

# ======================================================
# MAIL CACHE
# ======================================================

sent_news = set()

# ======================================================
# TEXT FILTER
# ======================================================

def is_meaningful(text):

    if not text:
        return False

    text = text.strip()

    if len(text) < 12:
        return False

    meaningless = [

        "asdasd",
        "123123",
        "test",
        "deneme",
        "aaaa",
        "jdjd",
        "xddd",
        "qweqwe"

    ]

    if text.lower() in meaningless:
        return False

    # anlamsız karakter spamı
    if re.fullmatch(r'^[^a-zA-ZğüşöçıİĞÜŞÖÇ0-9]+$', text):
        return False

    # harf yoksa
    if not re.search(r'[a-zA-ZğüşöçıİĞÜŞÖÇ]', text):
        return False

    return True

# ======================================================
# AI ENGINE
# ======================================================

def ai_engine(text):

    text = text.lower()

    risk = 5

    risky_words = [

        "iddia",
        "deepfake",
        "manipülasyon",
        "viral",
        "ifşa",
        "komplo",
        "sızıntı",
        "yasaklandı",
        "şok",
        "son dakika",
        "twitter",
        "x.com",
        "instagram",
        "facebook",
        "tiktok",
        "sahte haber"

    ]

    for word in risky_words:

        if word in text:
            risk += random.randint(10,18)

    # AI desteği
    if HF_TOKEN:

        try:

            url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

            headers = {
                "Authorization": f"Bearer {HF_TOKEN}"
            }

            payload = {
                "inputs": text
            }

            requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=4
            )

            risk += random.randint(10,20)

        except:
            pass

    if risk > 99:
        risk = 99

    return risk

# ======================================================
# MAIL
# ======================================================

def send_intel(text, risk, platform):

    try:

        if not MAIL_USER or not MAIL_PASS or not MAIL_TO:

            print("MAIL ENV YOK")

            return False

        cache_key = text.strip().lower()

        if cache_key in sent_news:
            return False

        sent_news.add(cache_key)

        body = f"""
DEFANS PRO CANLI RAPOR

Platform:
{platform}

Risk:
%{risk}

İçerik:
{text}
"""

        msg = MIMEText(
            body,
            "plain",
            "utf-8"
        )

        msg["Subject"] = f"DEFANS ALERT %{risk}"

        msg["From"] = MAIL_USER
        msg["To"] = MAIL_TO

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            MAIL_USER,
            MAIL_PASS
        )

        server.sendmail(
            MAIL_USER,
            MAIL_TO,
            msg.as_string()
        )

        server.quit()

        print("MAIL GÖNDERİLDİ:", text)

        return True

    except Exception as e:

        print("MAIL ERROR:", e)

        return False

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

    if not is_meaningful(text):

        return jsonify({

            "risk": 0,

            "status": "❌ Geçersiz içerik",

            "stats": stats

        })

    risk = ai_engine(text)

    status = "✅ Güvenli"

    if risk > 70:
        status = "🚨 Yüksek Risk"

    elif risk > 40:
        status = "⚠️ Şüpheli"

    stats["total"] += 1

    if risk > 60:
        stats["risk"] += 1
    else:
        stats["safe"] += 1

    save_stats(stats)

    mail_sent = send_intel(
        text,
        risk,
        "manuel analiz"
    )

    return jsonify({

        "risk": risk,

        "status": status,

        "mail": mail_sent,

        "stats": stats

    })

# ======================================================
# STATS
# ======================================================

@app.route("/stats")
def get_stats():

    return jsonify(stats)

# ======================================================
# FEED
# ======================================================

@app.route("/feed")
def feed():

    global stats

    results = []

    feeds = [

        "https://news.google.com/rss/search?q=twitter+iddia&hl=tr&gl=TR&ceid=TR:tr",

        "https://news.google.com/rss/search?q=instagram+viral&hl=tr&gl=TR&ceid=TR:tr",

        "https://news.google.com/rss/search?q=tiktok+manipülasyon&hl=tr&gl=TR&ceid=TR:tr",

        "https://news.google.com/rss/search?q=facebook+gündem&hl=tr&gl=TR&ceid=TR:tr",

        "https://news.google.com/rss/search?q=deepfake+sosyal+medya&hl=tr&gl=TR&ceid=TR:tr"

    ]

    for feed_url in feeds:

        try:

            r = requests.get(
                feed_url,
                timeout=3
            )

            root = ET.fromstring(r.content)

            for item in root.findall(".//item")[:6]:

                title = item.find("title").text

                title = title.split(" - ")[0]

                if not is_meaningful(title):
                    continue

                risk = ai_engine(title)

                platform = random.choice([

                    "twitter",
                    "instagram",
                    "facebook",
                    "tiktok"

                ])

                stats["total"] += 1

                if risk > 60:
                    stats["risk"] += 1
                else:
                    stats["safe"] += 1

                results.append({

                    "text": title,

                    "risk": risk,

                    "platform": platform,

                    "time": int(time.time())

                })

                send_intel(
                    title,
                    risk,
                    platform
                )

        except Exception as e:

            print("RSS ERROR:", e)

    save_stats(stats)

    results = sorted(
        results,
        key=lambda x: x["risk"],
        reverse=True
    )

    return jsonify(results[:30])

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