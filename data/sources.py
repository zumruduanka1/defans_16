import requests, feedparser

def reddit():
    try:
        r = requests.get("https://www.reddit.com/r/news/new.json",
                         headers={"User-Agent":"defans"}).json()
        return [{"text":p["data"]["title"],"score":p["data"]["score"],"source":"reddit"} 
                for p in r["data"]["children"][:10]]
    except:
        return []

def hackernews():
    try:
        ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:10]
        posts=[]
        for i in ids:
            d=requests.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json").json()
            if "title" in d:
                posts.append({"text":d["title"],"score":d["score"],"source":"hn"})
        return posts
    except:
        return []

def rss():
    feeds=["http://feeds.bbci.co.uk/news/rss.xml"]
    posts=[]
    for f in feeds:
        feed=feedparser.parse(f)
        for e in feed.entries[:5]:
            posts.append({"text":e.title,"score":50,"source":"rss"})
    return posts