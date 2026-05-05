import re
import requests

cache = {}

def basic_score(text):
    score = 0

    fake_patterns = [
        r"şok", r"inanılmaz", r"son dakika", r"hemen izle",
        r"gizli", r"büyük oyun", r"paylaş", r"silinmeden"
    ]

    for p in fake_patterns:
        if re.search(p, text.lower()):
            score += 10

    if len(text) < 25:
        score += 10

    if text.count("!") > 2:
        score += 10

    return score


def check_url(url):
    if not url:
        return 0
    
    if not url.startswith("https"):
        return 20
    
    if any(x in url for x in ["bit.ly", "t.co"]):
        return 15

    return 0


def ai_analysis(text):
    # cache (RAM korur)
    if text in cache:
        return cache[text]

    try:
        # ÜCRETSİZ / düşük RAM çözüm
        res = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
            headers={"Authorization": "Bearer " + "YOUR_HF_TOKEN"},
            json={
                "inputs": text,
                "parameters": {
                    "candidate_labels": ["fake news", "real news"]
                }
            },
            timeout=5
        )

        data = res.json()

        if "scores" in data:
            fake_score = data["scores"][0] * 100
        else:
            fake_score = 0

    except:
        fake_score = 0

    cache[text] = fake_score
    return fake_score


def analyze_all(text, url=None, media=False):
    score = 0

    score += basic_score(text)
    score += check_url(url)

    if media:
        score += 10

    ai_score = ai_analysis(text)

    total = score + (ai_score * 0.5)

    if total > 60:
        result = "Riskli"
    elif total > 30:
        result = "Şüpheli"
    else:
        result = "Güvenilir"

    return {
        "total_score": total,
        "ai_score": ai_score,
        "rule_score": score,
        "result": result
    }