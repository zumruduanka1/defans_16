import re
from data.fetch import fetch_all

def get_ai_ready_data(query):
    data = fetch_all(query)

    # basit analiz
    return {
        "query": query,
        "count": len(data),
        "data": data
    }

def is_valid(text):
    if len(text) < 20:
        return False
    if len(set(text)) < 6:
        return False
    if not re.search("[a-zA-Z]", text):
        return False
    return True

def get_ai_ready_data():
    raw = fetch_all()
    processed = []

    for item in raw:
        text = clean_text(item["text"])

        if not is_valid(text):
            continue

        processed.append({
            "text": text,
            "score": item["score"],
            "source": item["source"]
        })

    return processed