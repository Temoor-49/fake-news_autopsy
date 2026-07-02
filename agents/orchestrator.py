# agents/orchestrator.py
# Orchestrator Agent — the central coordinator of the Fake News Autopsy system
# This is the single entry point. It calls Search -> Credibility -> Timeline -> Verdict
# in sequence, handles failures gracefully, and returns one unified investigation report.

import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.search_agent import run_search_agent
from agents.credibility_agent import run_credibility_agent
from agents.timeline_agent import run_timeline_agent
from agents.verdict_agent import run_verdict_agent


class InvestigationOrchestrator:
    """
    Coordinates the full multi-agent investigation pipeline.

    Pipeline order matters:
    1. Search Agent    -> gathers raw evidence (web + news + articles)
    2. Credibility Agent -> scores trustworthiness of what Search found
    3. Timeline Agent  -> traces spread pattern of what Search found
    4. Verdict Agent   -> synthesizes everything into final judgment

    Credibility and Timeline both depend on Search Agent output,
    but are independent of each other (could run in parallel later).
    Verdict depends on ALL THREE prior agents.
    """

    def __init__(self):
        self.agent_log = []  # tracks which agents ran and how long they took

    def _log_step(self, agent_name: str, duration: float, status: str):
        self.agent_log.append({
            "agent": agent_name,
            "duration_seconds": round(duration, 2),
            "status": status
        })

    def investigate(self, claim: str) -> dict:
        """
        Runs the full investigation pipeline on a claim.
        Returns a unified report with results from all agents + final verdict.
        Handles partial failures gracefully — if one agent fails,
        downstream agents still attempt to run with whatever data exists.
        """

        print(f"\n{'='*60}")
        print(f"🕵️ ORCHESTRATOR STARTING INVESTIGATION")
        print(f"CLAIM: {claim}")
        print(f"{'='*60}")

        report = {
            "claim": claim,
            "search_results": None,
            "credibility_results": None,
            "timeline_results": None,
            "verdict_results": None,
            "agent_log": [],
            "overall_status": "in_progress"
        }

        # --- STEP 1: Search Agent ---
        try:
            start = time.time()
            search_results = run_search_agent(claim)
            self._log_step("Search Agent", time.time() - start, "success")
            report["search_results"] = search_results
        except Exception as e:
            self._log_step("Search Agent", 0, f"failed: {str(e)}")
            report["overall_status"] = "failed"
            report["agent_log"] = self.agent_log
            print(f"❌ Search Agent failed — cannot continue without base evidence: {e}")
            return report  # Can't proceed without search results

        # --- STEP 2: Credibility Agent ---
        try:
            start = time.time()
            credibility_results = run_credibility_agent(search_results)
            self._log_step("Credibility Agent", time.time() - start, "success")
            report["credibility_results"] = credibility_results
        except Exception as e:
            self._log_step("Credibility Agent", 0, f"failed: {str(e)}")
            print(f"⚠️ Credibility Agent failed, continuing with limited data: {e}")
            credibility_results = {
                "claim": claim,
                "domain_scores": [],
                "average_domain_score": 0,
                "credibility_analysis": "Credibility analysis unavailable due to an error.",
                "status": "failed"
            }
            report["credibility_results"] = credibility_results

        # --- STEP 3: Timeline Agent ---
        try:
            start = time.time()
            timeline_results = run_timeline_agent(search_results)
            self._log_step("Timeline Agent", time.time() - start, "success")
            report["timeline_results"] = timeline_results
        except Exception as e:
            self._log_step("Timeline Agent", 0, f"failed: {str(e)}")
            print(f"⚠️ Timeline Agent failed, continuing with limited data: {e}")
            timeline_results = {
                "claim": claim,
                "timeline": [],
                "timeline_analysis": "Timeline analysis unavailable due to an error.",
                "status": "failed"
            }
            report["timeline_results"] = timeline_results

        # --- STEP 4: Verdict Agent (needs all 3 above) ---
        try:
            start = time.time()
            verdict_results = run_verdict_agent(search_results, credibility_results, timeline_results)
            self._log_step("Verdict Agent", time.time() - start, "success")
            report["verdict_results"] = verdict_results
            report["overall_status"] = "complete"
        except Exception as e:
            self._log_step("Verdict Agent", 0, f"failed: {str(e)}")
            print(f"❌ Verdict Agent failed: {e}")
            report["overall_status"] = "failed"

        report["agent_log"] = self.agent_log

        print(f"\n{'='*60}")
        print(f"✅ INVESTIGATION COMPLETE — Status: {report['overall_status']}")
        print(f"{'='*60}")

        return report


def investigate(claim: str) -> dict:
    """
    Convenience function — the single entry point your UI will call.
    Usage: result = investigate("some claim here")
    """
    orchestrator = InvestigationOrchestrator()
    return orchestrator.investigate(claim)


# Test the orchestrator directly
if __name__ == "__main__":
    test_claim = "COVID-19 vaccines contain microchips"

    result = investigate(test_claim)

    print("\n" + "=" * 60)
    print("📊 AGENT EXECUTION LOG")
    print("=" * 60)
    for entry in result["agent_log"]:
        status_icon = "✅" if entry["status"] == "success" else "❌"
        print(f"{status_icon} {entry['agent']}: {entry['duration_seconds']}s — {entry['status']}")

    if result["overall_status"] == "complete":
        v = result["verdict_results"]["verdict_data"]
        print("\n" + "=" * 60)
        print("⚖️ FINAL VERDICT")
        print("=" * 60)
        print(f"VERDICT: {v['verdict']}")
        print(f"CONFIDENCE: {v['confidence_score']}/100")
        print(f"SUMMARY: {v['one_line_summary']}")