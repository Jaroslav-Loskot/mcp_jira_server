import asyncio
from dotenv import load_dotenv
import os
from fastmcp.client import Client

load_dotenv(override=True)

SERVER_URL = "http://127.0.0.1:8001/sse/"
TEST_PROJECT_KEY = "DELPROJ"  # Replace with a valid project key in your Jira


async def test_get_project_statuses():
    print(f"\n🔌 Connecting to MCP server at {SERVER_URL}...\n")

    try:
        async with Client(SERVER_URL) as client:
            print("✅ Connected.\n")

            print(f"▶️ Calling `get_project_statuses` with project key: '{TEST_PROJECT_KEY}'")
            result = await client.call_tool("get_project_statuses", {"project_key": TEST_PROJECT_KEY})
            statuses_by_type = result.structured_content

            print("\n📋 Available Statuses by Issue Type:")
            for issue_type, statuses in statuses_by_type.items():
                print(f" - {issue_type}: {statuses}")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")

    print("\n✅ Test completed.\n")


if __name__ == "__main__":
    asyncio.run(test_get_project_statuses())
