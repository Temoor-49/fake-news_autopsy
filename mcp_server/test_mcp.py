# mcp_server/test_mcp.py
# Tests the MCP server's tool functionality directly
# without needing a full MCP client like Claude Desktop

import sys
import os
import json
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test the underlying handlers directly
# (same logic the MCP server calls, without the protocol overhead)
from mcp_server.investigation_server import handle_investigate, handle_save_report


async def test_investigate():
    print("=" * 60)
    print("🧪 TESTING MCP: investigate_claim tool")
    print("=" * 60)

    result = await handle_investigate({
        "claim": "COVID-19 vaccines contain microchips"
    })

    # result is a list of TextContent objects
    response_text = result[0].text
    response_data = json.loads(response_text)

    print(f"\n✅ Tool returned successfully")
    print(f"VERDICT: {response_data.get('verdict')}")
    print(f"CONFIDENCE: {response_data.get('confidence_score')}/100")
    print(f"SUMMARY: {response_data.get('one_line_summary')}")
    print(f"\nAGENT LOG:")
    for entry in response_data.get("agent_execution_log", []):
        icon = "✅" if entry["status"] == "success" else "❌"
        print(f"  {icon} {entry['agent']}: {entry['duration_seconds']}s")

    return response_data


async def test_save_report(report_data: dict):
    print("\n" + "=" * 60)
    print("🧪 TESTING MCP: save_report tool")
    print("=" * 60)

    result = await handle_save_report({
        "claim": "COVID-19 vaccines contain microchips",
        "report": report_data
    })

    response_text = result[0].text
    response_data = json.loads(response_text)

    print(f"\n✅ Report saved successfully")
    print(f"File: {response_data.get('filename')}")
    print(f"Path: {response_data.get('filepath')}")

    return response_data


async def main():
    # Test investigate_claim tool
    report = await test_investigate()

    # Test save_report tool with the result
    await test_save_report(report)

    print("\n" + "=" * 60)
    print("✅ ALL MCP TOOLS WORKING")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())