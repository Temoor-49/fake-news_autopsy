# tools/article_fetcher.py
# This tool fetches and extracts readable text from any news article URL

import requests
from bs4 import BeautifulSoup
import httpx


def fetch_article(url: str) -> dict:
    """
    Fetches a URL and extracts the main article text, title, and metadata.
    Returns a dict with title, text, url, and status.
    """

    headers = {
        # Pretend to be a browser so websites don't block us
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""

        # Extract main text — grab all paragraph tags
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])

        # Clean up whitespace
        text = " ".join(text.split())

        # Limit text length to avoid token overflow in Gemini
        text = text[:5000]

        return {
            "url": url,
            "title": title.strip(),
            "text": text,
            "status": "success"
        }

    except Exception as e:
        return {
            "url": url,
            "title": "",
            "text": "",
            "status": f"error: {str(e)}"
        }


# Quick test
if __name__ == "__main__":
    result = fetch_article("https://www.bbc.com/news")
    print(f"Title: {result['title']}")
    print(f"Status: {result['status']}")
    print(f"Text preview: {result['text'][:300]}")