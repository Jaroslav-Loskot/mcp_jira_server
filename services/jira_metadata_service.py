import requests
import os
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
    """Returns (project_key, issue_type_name) for a given issue."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        raise Exception(f"❌ Failed to fetch issue: {resp.status_code}\n{resp.text}")

    data = resp.json()
    project_key = data["fields"]["project"]["key"]
    issue_type_name = data["fields"]["issuetype"]["name"]
    return project_key, issue_type_name


def get_field_definitions(project_key: str, issue_type_name: str) -> dict:
    """Returns full field metadata for the project and issue type."""
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


def get_issue_details(issue_key: str) -> dict:

    response = requests.get(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}",
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers=HEADERS,
    )
    if response.status_code != 200:
        raise Exception(f"Failed to fetch issue details: {response.status_code}, {response.text}")
    return response.json()