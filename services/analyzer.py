def analyze_content(text=None, url=None, image=None):
    if not text or len(text.split()) < 5:
        return {"risk": 0, "status": "geçersiz"}

    risk = 0
    reasons = []

    keywords = [
        "şok", "ifşa", "gizli", "sızdırıldı",
        "büyük olay", "son dakika", "yasaklandı"
    ]

    for k in keywords:
        if k in text.lower():
            risk += 20
            reasons.append(k)

    if "http" in text:
        risk += 10

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