def bot_score(text):
    spam=["urgent","shocking","!!!","leak"]
    return min(sum(1 for w in spam if w in text.lower())/4,1)