import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise RuntimeError("Missing JIRA credentials in .env")

# Authentication headers
auth = requests.auth._basic_auth_str(JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {
    "Authorization": auth,
    "Accept": "application/json"
}

# ----------------------------
# Helpers
# ----------------------------

def truncate(v, maxlen=300):
    return (v[:maxlen] + "…") if isinstance(v, str) and len(v) > maxlen else v

def extract_summary(issue_data):
    fields = issue_data.get("fields", {})
    names = issue_data.get("names", {})

    # --- Standard Jira Fields
    standard_fields = {
        "Issue Key": issue_data.get("key"),
        "Summary": fields.get("summary"),
        "Status": fields.get("status", {}).get("name"),
        "Assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
        "Created": fields.get("created"),
        "Updated": fields.get("updated"),
        "Due Date": fields.get("duedate")
    }

    # --- Custom Fields based on screenshot
    relevant_keywords = [
        # General tab
        "use case", "requirement", "notes", "contact", "license",
        "parameter", "cfc", "traffic", "data retention", "sla",

        # Contacts tab
        "client", "partner", "integrator", "spoc", "country", "email", "name",

        # License tab
        "distribution", "deployment", "support mode", "test environment",
        "active users", "identity submodules", "threats submodules", "payments submodules",

        # Project Parameters tab
        "start date", "go live", "nda", "milestones", "project parameters",

        # CFFC tab
        "cffc", "cffc services",

        # Channels & traffic tab
        "landing page", "web apps", "mobile apps", "impressions", "integration",
        "api response", "channels", "traffic",

        # Data Retention tab
        "data retention", "retention", "dr",

        # SLA tab
        "reaction time", "fix time", "workaround", "incident", "vulnerability",
        "reporting time", "mitigating measure", "fixing measure", "impact analysis",

        # Other tab
        "other notes", "other"
    ]



    custom_fields = {}
    for k, v in fields.items():
        if k.startswith("customfield_") and v is not None:
            field_name = names.get(k, k).lower()
            if any(kw in field_name for kw in relevant_keywords):
                readable_name = names.get(k, k)
                custom_fields[readable_name] = truncate(v)

    # --- Linked Issues
    links = fields.get("issuelinks", [])
    linked_issues = []
    for link in links:
        issue = link.get("outwardIssue") or link.get("inwardIssue")
        if issue:
            linked_issues.append({
                "key": issue.get("key"),
                "summary": issue.get("fields", {}).get("summary"),
                "status": issue.get("fields", {}).get("status", {}).get("name")
            })

    return {
        "standard": standard_fields,
        "custom_fields": custom_fields,
        "linked_issues": linked_issues
    }

# ----------------------------
# Main
# ----------------------------

if __name__ == "__main__":
    issue_key = "DELPROJ-2443"
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}?expand=names"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        issue_data = response.json()
        summary = extract_summary(issue_data)
        print(json.dumps(summary, indent=2))
    else:
        print(f"❌ Failed to fetch issue. Status: {response.status_code}")
        print(response.text)
