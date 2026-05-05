from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, os, re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

HF_TOKEN = os.getenv("HF_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

history = []

# -------------------------
# 🧠 VALIDATION
# -------------------------
def is_valid(text):
    if len(text) < 15:
        return False
    if re.fullmatch(r"[a-zA-Z\s]+", text) and len(text.split()) < 3:
        return False
    return True

# -------------------------
# 🌐 URL CONTENT
# -------------------------
def fetch_url(url):
    try:
        html = requests.get(url, timeout=5).text
        clean = re.sub("<.*?>", "", html)
        return clean[:1000]
    except:
        return None

# -------------------------
# 🧠 ANALYZE
# -------------------------
def analyze(text):

    if not is_valid(text):
        return {"error":"Geçersiz içerik"}

    risk = 0
    t = text.lower()

    # 🚨 clickbait
    patterns = ["şok","acil","hemen paylaş","ifşa","bomba"]
    for p in patterns:
        if p in t:
            risk += 20

    # 🔗 kaynak yoksa
    if "http" not in t:
        risk += 10

    # 🧠 AI
    try:
        res = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
            headers=headers,
            json={
                "inputs": text,
                "parameters":{
                    "candidate_labels":["gerçek","yalan","manipülasyon"]
                }
            },
            timeout=10
        )
        data = res.json()

        if "scores" in data:
            risk += int(data["scores"][1]*50)

    except:
        pass

    risk = min(risk,100)
    return {"risk":risk,"safe":100-risk}

# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def home():
    return send_from_directory("static","index.html")

@app.route("/api/analyze",methods=["POST"])
def api_analyze():
    text = request.json.get("text","")

    if text.startswith("http"):
        content = fetch_url(text)
        if not content:
            return jsonify({"error":"URL okunamadı"})
        result = analyze(content)
        result["type"]="url"
    else:
        result = analyze(text)
        result["type"]="text"

    history.append({
        "text":text[:40],
        "risk":result.get("risk",0)
    })

    return jsonify(result)

@app.route("/api/history")
def api_history():
    return jsonify(history[-10:][::-1])

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)