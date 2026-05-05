import random

def get_social_posts():
    return [
        {"platform": "twitter", "text": "Şok karar açıklandı!", "risk": random.randint(50,90)},
        {"platform": "instagram", "text": "Gizli belge sızdırıldı", "risk": random.randint(60,100)},
        {"platform": "tiktok", "text": "Büyük ifşa videosu", "risk": random.randint(40,80)},
        {"platform": "facebook", "text": "Herkes bunu konuşuyor", "risk": random.randint(30,70)},
    ]