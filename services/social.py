import os, requests
from dotenv import load_dotenv
load_dotenv()

def twitter():
    bearer = os.getenv("TWITTER_BEARER")
    if not bearer:
        return []

    try:
        headers = {"Authorization": f"Bearer {bearer}"}
        url = "https://api.twitter.com/2/tweets/search/recent?query=haber&max_results=10"
        r = requests.get(url, headers=headers).json()

        return [{"text":t["text"],"platform":"twitter"} for t in r.get("data",[])]
    except:
        return []

def reddit():
    try:
        r = requests.get(
            "https://www.reddit.com/r/news/top.json?limit=5",
            headers={"User-Agent":"defans"}
        ).json()

        return [{"text":p["data"]["title"],"platform":"reddit"} for p in r["data"]["children"]]
    except:
        return []

def get_all():
    return twitter() + reddit()