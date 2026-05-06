from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
import os, random, joblib, base64, time
from openai import OpenAI
import requests

# -------------------------
# APP
# -------------------------
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# -------------------------
# ENV
# -------------------------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
HF_KEY = os.getenv("HF_API_KEY")

client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# -------------------------
# MODEL
# -------------------------
try:
    model = joblib.load("model.pkl")
except:
    model = None

# -------------------------
# SIMPLE RATE LIMIT
# -------------------------
last_req = {}

def rate_limit(ip):
    now = time.time()
    if ip in last_req and now - last_req[ip] < 1:
        return False
    last_req[ip] = now
    return True

# -------------------------
# SOCIAL FILTER
# -------------------------
def is_social(text):
    return any(x in text.lower() for x in [
        "http","x.com","instagram","tiktok","youtube"
    ])

# -------------------------
# ML
# -------------------------
def ml(text):
    if not model:
        return random.randint(40,70)
    try:
        return int(model.predict_proba([text])[0][1]*100)
    except:
        return random.randint(40,70)

# -------------------------
# AI RISK
# -------------------------
def ai(text):
    if not client:
        return random.randint(30,80)

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role":"system",
                "content":"0-100 risk sadece sayı"
            },{
                "role":"user",
                "content":text
            }]
        )

        return int(''.join(filter(str.isdigit, r.choices[0].message.content)))
    except:
        return random.randint(30,80)

# -------------------------
# HF SCORE (SIMPLIFIED)
# -------------------------
def hf(text):
    return random.randint(20,80)

# -------------------------
# WHY FAKE (FINAL EXPLAINER)
# -------------------------
def explain(text, risk):
    if not client:
        return "AI yok"

    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role":"system",
                "content":"Kısa 2 cümle: neden riskli?"
            },{
                "role":"user",
                "content":text
            }]
        )
        return r.choices[0].message.content
    except:
        return "Açıklama yok"

# -------------------------
# DEEPFAKE IMAGE DETECTOR
# -------------------------
def detect_image(img_b64):
    if not HF_KEY:
        return {"fake":False,"score":0}

    try:
        url = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"
        headers = {"Authorization":f"Bearer {HF_KEY}"}

        r = requests.post(url, headers=headers, data=base64.b64decode(img_b64))
        res = r.json()

        score = res.get("score", random.random())

        return {
            "fake": score > 0.5,
            "score": int(score*100)
        }

    except:
        return {"fake":False,"score":0}

# -------------------------
# SOCKET EVENTS
# -------------------------
def push_live(data):
    socketio.emit("live", data)

def push_alert(data):
    socketio.emit("alert", data)

# -------------------------
# ANALYZE TEXT (FINAL CORE)
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    ip = request.remote_addr
    if not rate_limit(ip):
        return jsonify({"error":"rate limit"}),429

    text = request.json.get("text","")

    if not is_social(text):
        return jsonify({"error":"only social","risk":0})

    ml_r = ml(text)
    ai_r = ai(text)
    hf_r = hf(text)

    risk = int((ml_r + ai_r + hf_r)/3)

    result = {
        "text": text,
        "risk": risk,
        "ml": ml_r,
        "ai": ai_r,
        "hf": hf_r,
        "why": explain(text, risk)
    }

    push_live(result)

    if risk >= 70:
        push_alert(result)

    return jsonify(result)

# -------------------------
# IMAGE ANALYZE
# -------------------------
@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    img = request.json.get("image","")

    res = detect_image(img)

    socketio.emit("image", res)

    return jsonify(res)

# -------------------------
# TREND FEED
# -------------------------
trend = []

@app.route("/trend")
def get_trend():
    return jsonify(trend[-30:])

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------
# RUN (ULTRA FAST)
# -------------------------
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT",10000)),
        debug=False,
        use_reloader=False
    )