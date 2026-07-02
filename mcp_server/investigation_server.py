# mcp_server/investigation_server.py
# MCP Server for Fake News Autopsy
# Exposes the investigation pipeline as standardized MCP tools
# Any MCP-compatible client can call these tools directly

import os
import sys
import json
import asyncio
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from agents.orchestrator import investigate

# Initialize the MCP server with a name judges can see
app = Server("fake-news-autopsy")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """
    Declares all tools this MCP server exposes.
    MCP clients call this first to discover what's available.
    """
    return [
        types.Tool(
            name="investigate_claim",
            description=(
                "Investigates a news claim or article URL using a multi-agent pipeline. "
                "Runs Search, Credibility, Timeline, and Verdict agents in sequence. "
                "Returns a structured verdict: TRUE, FALSE, MISLEADING, or UNVERIFIED "
                "with confidence score and full reasoning chain."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "The news claim or article text to investigate"
                    }
                },
                "required": ["claim"]
            }
        ),
        types.Tool(
            name="save_report",
            description=(
                "Saves a completed investigation report to a local JSON file. "
                "Returns the file path where the report was saved."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "The original claim that was investigated"
                    },
                    "report": {
                        "type": "object",
                        "description": "The full investigation report to save"
                    }
                },
                "required": ["claim", "report"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """
    Handles tool calls from MCP clients.
    Routes each call to the correct handler.
    """

    if name == "investigate_claim":
        return await handle_investigate(arguments)

    elif name == "save_report":
        return await handle_save_report(arguments)

    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def handle_investigate(arguments: dict):
    """
    Runs the full investigation pipeline asynchronously.
    Returns structured verdict as JSON text.
    """
    claim = arguments.get("claim", "").strip()

    if not claim:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": "No claim provided"})
        )]

    try:
        # Run the synchronous pipeline in a thread pool
        # so it doesn't block the async MCP server
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, investigate, claim)

        # Extract the key parts judges care about
        verdict_data = result.get("verdict_results", {}).get("verdict_data", {})
        agent_log = result.get("agent_log", [])

        response = {
            "claim": claim,
            "verdict": verdict_data.get("verdict", "UNVERIFIED"),
            "confidence_score": verdict_data.get("confidence_score", 0),
            "one_line_summary": verdict_data.get("one_line_summary", ""),
            "reasoning": verdict_data.get("reasoning", ""),
            "supporting_evidence": verdict_data.get("supporting_evidence", []),
            "limitations": verdict_data.get("limitations", ""),
            "recommended_action": verdict_data.get("recommended_action", ""),
            "agent_execution_log": agent_log,
            "overall_status": result.get("overall_status", "unknown")
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


async def handle_save_report(arguments: dict):
    """
    Saves investigation report to local filesystem.
    This satisfies the Filesystem MCP concept.
    """
    claim = arguments.get("claim", "untitled")
    report = arguments.get("report", {})

    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "reports"
    )
    os.makedirs(reports_dir, exist_ok=True)

    # Build a clean filename from the claim
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in (' ', '-') else '_' for c in claim[:40])
    safe_name = safe_name.strip().replace(' ', '_')
    filename = f"{timestamp}_{safe_name}.json"
    filepath = os.path.join(reports_dir, filename)

    # Write full report with metadata
    full_report = {
        "metadata": {
            "claim": claim,
            "saved_at": datetime.now().isoformat(),
            "system": "Fake News Autopsy v1.0"
        },
        "report": report
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)

    return [types.TextContent(
        type="text",
        text=json.dumps({
            "status": "saved",
            "filepath": filepath,
            "filename": filename
        })
    )]


async def main():
    """Entry point — starts the MCP server over stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())