import os, requests
from dotenv import load_dotenv
load_dotenv()

HF_API = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
HF_KEY = os.getenv("HF_API_KEY")

def analyze(text):
    if not text or len(text.split()) < 5:
        return {"score":0,"status":"geçersiz"}

    try:
        headers = {"Authorization": f"Bearer {HF_KEY}"}
        payload = {
            "inputs": text,
            "parameters": {
                "candidate_labels": ["fake news","real news"]
            }
        }

        r = requests.post(HF_API, headers=headers, json=payload, timeout=8)
        data = r.json()

        label = data["labels"][0]
        score = int(data["scores"][0] * 100)

        if label == "fake news":
            return {"score": score, "status": "riskli"}
        else:
            return {"score": score, "status": "güvenli"}

    except:
        score = 0
        for k in ["şok","ifşa","gizli","son dakika"]:
            if k in text.lower():
                score += 25

        score = min(score,100)
        return {"score":score,"status":"riskli" if score>60 else "güvenli"}