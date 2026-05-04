from transformers import pipeline
import random

print("MODEL LOADING...")

clf = pipeline(
    "text-classification",
    model="distilbert-base-uncased",
    return_all_scores=True
)

print("MODEL LOADED")

def analyze_text(text: str):
    if not text or not text.strip():
        return {"risk": 0, "safe": 0}

    result = clf(text)[0]

    score = sum(r["score"] for r in result) / len(result)
    risk = int(score * 100) + random.randint(-10, 10)
    risk = max(0, min(100, risk))
    safe = 100 - risk

    return {"risk": risk, "safe": safe}