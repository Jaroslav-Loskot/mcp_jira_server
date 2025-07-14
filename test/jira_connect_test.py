import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the root directory (parent of current file)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

print(f"JIRA_BASE_URL={JIRA_BASE_URL}")
print(f"JIRA_EMAIL={JIRA_EMAIL}")
print(f"JIRA_API_TOKEN={JIRA_API_TOKEN}")


def check_credentials():
    if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        print("❌ Missing one or more environment variables.")
        return

    headers = {
        "Authorization": f"Basic {requests.auth._basic_auth_str(JIRA_EMAIL, JIRA_API_TOKEN)}",
        "Accept": "application/json"
    }

    # Simple test: Get your user info
    url = f"{JIRA_BASE_URL}/rest/api/3/myself"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Jira credentials are valid. Logged in as: {data['displayName']}")
    else:
        print(f"❌ Failed to authenticate. Status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    check_credentials()
