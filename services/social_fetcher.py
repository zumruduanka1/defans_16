import random

def get_twitter_data():
    return [
        {"text": "Şok karar açıklandı!", "risk": random.randint(40,90)},
        {"text": "Gizli belge sızdırıldı", "risk": random.randint(50,100)}
    ]