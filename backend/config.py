import os
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "medialens"

OUTLETS = {
    "cnn": "cnn",
    "fox-news": "fox-news",
    "reuters": "reuters",
    "associated-press": "associated-press",
    "bbc-news": "bbc-news",
    "npr": "npr",
    "the-wall-street-journal": "the-wall-street-journal",
    "politico": "politico",
    "the-guardian": "the-guardian-us",
    "abc-news": "abc-news",
}

OUTLET_RSS = {
    "cnn": "http://rss.cnn.com/rss/edition.rss",
    "fox-news": "https://feeds.foxnews.com/foxnews/latest",
    "reuters": "https://feeds.reuters.com/reuters/topNews",
    "associated-press": "https://apnews.com/apf-topnews.rss",
    "bbc-news": "https://feeds.bbci.co.uk/news/rss.xml",
    "npr": "https://feeds.npr.org/1001/rss.xml",
    "the-wall-street-journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "politico": "https://rss.politico.com/politics-news.xml",
    "the-guardian": "https://www.theguardian.com/world/rss",
    "abc-news": "https://abcnews.go.com/abcnews/topstories",
}

PIPELINE_INTERVAL_HOURS = 4
HIGH_DIVERGENCE_THRESHOLD = 5.0
MIN_OUTLETS_FOR_SCORING = 3
