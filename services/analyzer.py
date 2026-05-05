import re

def valid_text(text):
    if not text:
        return False
    words = text.split()
    return len(words) > 5

def analyze_content(text=None, url=None, image=None):
    risk = 0
    reasons = []

    if text:
        if not valid_text(text):
            return {"risk": 0, "status": "geçersiz"}

        keywords = ["şok", "ifşa", "gizli", "sızdırıldı"]
        for k in keywords:
            if k in text.lower():
                risk += 25
                reasons.append(k)

    if url:
        risk += 15
        reasons.append("url içerik")

    if image:
        risk += 20
        reasons.append("görsel içerik")

    risk = min(risk, 100)

    status = "güvenli"
    if risk > 70:
        status = "tehlikeli"
    elif risk > 40:
        status = "şüpheli"

    return {
        "risk": risk,
        "status": status,
        "reasons": reasons
    }