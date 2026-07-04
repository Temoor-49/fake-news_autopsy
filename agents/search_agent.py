# agents/search_agent.py
# Self-contained — all tools inlined to avoid import issues on Streamlit Cloud

import os
import sys
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ── Inline path fix ──────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# ── Inline config loader ─────────────────────────────────────
def get_secret(key: str) -> str:
    value = os.getenv(key, "")
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(key, "")
        if value:
            return value
    except Exception:
        pass
    return ""

# ── Initialize Gemini client ─────────────────────────────────
from google import genai
client = genai.Client(api_key=get_secret("GOOGLE_API_KEY"))

# ── Inline: Web Search Tool ──────────────────────────────────
def search_web(query: str, num_results: int = 5) -> list:
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": get_secret("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }
    payload = {"q": query, "num": num_results}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
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

# ── Inline: Article Fetcher ──────────────────────────────────
def fetch_article(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else ""
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        text = " ".join(text.split())[:5000]
        return {"url": url, "title": str(title).strip(), "text": text, "status": "success"}
    except Exception as e:
        return {"url": url, "title": "", "text": "", "status": f"error: {str(e)}"}

# ── Inline: News Search Tool ─────────────────────────────────
def simplify_query(claim: str, max_words: int = 5) -> str:
    stopwords = {"is","are","the","a","an","of","in","on","to","and","that","this"}
    words = claim.split()
    keywords = [w for w in words if w.lower().strip(".,?!") not in stopwords]
    return " ".join(keywords[:max_words])

def search_news(query: str) -> list:
    simplified = simplify_query(query)
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": simplified,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": 10,
        "apiKey": get_secret("NEWS_API_KEY")
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
        if not articles:
            shorter = simplify_query(query, max_words=2)
            if shorter != simplified:
                params["q"] = shorter
                response = requests.get(url, params=params)
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

# ── Main Agent Function ───────────────────────────────────────
def run_search_agent(claim: str) -> dict:
    """
    Search Agent — investigates a news claim by searching web + news,
    fetching article content, and using Gemini to analyze findings.
    """
    print(f"\n🔍 Search Agent investigating: {claim}")
    print("-" * 50)

    print("📡 Searching the web...")
    web_results = search_web(claim, num_results=5)

    print("📰 Searching news sources...")
    news_results = search_news(claim)

    print("📄 Fetching article content...")
    fetched_articles = []
    for result in web_results[:3]:
        article = fetch_article(result["link"])
        if article["status"] == "success" and article["text"]:
            fetched_articles.append(article)

    context = f"""
    CLAIM TO INVESTIGATE: {claim}

    WEB SEARCH RESULTS:
    {chr(10).join([f"- {r['title']}: {r['snippet']}" for r in web_results])}

    NEWS ARTICLES FOUND:
    {chr(10).join([f"- [{a['source']}] {a['title']} ({a['published_at']})" for a in news_results[:5]])}

    FULL ARTICLE CONTENT FETCHED:
    {chr(10).join([f"SOURCE: {a['url']}{chr(10)}CONTENT: {a['text'][:1000]}" for a in fetched_articles])}
    """

    print("🤖 Gemini analyzing findings...")
    prompt = f"""
    You are the Search Agent in a Fake News Investigation system.
    Analyze these search results and summarize key findings.

    {context}

    Provide a structured summary with:
    1. CLAIM SUMMARY: Restate the claim in one sentence
    2. KEY FINDINGS: What do results tell us? (3-5 bullet points)
    3. SOURCES FOUND: Most credible sources that appeared
    4. RED FLAGS: Any immediate signs of misinformation
    5. NEEDS FURTHER INVESTIGATION: Questions still to answer

    Be factual and concise.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "claim": claim,
        "web_results": web_results,
        "news_results": news_results[:5],
        "fetched_articles": fetched_articles,
        "gemini_analysis": response.text,
        "status": "complete"
    }


if __name__ == "__main__":
    result = run_search_agent("COVID-19 vaccines contain microchips")
    print(result["gemini_analysis"])