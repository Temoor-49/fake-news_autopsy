# agents/search_agent.py
# Search Agent — investigates a news claim by searching the web

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai
from tools.search_tool import search_web
from tools.article_fetcher import fetch_article
from tools.news_tool import search_news

load_dotenv()

# Initialize new google.genai client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def run_search_agent(claim: str) -> dict:
    """
    Search Agent — investigates a news claim by:
    1. Searching the web for related articles
    2. Searching NewsAPI for news coverage
    3. Fetching content from top results
    4. Using Gemini to summarize what was found
    """

    print(f"\n🔍 Search Agent investigating: {claim}")
    print("-" * 50)

    # Step 1 — Search the web
    print("📡 Searching the web...")
    web_results = search_web(claim, num_results=5)

    # Step 2 — Search news sources
    print("📰 Searching news sources...")
    news_results = search_news(claim)
    print(f"DEBUG: NewsAPI returned {len(news_results)} articles")

    # Step 3 — Fetch full content from top 3 web results
    print("📄 Fetching article content...")
    fetched_articles = []
    for result in web_results[:3]:
        article = fetch_article(result["link"])
        if article["status"] == "success" and article["text"]:
            fetched_articles.append(article)

    # Step 4 — Build context for Gemini
    context = f"""
    CLAIM TO INVESTIGATE: {claim}

    WEB SEARCH RESULTS:
    {chr(10).join([f"- {r['title']}: {r['snippet']}" for r in web_results])}

    NEWS ARTICLES FOUND:
    {chr(10).join([f"- [{a['source']}] {a['title']} ({a['published_at']})" for a in news_results[:5]])}

    FULL ARTICLE CONTENT FETCHED:
    {chr(10).join([f"SOURCE: {a['url']}{chr(10)}CONTENT: {a['text'][:1000]}" for a in fetched_articles])}
    """

    # Step 5 — Ask Gemini to analyze what was found
    print("🤖 Gemini analyzing findings...")

    prompt = f"""
    You are the Search Agent in a Fake News Investigation system.
    Your job is to analyze search results and summarize key findings.

    {context}

    Based on the search results above, provide a structured summary with:
    1. CLAIM SUMMARY: Restate the claim being investigated in one sentence
    2. KEY FINDINGS: What do search results tell us about this claim? (3-5 bullet points)
    3. SOURCES FOUND: List the most credible sources that appeared
    4. RED FLAGS: Any immediate signs this might be misinformation
    5. NEEDS FURTHER INVESTIGATION: What questions still need to be answered?

    Be factual and concise.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # Return structured result
    return {
        "claim": claim,
        "web_results": web_results,
        "news_results": news_results[:5],
        "fetched_articles": fetched_articles,
        "gemini_analysis": response.text,
        "status": "complete"
    }


# Test the agent directly
if __name__ == "__main__":
    test_claim = "COVID-19 vaccines contain microchips"
    result = run_search_agent(test_claim)

    print("\n" + "="*50)
    print("🤖 GEMINI ANALYSIS:")
    print("="*50)
    print(result["gemini_analysis"])