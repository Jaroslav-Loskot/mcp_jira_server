import asyncio
import os
from dotenv import load_dotenv
from fastmcp.client import Client

load_dotenv(override=True)

SERVER_URL = "http://127.0.0.1:8001/sse/"
EXAMPLE_ISSUE_KEY = "DELTP-7867"
EXAMPLE_JQL = f'key = "{EXAMPLE_ISSUE_KEY}"'
EXAMPLE_PROJECT_KEY = "DELTP"

EXAMPLE_INPUTS = {
    "get_issue": {"key": EXAMPLE_ISSUE_KEY},
    "get_issue_with_comments": {"key": EXAMPLE_ISSUE_KEY},
    "get_available_issue_statuses": {"key": EXAMPLE_ISSUE_KEY},
    "search_issues": {"jql": EXAMPLE_JQL},
    "search_advanced_issues": {
        "projects": [],
        "statuses": [],
        "priorities": [],
        "assignees": [],
        "created_after": "",
        "updated_after": "",
        "max_results": 2,
        "sort_by": "created",
        "sort_order": "DESC"
    },
    "list_projects": {}, 
    "resolve_project_key": {"human_input" : "UniCredit Italy"},
    "parse_jira_date" : {"input_str" : "1 JUL 2025"}
}

async def test_all_mcp_tools():
    print(f"Connecting to MCP server at {SERVER_URL}...\n")

    results = []

    try:
        async with Client(SERVER_URL) as client:
            print("✅ Connected to MCP server.\n")

            tools = await client.list_tools()
            print(f"🔧 Available tools: {[tool.name for tool in tools]}\n")

            for tool in tools:
                tool_name = tool.name
                input_data = EXAMPLE_INPUTS.get(tool_name, {})

                print(f"▶️ Testing `{tool_name}` with input: {input_data}")
                try:
                    result = await client.call_tool(tool_name, input_data)
                    print(f"   ✅ Success. Output summary: {str(result.structured_content)[:200]}...\n")
                    results.append((tool_name, "✅ Success"))
                except Exception as e:
                    print(f"   ❌ Error calling `{tool_name}`: {e}\n")
                    results.append((tool_name, f"❌ {e}"))

    except Exception as e:
        print(f"\n🚨 Failed to connect to server or fetch tools: {e}")
        return

    # Summary report
    print("\n📊 Test Summary:")
    for name, status in results:
        print(f" - {name:30}: {status}")

if __name__ == "__main__":
    asyncio.run(test_all_mcp_tools())
