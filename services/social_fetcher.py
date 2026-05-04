import random

def get_social_data():
    base = [
        {"platform": "X", "text": "Büyük patlama oldu şehirde"},
        {"platform": "Instagram", "text": "Yeni yasa çıktı herkes konuşuyor"},
        {"platform": "TikTok", "text": "Şok gelişme az önce açıklandı"},
        {"platform": "X", "text": "Deprem oldu hissedildi"},
    ]

    # her çağrıda veri değişsin
    for item in base:
        item["text"] += " " + str(random.randint(1, 1000))

    return base