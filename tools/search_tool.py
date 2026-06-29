# tools/search_tool.py
# This tool lets our agent search the web using Serper API

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


def search_web(query: str, num_results: int = 5) -> list[dict]:
    """
    Searches the web for a given query using Serper API.
    Returns a list of results with title, link, and snippet.
    """

    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "q": query,
        "num": num_results
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract the organic search results
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })

        return results

    except Exception as e:
        print(f"Search error: {e}")
        return []


# Quick test — run this file directly to test
if __name__ == "__main__":
    results = search_web("is climate change caused by humans")
    for r in results:
        print(f"\nTitle: {r['title']}")
        print(f"Link: {r['link']}")
        print(f"Snippet: {r['snippet']}")