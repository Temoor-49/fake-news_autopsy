# tools/article_fetcher.py
# Fetches and extracts readable text from any news article URL
# Uses requests + BeautifulSoup only — no lxml compilation needed

import requests
from bs4 import BeautifulSoup


def fetch_article(url: str) -> dict:
    """
    Fetches a URL and extracts the main article text, title, and metadata.
    Returns a dict with title, text, url, and status.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""

        # Extract main text from paragraphs
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        text = " ".join(text.split())
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