# agents/verdict_agent.py
# Verdict Agent — the final judge in the investigation pipeline
# Synthesizes Search, Credibility, and Timeline findings into one structured verdict

import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from dotenv import load_dotenv
from google import genai
from utils.config import get_secret

load_dotenv()
client = genai.Client(api_key=get_secret("GOOGLE_API_KEY"))


def run_verdict_agent(search_results: dict, credibility_results: dict, timeline_results: dict) -> dict:
    """
    Verdict Agent — takes outputs from all 3 prior agents and delivers
    a final structured verdict with reasoning and confidence score.

    Inputs: outputs of run_search_agent(), run_credibility_agent(), run_timeline_agent()
    Returns: structured final verdict report
    """

    claim = search_results["claim"]

    print(f"\n⚖️ Verdict Agent delivering final judgment for: {claim}")
    print("-" * 50)

    # Build full context from all 3 agents
    context = f"""
    CLAIM UNDER INVESTIGATION: {claim}

    === SEARCH AGENT FINDINGS ===
    {search_results['gemini_analysis']}

    === CREDIBILITY AGENT FINDINGS ===
    Average Domain Score: {credibility_results['average_domain_score']}/10
    {credibility_results['credibility_analysis']}

    === TIMELINE AGENT FINDINGS ===
    Status: {timeline_results['status']}
    {timeline_results['timeline_analysis']}
    """

    prompt = f"""
    You are the Verdict Agent — the final decision-maker in a Fake News Investigation system.
    Three specialist agents have already investigated this claim. Your job is to synthesize
    their findings into ONE final, structured verdict.

    {context}

    IMPORTANT RULES:
    - Base your verdict ONLY on the evidence provided above. Do not use outside knowledge not reflected in these findings.
    - If the Timeline Agent reported low confidence or irrelevant data, acknowledge that gap honestly — do not let it weaken your verdict if Search/Credibility evidence is otherwise strong.
    - Be conservative: if evidence is genuinely mixed or insufficient, the verdict should be UNVERIFIED rather than guessing.

    Respond ONLY in valid JSON format (no markdown, no backticks, no extra text) with this exact structure:

    {{
        "verdict": "TRUE or FALSE or MISLEADING or UNVERIFIED",
        "confidence_score": <integer 0-100>,
        "one_line_summary": "<single sentence verdict summary for a headline>",
        "reasoning": "<2-4 sentences explaining WHY this verdict was reached, citing which agent's findings mattered most>",
        "supporting_evidence": ["<key point 1>", "<key point 2>", "<key point 3>"],
        "limitations": "<1-2 sentences on any weaknesses in the investigation, e.g. limited timeline data, single-source reliance>",
        "recommended_action": "<what should a reader do with this claim - e.g. 'Do not share', 'Verify with primary source', 'Safe to share with context'>"
    }}
    """

    print("🤖 Gemini synthesizing final verdict...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # Parse the JSON response safely
    raw_text = response.text.strip()

    # Clean up in case Gemini adds markdown code fences despite instructions
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        verdict_json = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing failed: {e}")
        # Fallback — return raw text so nothing crashes
        verdict_json = {
            "verdict": "UNVERIFIED",
            "confidence_score": 0,
            "one_line_summary": "Verdict could not be parsed.",
            "reasoning": raw_text,
            "supporting_evidence": [],
            "limitations": "JSON parsing error occurred.",
            "recommended_action": "Manual review needed."
        }

    return {
        "claim": claim,
        "verdict_data": verdict_json,
        "status": "complete"
    }


# Test the agent directly — chains all 3 previous agents
if __name__ == "__main__":
    from agents.search_agent import run_search_agent
    from agents.credibility_agent import run_credibility_agent
    from agents.timeline_agent import run_timeline_agent

    test_claim = "COVID-19 vaccines contain microchips"

    print("STEP 1: Running Search Agent...\n")
    search_results = run_search_agent(test_claim)

    print("\n\nSTEP 2: Running Credibility Agent...\n")
    credibility_results = run_credibility_agent(search_results)

    print("\n\nSTEP 3: Running Timeline Agent...\n")
    timeline_results = run_timeline_agent(search_results)

    print("\n\nSTEP 4: Running Verdict Agent...\n")
    verdict_results = run_verdict_agent(search_results, credibility_results, timeline_results)

    print("\n" + "=" * 50)
    print("⚖️ FINAL VERDICT")
    print("=" * 50)

    v = verdict_results["verdict_data"]
    print(f"\n📋 VERDICT: {v['verdict']}")
    print(f"🎯 CONFIDENCE: {v['confidence_score']}/100")
    print(f"\n📰 SUMMARY: {v['one_line_summary']}")
    print(f"\n🧠 REASONING: {v['reasoning']}")
    print(f"\n✅ SUPPORTING EVIDENCE:")
    for point in v['supporting_evidence']:
        print(f"   • {point}")
    print(f"\n⚠️ LIMITATIONS: {v['limitations']}")
    print(f"\n💡 RECOMMENDED ACTION: {v['recommended_action']}")