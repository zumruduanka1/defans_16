def enrich(item):
    keywords = ["breaking", "urgent", "leak", "confirmed"]
    score = sum(1 for k in keywords if k in item["text"])
    item["signal"] = score / len(keywords)
    return item