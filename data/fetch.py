from data.sources import reddit, hackernews, rss
from social.twitter import get_twitter

def fetch_all(query):
    twitter_data = get_twitter(query)
    return twitter_data