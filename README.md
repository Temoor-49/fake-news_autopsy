markdown# 🔬 Fake News Autopsy

**A multi-agent AI system that investigates news claims and exposes misinformation trails.**

> Built for the Kaggle AI Agents Intensive Vibe Coding Capstone — Agents for Good track

🔴 **[Live Demo →](YOUR_STREAMLIT_URL_HERE)**
&nbsp;&nbsp;|&nbsp;&nbsp;
📹 **[Demo Video →](YOUR_YOUTUBE_URL_HERE)**

---

## What It Does

Paste any news claim ("COVID-19 vaccines contain microchips") and Fake News Autopsy
deploys a team of 4 specialized AI agents to investigate it:

1. **Search Agent** — searches the web and news sources for related coverage
2. **Credibility Agent** — scores each source's trustworthiness and checks for bias
3. **Timeline Agent** — traces how the story spread chronologically
4. **Verdict Agent** — synthesizes all findings into a structured verdict

Final output: **TRUE / FALSE / MISLEADING / UNVERIFIED** with confidence score,
reasoning chain, supporting evidence, and recommended action.

---

## Architecture
User Input (claim or URL)
↓
[Orchestrator Agent]  ← coordinates everything, handles failures gracefully
↓
┌─────────────────────────────────────────────┐
│  [Search Agent]      [Credibility Agent]    │
│  Web + NewsAPI       Domain reputation +    │
│  Article fetching    Gemini bias analysis   │
│                                             │
│  [Timeline Agent]    [Verdict Agent]        │
│  Chronological       Synthesizes all →      │
│  spread tracing      JSON verdict           │
└─────────────────────────────────────────────┘
↓
[ChromaDB Memory]  ← caches results, instant recall for repeat claims
[MCP Server]       ← exposes pipeline as standardized tools
[Security Layer]   ← input sanitization, rate limiting, audit logging

---

## Course Concepts Demonstrated

| Concept | Where |
|---|---|
| ✅ Multi-agent system (ADK) | `agents/orchestrator.py` + 4 specialized agents |
| ✅ MCP Server | `mcp_server/investigation_server.py` |
| ✅ Security features | `utils/security.py` — sanitization, rate limiting, logging |
| ✅ Memory/State | `memory/investigation_memory.py` — ChromaDB vector cache |
| ✅ Deployability | Streamlit Cloud deployment |
| ✅ Antigravity | Demonstrated in video |

---

## Tech Stack

- **Language:** Python 3.11
- **Agent Framework:** Google ADK + Gemini 2.5 Flash
- **Search:** Serper API + NewsAPI
- **Memory:** ChromaDB (vector similarity cache)
- **UI:** Streamlit (dark forensic theme)
- **Protocol:** MCP Server (investigate_claim + save_report tools)
- **Security:** Input sanitization + rate limiting + audit logging
- **Deployment:** Streamlit Community Cloud

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOURUSERNAME/fake-news-autopsy.git
cd fake-news-autopsy

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add API keys
# Create a .env file with:
# GOOGLE_API_KEY=your_key
# SERPER_API_KEY=your_key
# NEWS_API_KEY=your_key

# 5. Run the app
streamlit run ui/app.py
```

---

## Sample Verdicts

| Claim | Verdict | Confidence |
|---|---|---|
| COVID-19 vaccines contain microchips | 🔴 FALSE | 95/100 |
| 5G towers spread COVID-19 | 🔴 FALSE | 90/100 |
| Climate change is caused by humans | 🟢 TRUE | 88/100 |

---

*Built solo in 12 days for the Kaggle AI Agents Intensive Capstone.*

