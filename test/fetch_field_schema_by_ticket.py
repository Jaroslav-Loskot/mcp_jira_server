import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

HEADERS = {
    "Authorization": requests.auth._basic_auth_str(JIRA_EMAIL, JIRA_API_TOKEN),
    "Accept": "application/json"
}


def get_issue_metadata(issue_key: str):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        raise Exception(f"❌ Failed to fetch issue: {resp.status_code}\n{resp.text}")

    data = resp.json()
    project_key = data["fields"]["project"]["key"]
    issue_type_name = data["fields"]["issuetype"]["name"]

    print(f"✅ Project: {project_key} | Issue Type: {issue_type_name}")
    return project_key, issue_type_name


def get_field_definitions(project_key: str, issue_type_name: str):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/createmeta"
    params = {
        "projectKeys": project_key,
        "expand": "projects.issuetypes.fields"
    }

    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        raise Exception(f"❌ Failed to fetch create metadata: {resp.status_code}\n{resp.text}")

    data = resp.json()
    for project in data.get("projects", []):
        for issue_type in project.get("issuetypes", []):
            if issue_type["name"].lower() == issue_type_name.lower():
                return issue_type["fields"]

    raise Exception("❌ No matching issue type found.")


if __name__ == "__main__":
    issue_key = "DELTP-7867"  # Change this to your actual issue key
    project_key, issue_type = get_issue_metadata(issue_key)
    field_defs = get_field_definitions(project_key, issue_type)

    print("\n📋 Custom Fields:")
    for fid, info in field_defs.items():
        if fid.startswith("customfield_"):
            name = info.get("name")
            schema = info.get("schema", {})
            print(f"{fid} → {name} ({schema.get('type')})")
