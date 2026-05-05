import re

def is_news_like(text):
    patterns = [
        r"https?://",  # URL
        r"\b(şok|ifşa|son dakika|gizli|iddia)\b",
        r"\b(video|görüntü|fotoğraf)\b",
        r"\b(açıklandı|duyuruldu|ortaya çıktı)\b"
    ]

    for p in patterns:
        if re.search(p, text.lower()):
            return True

    return False


def analyze_text(text):
    text = text.strip().lower()

    if len(text) < 15:
        return {"risk": 0, "safe": 0, "label": "Geçersiz"}

    # ❗ haber değilse analiz etme
    if not is_news_like(text):
        return {"risk": 0, "safe": 0, "label": "Haber değil"}

    risk_keywords = [
        "şok", "ifşa", "gizli", "skandal",
        "herkes bunu konuşuyor",
        "kanıtlandı", "büyük olay"
    ]

    risk = sum(1 for k in risk_keywords if k in text)

    if risk >= 2:
        return {"risk": 85, "safe": 15, "label": "Yalan olabilir"}
    elif risk == 1:
        return {"risk": 50, "safe": 50, "label": "Şüpheli"}
    else:
        return {"risk": 15, "safe": 85, "label": "Düşük risk"}