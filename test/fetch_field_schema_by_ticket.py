import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

HEADERS = {
    "Authorization": requests.auth._basic_auth_str(JIRA_EMAIL, JIRA_API_TOKEN),
    "Accept": "application/json"
}


def get_issue(issue_key: str) -> dict:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        raise Exception(f"❌ Failed to fetch issue: {resp.status_code}\n{resp.text}")
    return resp.json()


def get_field_definitions(project_key: str, issue_type_name: str) -> dict:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/createmeta"
    params = {
        "projectKeys": project_key,
        "expand": "projects.issuetypes.fields"
    }

    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        raise Exception(f"❌ Failed to fetch field definitions: {resp.status_code}\n{resp.text}")

    data = resp.json()
    for project in data.get("projects", []):
        for issue_type in project.get("issuetypes", []):
            if issue_type["name"].lower() == issue_type_name.lower():
                return issue_type["fields"]

    raise Exception("❌ No matching issue type found.")


def dump_customfield_values(issue_data: dict, field_defs: dict):
    print("\n📋 Custom Fields with Values:")
    fields = issue_data.get("fields", {})

    for field_id, value in fields.items():
        if not field_id.startswith("customfield_"):
            continue
        if isinstance(value, (str, int)) and value:
            field_info = field_defs.get(field_id, {})
            field_name = field_info.get("name", "❓ Unknown")
            field_type = field_info.get("schema", {}).get("type", "❓")
            print(f"{field_id} → {field_name}: {value} ({field_type})")
        elif isinstance(value, dict) and "value" in value:
            field_info = field_defs.get(field_id, {})
            field_name = field_info.get("name", "❓ Unknown")
            field_type = field_info.get("schema", {}).get("type", "❓")
            print(f"{field_id} → {field_name}: {value['value']} ({field_type})")


if __name__ == "__main__":
    issue_key = "DELTP-7867"
    issue_data = get_issue(issue_key)
    project_key = issue_data["fields"]["project"]["key"]
    issue_type = issue_data["fields"]["issuetype"]["name"]

    print(f"✅ Project: {project_key} | Issue Type: {issue_type}")

    field_defs = get_field_definitions(project_key, issue_type)
    dump_customfield_values(issue_data, field_defs)
