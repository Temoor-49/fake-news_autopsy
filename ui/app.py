# ui/app.py
# Fake News Autopsy — Streamlit UI
# Full investigation interface with real-time progress,
# verdict display, source credibility, report download,
# memory cache badge, security blocking, and sidebar history

import streamlit as st
import sys
import os
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import investigate
from memory.investigation_memory import InvestigationMemory
from utils.security import rate_limiter

memory_store = InvestigationMemory()

# ─── PAGE CONFIG ────────────────────────────────────────────
st.set_page_config(
    page_title="Fake News Autopsy",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CUSTOM CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0d0d0f;
    color: #e8e8e8;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 2rem; padding-bottom: 2rem;}

.hero {
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
    border-bottom: 1px solid #222;
    margin-bottom: 2rem;
}
.hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.8rem;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.02em;
    margin: 0;
}
.hero-title span { color: #e84444; }
.hero-subtitle {
    font-size: 1rem;
    color: #888;
    margin-top: 0.5rem;
    font-weight: 300;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.verdict-false {
    background: linear-gradient(135deg, #1a0505 0%, #2d0808 100%);
    border: 2px solid #e84444;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
}
.verdict-true {
    background: linear-gradient(135deg, #031a08 0%, #062d10 100%);
    border: 2px solid #22c55e;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
}
.verdict-misleading {
    background: linear-gradient(135deg, #1a1205 0%, #2d1f08 100%);
    border: 2px solid #f59e0b;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
}
.verdict-unverified {
    background: linear-gradient(135deg, #0d0d0f 0%, #1a1a1f 100%);
    border: 2px solid #6b7280;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
}
.verdict-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 3rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin: 0;
}
.verdict-false .verdict-label  { color: #e84444; }
.verdict-true .verdict-label   { color: #22c55e; }
.verdict-misleading .verdict-label { color: #f59e0b; }
.verdict-unverified .verdict-label { color: #6b7280; }

.confidence-text {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    color: #aaa;
    margin-top: 0.5rem;
}
.summary-text {
    font-size: 1rem;
    color: #ddd;
    margin-top: 1rem;
    font-style: italic;
    line-height: 1.6;
}

.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #e84444;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #222;
}

.evidence-item {
    background: #141416;
    border-left: 3px solid #e84444;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 0 6px 6px 0;
    font-size: 0.9rem;
    line-height: 1.5;
    color: #ccc;
}

.source-card {
    background: #141416;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
}
.source-domain {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #e84444;
}
.source-title {
    font-size: 0.85rem;
    color: #ccc;
    margin-top: 0.25rem;
}

.agent-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 1rem;
    border-bottom: 1px solid #1a1a1a;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
}
.agent-name  { color: #ddd; }
.agent-time  { color: #666; }
.agent-success { color: #22c55e; }
.agent-failed  { color: #e84444; }
.agent-cache   { color: #3b82f6; }

.action-box {
    background: #141416;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 1.25rem;
    font-size: 0.95rem;
    color: #ddd;
    line-height: 1.6;
}

.limitation-box {
    background: #12100a;
    border: 1px solid #2d2200;
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.85rem;
    color: #999;
    line-height: 1.5;
}

.cache-badge {
    background: #0a1a0a;
    border: 1px solid #22c55e;
    border-radius: 6px;
    padding: 0.6rem 1rem;
    margin-bottom: 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #22c55e;
}

.stTextArea textarea {
    background: #141416 !important;
    border: 1px solid #333 !important;
    color: #e8e8e8 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
}
.stTextArea textarea:focus {
    border-color: #e84444 !important;
    box-shadow: 0 0 0 1px #e84444 !important;
}

.stButton > button {
    background: #e84444 !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 2rem !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    border-radius: 6px !important;
    width: 100% !important;
    text-transform: uppercase !important;
}
.stButton > button:hover {
    background: #c53030 !important;
    transform: translateY(-1px);
}

.timeline-item {
    display: flex;
    gap: 1rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid #1a1a1a;
    align-items: flex-start;
}
.timeline-seq {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #e84444;
    min-width: 60px;
    padding-top: 2px;
}
.timeline-content { flex: 1; }
.timeline-source {
    font-size: 0.75rem;
    color: #888;
    font-family: 'IBM Plex Mono', monospace;
}
.timeline-title {
    font-size: 0.85rem;
    color: #ccc;
    margin-top: 0.2rem;
}
.timeline-date {
    font-size: 0.75rem;
    color: #555;
    margin-top: 0.2rem;
    font-family: 'IBM Plex Mono', monospace;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0a0a0c !important;
    border-right: 1px solid #1a1a1a;
}
</style>
""", unsafe_allow_html=True)


# ─── HELPER FUNCTIONS ────────────────────────────────────────

def get_verdict_class(verdict: str) -> str:
    return {
        "FALSE":      "verdict-false",
        "TRUE":       "verdict-true",
        "MISLEADING": "verdict-misleading",
        "UNVERIFIED": "verdict-unverified"
    }.get(verdict.upper(), "verdict-unverified")


def get_verdict_emoji(verdict: str) -> str:
    return {
        "FALSE":      "🔴",
        "TRUE":       "🟢",
        "MISLEADING": "🟡",
        "UNVERIFIED": "⚪"
    }.get(verdict.upper(), "⚪")


def render_verdict_card(verdict_data: dict):
    verdict    = verdict_data.get("verdict", "UNVERIFIED")
    confidence = verdict_data.get("confidence_score", 0)
    summary    = verdict_data.get("one_line_summary", "")
    css_class  = get_verdict_class(verdict)
    emoji      = get_verdict_emoji(verdict)

    st.markdown(f"""
    <div class="{css_class}">
        <p class="verdict-label">{emoji} {verdict}</p>
        <p class="confidence-text">Confidence: {confidence}/100</p>
        <p class="summary-text">"{summary}"</p>
    </div>
    """, unsafe_allow_html=True)


def render_agent_log(agent_log: list):
    st.markdown('<p class="section-header">⚙ Agent Execution Log</p>', unsafe_allow_html=True)
    for entry in agent_log:
        status = entry["status"]
        if status == "success":
            status_html = '<span class="agent-success">✓ success</span>'
        elif status == "cache_hit":
            status_html = '<span class="agent-cache">⚡ cache hit</span>'
        else:
            status_html = f'<span class="agent-failed">✗ {status}</span>'

        st.markdown(f"""
        <div class="agent-row">
            <span class="agent-name">{entry['agent']}</span>
            <span class="agent-time">{entry['duration_seconds']}s</span>
            {status_html}
        </div>
        """, unsafe_allow_html=True)


def render_evidence(evidence_list: list):
    st.markdown('<p class="section-header">✦ Supporting Evidence</p>', unsafe_allow_html=True)
    for point in evidence_list:
        st.markdown(f'<div class="evidence-item">{point}</div>', unsafe_allow_html=True)


def render_sources(domain_scores: list):
    st.markdown('<p class="section-header">◈ Source Credibility</p>', unsafe_allow_html=True)
    if not domain_scores:
        st.markdown(
            '<p style="color:#555; font-size:0.85rem;">No source data available.</p>',
            unsafe_allow_html=True
        )
        return
    for source in domain_scores[:6]:
        score      = source.get("score", 5)
        reputation = source.get("reputation", "unknown")
        domain     = source.get("domain", "")
        title      = source.get("title", "")[:80]
        score_color = (
            "#22c55e" if score >= 7
            else "#f59e0b" if score >= 4
            else "#e84444"
        )
        st.markdown(f"""
        <div class="source-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="source-domain">{domain}</span>
                <span style="font-family:'IBM Plex Mono',monospace; font-size:0.8rem; color:{score_color};">
                    {score}/10 — {reputation}
                </span>
            </div>
            <div class="source-title">{title}</div>
        </div>
        """, unsafe_allow_html=True)


def render_timeline(timeline: list):
    if not timeline:
        st.markdown(
            '<p style="color:#555; font-size:0.85rem;">No timeline data available for this claim.</p>',
            unsafe_allow_html=True
        )
        return
    for item in timeline:
        seq_label = "🟢 ORIGIN" if item.get("is_likely_origin") else f"#{item['sequence']}"
        date_str  = item.get("published_at", "")[:10]
        st.markdown(f"""
        <div class="timeline-item">
            <span class="timeline-seq">{seq_label}</span>
            <div class="timeline-content">
                <div class="timeline-source">{item.get('source','')}</div>
                <div class="timeline-title">{item.get('title','')}</div>
                <div class="timeline-date">{date_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def build_download_report(result: dict) -> str:
    download_data = {
        "metadata": {
            "system": "Fake News Autopsy",
            "investigated_at": datetime.now().isoformat(),
            "claim": result.get("claim", ""),
            "from_cache": result.get("from_cache", False)
        },
        "verdict":   result.get("verdict_results", {}).get("verdict_data", {}),
        "agent_log": result.get("agent_log", [])
    }
    return json.dumps(download_data, indent=2)


# ─── SIDEBAR ─────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<p style="font-family:\'IBM Plex Mono\',monospace; font-size:0.75rem; '
            'color:#e84444; letter-spacing:0.1em; padding-top:1rem;">◈ PAST INVESTIGATIONS</p>',
            unsafe_allow_html=True
        )
        past = memory_store.get_all_investigations()
        if not past:
            st.markdown(
                '<p style="color:#444; font-size:0.8rem;">No past investigations yet.</p>',
                unsafe_allow_html=True
            )
        else:
            for inv in past[:10]:
                verdict = inv.get("verdict", "")
                emoji   = {"FALSE": "🔴", "TRUE": "🟢", "MISLEADING": "🟡"}.get(verdict, "⚪")
                st.markdown(
                    f'<div style="padding:0.5rem 0; border-bottom:1px solid #1a1a1a;">'
                    f'<span style="font-size:0.75rem; color:#aaa;">{emoji} {verdict}</span><br>'
                    f'<span style="font-size:0.7rem; color:#555;">{inv["claim"][:50]}...</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        remaining = rate_limiter.get_remaining(str(id(st.session_state)))
        st.markdown(
            f'<p style="color:#333; font-size:0.7rem; font-family:\'IBM Plex Mono\',monospace; '
            f'margin-top:1rem;">Stored: {memory_store.count()} | Requests left: {remaining}/5</p>',
            unsafe_allow_html=True
        )


# ─── MAIN APP ────────────────────────────────────────────────

def main():
    render_sidebar()

    # Hero Header
    st.markdown("""
    <div class="hero">
        <h1 class="hero-title">🔬 FAKE NEWS <span>AUTOPSY</span></h1>
        <p class="hero-subtitle">Multi-Agent Misinformation Investigation System</p>
    </div>
    """, unsafe_allow_html=True)

    # Input Section
    col_input, col_spacer = st.columns([3, 1])
    with col_input:
        claim = st.text_area(
            label="Enter claim to investigate",
            placeholder="e.g. 'COVID-19 vaccines contain microchips' or paste a news article URL...",
            height=100,
            label_visibility="collapsed"
        )
        col_btn, col_examples = st.columns([1, 2])
        with col_btn:
            run_button = st.button("🔬 INVESTIGATE", use_container_width=True)
        with col_examples:
            st.markdown(
                '<p style="color:#555; font-size:0.8rem; padding-top:0.75rem;">'
                'Try: "5G towers spread COVID-19" or "Climate change is a hoax"</p>',
                unsafe_allow_html=True
            )

    # Session state
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "last_claim" not in st.session_state:
        st.session_state.last_claim = None

    # ── RUN INVESTIGATION ────────────────────────────────────
    if run_button and claim.strip():
        st.markdown("---")

        progress_container = st.container()
        with progress_container:
            st.markdown(
                '<p class="section-header">◎ Investigation In Progress</p>',
                unsafe_allow_html=True
            )
            progress_bar = st.progress(0)
            status_text  = st.empty()

            status_text.markdown(
                '<p style="color:#888; font-family:\'IBM Plex Mono\',monospace; font-size:0.85rem;">'
                '⟳ Checking memory and validating input...</p>',
                unsafe_allow_html=True
            )
            progress_bar.progress(10)

        with st.spinner(""):
            try:
                progress_bar.progress(25)
                status_text.markdown(
                    '<p style="color:#888; font-family:\'IBM Plex Mono\',monospace; font-size:0.85rem;">'
                    '⟳ Running multi-agent investigation pipeline...</p>',
                    unsafe_allow_html=True
                )

                result = investigate(
                    claim.strip(),
                    session_id=str(id(st.session_state))
                )

                # Handle security blocks
                if result.get("overall_status") in ["blocked_sanitization", "blocked_rate_limit"]:
                    progress_bar.progress(100)
                    status_text.markdown(
                        '<p style="color:#e84444; font-family:\'IBM Plex Mono\',monospace; font-size:0.85rem;">'
                        f'⚠ Blocked: {result.get("error")}</p>',
                        unsafe_allow_html=True
                    )
                    st.error(result.get("error"))
                    st.stop()

                progress_bar.progress(100)
                status_text.markdown(
                    '<p style="color:#22c55e; font-family:\'IBM Plex Mono\',monospace; font-size:0.85rem;">'
                    '✓ Investigation complete</p>',
                    unsafe_allow_html=True
                )

                st.session_state.last_result = result
                st.session_state.last_claim  = claim.strip()

            except Exception as e:
                st.error(f"Investigation failed: {str(e)}")
                return

    # ── DISPLAY RESULTS ──────────────────────────────────────
    if st.session_state.last_result:
        result           = st.session_state.last_result
        verdict_data     = result.get("verdict_results", {}).get("verdict_data", {})
        credibility_data = result.get("credibility_results", {})
        timeline_data    = result.get("timeline_results", {})
        agent_log        = result.get("agent_log", [])

        st.markdown("---")

        # Cache badge
        if result.get("from_cache"):
            st.markdown(
                f'<div class="cache-badge">⚡ INSTANT RESULT — Served from memory cache '
                f'(similarity: {result.get("similarity_score", 0):.0%})</div>',
                unsafe_allow_html=True
            )

        # Verdict (full width)
        st.markdown('<p class="section-header">◉ Verdict</p>', unsafe_allow_html=True)
        render_verdict_card(verdict_data)

        st.markdown("<br>", unsafe_allow_html=True)

        # Two-column layout
        col_left, col_right = st.columns([3, 2])

        with col_left:
            # Reasoning
            st.markdown('<p class="section-header">◎ Reasoning</p>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="action-box">{verdict_data.get("reasoning", "")}</div>',
                unsafe_allow_html=True
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Evidence
            render_evidence(verdict_data.get("supporting_evidence", []))

            st.markdown("<br>", unsafe_allow_html=True)

            # Timeline
            st.markdown('<p class="section-header">◷ Misinformation Timeline</p>', unsafe_allow_html=True)
            render_timeline(timeline_data.get("timeline", []))

            if timeline_data.get("timeline_analysis"):
                with st.expander("Full timeline analysis"):
                    st.markdown(
                        f'<div style="color:#aaa; font-size:0.85rem; line-height:1.6;">'
                        f'{timeline_data["timeline_analysis"]}</div>',
                        unsafe_allow_html=True
                    )

        with col_right:
            # Recommended Action
            st.markdown('<p class="section-header">◈ Recommended Action</p>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="action-box">{verdict_data.get("recommended_action", "")}</div>',
                unsafe_allow_html=True
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Source Credibility
            render_sources(credibility_data.get("domain_scores", []))

            st.markdown("<br>", unsafe_allow_html=True)

            # Agent Log
            render_agent_log(agent_log)

            st.markdown("<br>", unsafe_allow_html=True)

            # Limitations
            if verdict_data.get("limitations"):
                st.markdown('<p class="section-header">⚠ Limitations</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="limitation-box">{verdict_data["limitations"]}</div>',
                    unsafe_allow_html=True
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Download
            st.markdown('<p class="section-header">↓ Export Report</p>', unsafe_allow_html=True)
            download_json = build_download_report(result)
            st.download_button(
                label="⬇ DOWNLOAD FULL REPORT",
                data=download_json,
                file_name=f"autopsy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    elif not st.session_state.last_result and not (run_button and claim.strip()):
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; padding:3rem; color:#333;">
            <p style="font-size:3rem;">🔬</p>
            <p style="font-family:'IBM Plex Mono',monospace; font-size:0.9rem;
            color:#444; letter-spacing:0.1em;">
                ENTER A CLAIM ABOVE TO BEGIN AUTOPSY
            </p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()