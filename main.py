import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
import os, time, random
from openai import OpenAI

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

logs = []
last = {}

def rate(ip):
    now = time.time()
    if ip in last and now - last[ip] < 0.7:
        return False
    last[ip] = now
    return True

def is_social(t):
    if not t:
        return False

    t = t.lower()

    allowed = [
        "http",
        "x.com",
        "instagram",
        "tiktok",
        "youtube",
        "facebook",
        "haber",
        "news"
    ]

    return any(x in t for x in allowed)

def ai_score(text):
    if not client:
        return random.randint(35,70)
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"0-100 risk sayısı ver"},
                {"role":"user","content":text[:400]}
            ]
        )
        return int(''.join(filter(str.isdigit, r.choices[0].message.content)))
    except:
        return random.randint(35,70)

def explain(text):
    if not client:
        return "AI offline"
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"2 cümle neden riskli açıklama"},
                {"role":"user","content":text[:300]}
            ]
        )
        return r.choices[0].message.content
    except:
        return "Açıklama yok"

fetch("/analyze", {
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify({text:"test"})
}).then(r=>r.json()).then(console.log)

    text = request.json.get("text","")

    if not is_social(text):
        return jsonify({"risk":0})

    risk = ai_score(text)

    result = {
        "text": text,
        "risk": risk,
        "why": explain(text)
    }

    logs.append(result)
    if len(logs) > 50:
        logs.pop(0)

    socketio.emit("live", result)

    if risk >= 70:
        socketio.emit("alert", result)

    return jsonify(result)

@app.route("/trend")
def trend():
    return jsonify(logs)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT",10000))
    )