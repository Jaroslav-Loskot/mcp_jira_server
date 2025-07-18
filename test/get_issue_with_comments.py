import asyncio
import os
from dotenv import load_dotenv
from fastmcp.client import Client

load_dotenv(override=True)

SERVER_URL = "http://127.0.0.1:8001/sse/"
EXAMPLE_ISSUE_KEY = "DELPROJ-2443"  # <-- Replace with another key if needed

async def test_get_issue_with_comments():
    print(f"Connecting to MCP server at {SERVER_URL}...\n")

    try:
        async with Client(SERVER_URL) as client:
            print("✅ Connected to MCP server.\n")

            print(f"▶️ Calling `get_issue_with_comments` for issue `{EXAMPLE_ISSUE_KEY}`...")
            result = await client.call_tool("get_issue_with_comments", {"key": EXAMPLE_ISSUE_KEY})

            issue = result.structured_content
            print("\n📋 Issue Details:")
            print(f"Key      : {issue.get('key')}")
            print(f"Summary  : {issue.get('summary')}")
            print(f"Status   : {issue.get('status')}")
            print(f"Priority : {issue.get('priority')}")
            print(f"Assignee : {issue.get('assignee')}")
            print(f"Created  : {issue.get('created')}")
            print(f"Updated  : {issue.get('updated')}")
            print(f"Type     : {issue.get('task_type')}")

            print("\n💬 Comments:")
            comments = issue.get("comments", [])
            if comments:
                for idx, comment in enumerate(comments, start=1):
                    print(f"  {idx}. {comment}")
            else:
                print("  No comments found.")

    except Exception as e:
        print(f"\n❌ Error during tool call: {e}")

    print("\n✅ Test completed.")

if __name__ == "__main__":
    asyncio.run(test_get_issue_with_comments())
