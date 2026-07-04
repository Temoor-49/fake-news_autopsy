# agents/credibility_agent.py
# Credibility Agent — scores each source found by the Search Agent
# for trustworthiness, bias, and reliability

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from dotenv import load_dotenv
from google import genai
from tools.domain_checker import check_domain_reputation
from utils.config import get_secret

load_dotenv()
client = genai.Client(api_key=get_secret("GOOGLE_API_KEY"))


def run_credibility_agent(search_agent_results: dict) -> dict:
    """
    Credibility Agent — takes the output from the Search Agent and:
    1. Scores each source's domain reputation
    2. Uses Gemini to detect bias/tone signals in fetched articles
    3. Checks if multiple credible sources agree on the claim

    Input: the dict returned by run_search_agent()
    Returns: structured credibility report
    """

    claim = search_agent_results["claim"]
    fetched_articles = search_agent_results["fetched_articles"]
    news_results = search_agent_results["news_results"]

    print(f"\n🛡️ Credibility Agent evaluating sources for: {claim}")
    print("-" * 50)

    # Step 1 — Score domain reputation for every fetched article
    print("🌐 Checking domain reputations...")
    domain_scores = []
    for article in fetched_articles:
        rep = check_domain_reputation(article["url"])
        domain_scores.append({
            "url": article["url"],
            "title": article["title"],
            **rep
        })

    # Step 2 — Also score domains from news_results (different sources)
    for news in news_results:
        rep = check_domain_reputation(news["url"])
        domain_scores.append({
            "url": news["url"],
            "title": news["title"],
            **rep
        })

    # Step 3 — Calculate average credibility score
    if domain_scores:
        avg_score = sum(d["score"] for d in domain_scores) / len(domain_scores)
    else:
        avg_score = 5  # neutral default if nothing found

    # Step 4 — Build context for Gemini bias/tone analysis
    articles_text = "\n\n".join([
        f"SOURCE: {a['url']}\nDOMAIN REPUTATION: {next((d['reputation'] for d in domain_scores if d['url']==a['url']), 'unknown')}\nCONTENT: {a['text'][:800]}"
        for a in fetched_articles
    ])

    prompt = f"""
    You are the Credibility Agent in a Fake News Investigation system.
    Your job is to evaluate the trustworthiness of sources discussing this claim.

    CLAIM: {claim}

    SOURCES AND CONTENT:
    {articles_text}

    DOMAIN REPUTATION SCORES (0-10 scale, 10 = most credible):
    {chr(10).join([f"- {d['domain']}: {d['score']}/10 ({d['reputation']})" for d in domain_scores])}

    Based on this information, provide:
    1. OVERALL CREDIBILITY VERDICT: (High / Medium / Low) — how trustworthy is the coverage of this claim overall?
    2. BIAS SIGNALS: Do any sources show emotional language, one-sidedness, or sensationalism? Give examples.
    3. SOURCE AGREEMENT: Do multiple independent credible sources agree with each other? Or is there only one source?
    4. RELIABILITY CONCERNS: Any specific reasons to doubt these sources?
    5. CONFIDENCE SCORE: Give a number 0-100 representing how confident you are in the credibility assessment.

    Be objective and evidence-based.
    """

    print("🤖 Gemini analyzing source credibility...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "claim": claim,
        "domain_scores": domain_scores,
        "average_domain_score": round(avg_score, 1),
        "credibility_analysis": response.text,
        "status": "complete"
    }


# Test the agent directly — chains with Search Agent
if __name__ == "__main__":
    from agents.search_agent import run_search_agent

    test_claim = "COVID-19 vaccines contain microchips"

    print("STEP 1: Running Search Agent first...\n")
    search_results = run_search_agent(test_claim)

    print("\n\nSTEP 2: Running Credibility Agent...\n")
    credibility_results = run_credibility_agent(search_results)

    print("\n" + "=" * 50)
    print("🛡️ CREDIBILITY ANALYSIS:")
    print("=" * 50)
    print(f"Average Domain Score: {credibility_results['average_domain_score']}/10\n")
    print(credibility_results["credibility_analysis"])