# agents/timeline_agent.py
# Timeline Agent — traces how a claim spread across sources over time
# This produces the "misinformation trail" — a key unique feature of the project

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google import genai
from tools.timeline_builder import build_timeline

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def run_timeline_agent(search_agent_results: dict) -> dict:
    """
    Timeline Agent — takes Search Agent output and:
    1. Builds a chronological timeline of news coverage
    2. Identifies the likely origin point
    3. Uses Gemini to analyze how the story evolved/spread/distorted over time

    Input: dict returned by run_search_agent()
    Returns: structured timeline report
    """

    claim = search_agent_results["claim"]
    news_results = search_agent_results["news_results"]

    # DEBUG
    print(f"DEBUG: news_results count = {len(news_results)}")
    if news_results:
        print(f"DEBUG: first article = {news_results[0]}")

    print(f"\n🕒 Timeline Agent tracing spread for: {claim}")
    print("-" * 50)

    # Step 1 — Build chronological timeline
    print("📅 Building timeline...")
    timeline = build_timeline(news_results)

    if not timeline:
        return {
            "claim": claim,
            "timeline": [],
            "timeline_analysis": "Not enough dated articles were found to build a reliable timeline.",
            "status": "incomplete"
        }

    # Step 2 — Build context for Gemini
    timeline_text = "\n".join([
        f"#{item['sequence']} | {item['published_at']} | {item['source']}: {item['title']}"
        + (" ⬅ EARLIEST FOUND" if item["is_likely_origin"] else "")
        for item in timeline
    ])

    prompt = f"""
    You are the Timeline Agent in a Fake News Investigation system.
    Your job is to analyze how a claim or story spread across news sources over time.

    CLAIM: {claim}

    CHRONOLOGICAL TIMELINE OF COVERAGE (oldest to newest):
    {timeline_text}

    Based on this timeline, provide:
    1. LIKELY ORIGIN: Which source appears to have covered this first, and what does that suggest about where the story/claim started?
    2. SPREAD PATTERN: How did coverage evolve over time? Did more outlets pick it up quickly (viral spread) or slowly (organic)?
    3. NARRATIVE SHIFT: Based on titles, does the story seem to have changed/escalated/been distorted as it spread? Any signs of exaggeration over time?
    4. SPREAD VELOCITY: Classify as RAPID / MODERATE / SLOW based on the time gaps between articles
    5. TIMELINE CONFIDENCE: Note if there are gaps or too few sources to draw strong conclusions

    Be analytical and note any limitations in the available data.
    """

    print("🤖 Gemini analyzing spread pattern...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "claim": claim,
        "timeline": timeline,
        "timeline_analysis": response.text,
        "status": "complete"
    }


# Test the agent directly — chains with Search Agent
if __name__ == "__main__":
    from agents.search_agent import run_search_agent

    test_claim = "COVID-19 vaccines contain microchips"

    print("STEP 1: Running Search Agent first...\n")
    search_results = run_search_agent(test_claim)

    print("\n\nSTEP 2: Running Timeline Agent...\n")
    timeline_results = run_timeline_agent(search_results)

    print("\n" + "=" * 50)
    print("🕒 TIMELINE ANALYSIS:")
    print("=" * 50)

    if timeline_results["timeline"]:
        print("\nCHRONOLOGY:")
        for item in timeline_results["timeline"]:
            marker = "🟢 ORIGIN" if item["is_likely_origin"] else f"#{item['sequence']}"
            print(f"{marker} | {item['published_at']} | {item['source']}: {item['title']}")

    print("\n" + "-" * 50)
    print(timeline_results["timeline_analysis"])