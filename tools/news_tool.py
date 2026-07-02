# tools/news_tool.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def simplify_query(claim: str, max_words: int = 5) -> str:
    """
    Long sentence-style claims often return 0 results on NewsAPI
    because it does literal phrase matching. This trims the claim
    down to its most important keywords for a better match.
    """
    # Remove common filler words that don't help search matching
    stopwords = {"is", "are", "the", "a", "an", "of", "in", "on", "to", "and", "that", "this"}

    words = claim.split()
    keywords = [w for w in words if w.lower().strip(".,?!") not in stopwords]

    return " ".join(keywords[:max_words])


def search_news(query: str) -> list[dict]:
    """
    Searches NewsAPI for articles related to the query.
    Automatically simplifies long claim-style queries for better matching.
    """

    simplified = simplify_query(query)

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": simplified,
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

        # Fallback: if simplified query still returns nothing,
        # try an even shorter 2-word version as a last resort
        if not articles:
            shorter = simplify_query(query, max_words=2)
            if shorter != simplified:
                params["q"] = shorter
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
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


if __name__ == "__main__":
    test_claim = "COVID-19 vaccines contain microchips"
    print(f"Simplified query: '{simplify_query(test_claim)}'\n")

    articles = search_news(test_claim)
    print(f"Found {len(articles)} articles\n")
    for a in articles:
        print(f"Title: {a['title']}")
        print(f"Source: {a['source']}")
        print(f"Date: {a['published_at']}\n")