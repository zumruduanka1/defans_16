import requests

def get_social_data():
    posts = []

    try:
        r = requests.get(
            "https://www.reddit.com/r/news.json",
            headers={"User-Agent": "Mozilla/5.0"}
        )

        data = r.json()["data"]["children"]

        for item in data[:10]:
            posts.append({
                "platform": "Reddit",
                "text": item["data"]["title"],
                "url": "https://reddit.com" + item["data"]["permalink"]
            })

    except:
        # fallback
        posts = [
            {"platform": "X", "text": "Şok görüntüler ortaya çıktı", "url": "#"},
            {"platform": "TikTok", "text": "Gizli video sızdırıldı", "url": "#"}
        ]

    return posts