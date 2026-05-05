import requests
import os

def get_news():
    key = os.getenv("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/top-headlines?country=tr&apiKey={key}"

    try:
        res = requests.get(url).json()
        return res.get("articles", [])[:5]
    except:
        return []