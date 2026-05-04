def get_twitter(query=None):
    return [
        {
            "text": f"{query} hakkında tweet",
            "source": "twitter",
            "url": "https://twitter.com/search"
        }
    ]