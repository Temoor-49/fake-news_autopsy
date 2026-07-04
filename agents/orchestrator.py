# agents/orchestrator.py
# Orchestrator Agent — coordinates the full investigation pipeline
# Now includes ChromaDB memory (cache) and security validation

import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from agents.search_agent import run_search_agent
from agents.credibility_agent import run_credibility_agent
from agents.timeline_agent import run_timeline_agent
from agents.verdict_agent import run_verdict_agent
from memory.investigation_memory import InvestigationMemory
from utils.security import sanitizer, rate_limiter, log_investigation, log_blocked_request

memory = InvestigationMemory()


class InvestigationOrchestrator:
    """
    Coordinates the full multi-agent investigation pipeline.
    Now with memory cache and security features.
    """

    def __init__(self):
        self.agent_log = []

    def _log_step(self, agent_name: str, duration: float, status: str):
        self.agent_log.append({
            "agent": agent_name,
            "duration_seconds": round(duration, 2),
            "status": status
        })

    def investigate(self, claim: str, session_id: str = "default") -> dict:
        """
        Runs the full investigation pipeline with:
        - Input sanitization
        - Rate limiting
        - Memory cache check (returns instantly if similar claim found)
        - Full pipeline if no cache hit
        - Stores result in memory after completion
        """

        print(f"\n{'='*60}")
        print(f"🕵️ ORCHESTRATOR STARTING INVESTIGATION")
        print(f"CLAIM: {claim}")
        print(f"{'='*60}")

        # ── SECURITY: Sanitize input ──────────────────────────
        is_valid, cleaned_claim, error_msg = sanitizer.sanitize(claim)
        if not is_valid:
            log_blocked_request(f"sanitization: {error_msg}", claim)
            return {
                "claim": claim,
                "error": error_msg,
                "overall_status": "blocked_sanitization"
            }

        # ── SECURITY: Rate limiting ───────────────────────────
        allowed, rate_msg = rate_limiter.is_allowed(session_id)
        if not allowed:
            log_blocked_request(f"rate_limit", claim)
            return {
                "claim": cleaned_claim,
                "error": rate_msg,
                "overall_status": "blocked_rate_limit"
            }

        # ── MEMORY: Check cache for similar past investigation ─
        print("\n🧠 Checking memory for similar past investigations...")
        cached = memory.find_similar(cleaned_claim)
        if cached:
            log_investigation(
                cleaned_claim,
                cached["verdict_data"]["verdict"],
                cached["verdict_data"]["confidence_score"],
                from_cache=True
            )
            return {
                "claim": cleaned_claim,
                "from_cache": True,
                "similarity_score": cached["similarity_score"],
                "original_claim": cached["original_claim"],
                "verdict_results": {"verdict_data": cached["verdict_data"]},
                "agent_log": [{"agent": "Memory Cache", "duration_seconds": 0.1, "status": "cache_hit"}],
                "overall_status": "complete"
            }

        # ── FULL PIPELINE ─────────────────────────────────────
        report = {
            "claim": cleaned_claim,
            "search_results": None,
            "credibility_results": None,
            "timeline_results": None,
            "verdict_results": None,
            "agent_log": [],
            "overall_status": "in_progress"
        }

        # Step 1 — Search Agent
        try:
            start = time.time()
            search_results = run_search_agent(cleaned_claim)
            self._log_step("Search Agent", time.time() - start, "success")
            report["search_results"] = search_results
        except Exception as e:
            self._log_step("Search Agent", 0, f"failed: {str(e)}")
            report["overall_status"] = "failed"
            report["agent_log"] = self.agent_log
            return report

        # Step 2 — Credibility Agent
        try:
            start = time.time()
            credibility_results = run_credibility_agent(search_results)
            self._log_step("Credibility Agent", time.time() - start, "success")
            report["credibility_results"] = credibility_results
        except Exception as e:
            self._log_step("Credibility Agent", 0, f"failed: {str(e)}")
            credibility_results = {
                "claim": cleaned_claim,
                "domain_scores": [],
                "average_domain_score": 0,
                "credibility_analysis": "Credibility analysis unavailable.",
                "status": "failed"
            }
            report["credibility_results"] = credibility_results

        # Step 3 — Timeline Agent
        try:
            start = time.time()
            timeline_results = run_timeline_agent(search_results)
            self._log_step("Timeline Agent", time.time() - start, "success")
            report["timeline_results"] = timeline_results
        except Exception as e:
            self._log_step("Timeline Agent", 0, f"failed: {str(e)}")
            timeline_results = {
                "claim": cleaned_claim,
                "timeline": [],
                "timeline_analysis": "Timeline analysis unavailable.",
                "status": "failed"
            }
            report["timeline_results"] = timeline_results

        # Step 4 — Verdict Agent
        try:
            start = time.time()
            verdict_results = run_verdict_agent(search_results, credibility_results, timeline_results)
            self._log_step("Verdict Agent", time.time() - start, "success")
            report["verdict_results"] = verdict_results
            report["overall_status"] = "complete"
        except Exception as e:
            self._log_step("Verdict Agent", 0, f"failed: {str(e)}")
            report["overall_status"] = "failed"

        report["agent_log"] = self.agent_log

        # ── MEMORY: Store completed investigation ─────────────
        if report["overall_status"] == "complete":
            memory.store_investigation(cleaned_claim, report)
            log_investigation(
                cleaned_claim,
                report["verdict_results"]["verdict_data"].get("verdict", "UNVERIFIED"),
                report["verdict_results"]["verdict_data"].get("confidence_score", 0),
                from_cache=False
            )

        print(f"\n{'='*60}")
        print(f"✅ INVESTIGATION COMPLETE — Status: {report['overall_status']}")
        print(f"{'='*60}")

        return report


def investigate(claim: str, session_id: str = "default") -> dict:
    """Single entry point for the full investigation pipeline."""
    orchestrator = InvestigationOrchestrator()
    return orchestrator.investigate(claim, session_id)


if __name__ == "__main__":
    # Test 1 — fresh investigation
    print("\n🧪 TEST 1: Fresh investigation")
    result = investigate("5G towers spread COVID-19")
    if result.get("overall_status") == "complete":
        v = result["verdict_results"]["verdict_data"]
        print(f"VERDICT: {v['verdict']} ({v['confidence_score']}/100)")

    # Test 2 — repeat claim should hit cache
    print("\n🧪 TEST 2: Same claim again (should hit cache)")
    result2 = investigate("5G towers spread COVID-19")
    print(f"From cache: {result2.get('from_cache', False)}")
    print(f"Status: {result2.get('overall_status')}")