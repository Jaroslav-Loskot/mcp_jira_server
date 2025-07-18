import asyncio
import os
from dotenv import load_dotenv
from fastmcp.client import Client

load_dotenv(override=True)

SERVER_URL = "http://127.0.0.1:8001/sse/"
PROJECT_INPUT = "nordea project"
DATE_INPUT = "July 1, 2025"


async def test_resolve_project_key():
    print(f"\n▶️ Calling `resolve_project_key` with input: '{PROJECT_INPUT}'")
    try:
        async with Client(SERVER_URL) as client:
            result = await client.call_tool("resolve_project_key", {"human_input": PROJECT_INPUT})
            print(f"✅ Resolved Jira project key: {result.structured_content}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_parse_jira_date():
    print(f"\n▶️ Calling `parse_jira_date` with input: '{DATE_INPUT}'")
    try:
        async with Client(SERVER_URL) as client:
            result = await client.call_tool("parse_jira_date", {"input_str": DATE_INPUT})
            print(f"✅ Parsed date: {result.structured_content}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    print(f"🔌 Connecting to MCP server at {SERVER_URL}")
    await test_resolve_project_key()
    await test_parse_jira_date()
    print("\n✅ All tests completed.")


if __name__ == "__main__":
    asyncio.run(main())
