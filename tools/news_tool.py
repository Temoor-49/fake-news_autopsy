# tools/news_tool.py
# Searches NewsAPI for recent articles about a claim or topic

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def search_news(query: str, days_back: int = 30) -> list[dict]:
    """
    Searches NewsAPI for articles related to the query.
    Returns list of articles with title, source, date, url, description.
    """

    # Calculate date range
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("name", ""),
                "published_at": article.get("publishedAt", ""),
                "url": article.get("url", ""),
                "description": article.get("description", "")
            })

        return articles

    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []


# Quick test
if __name__ == "__main__":
    articles = search_news("covid vaccine side effects")
    for a in articles:
        print(f"\nTitle: {a['title']}")
        print(f"Source: {a['source']}")
        print(f"Date: {a['published_at']}")