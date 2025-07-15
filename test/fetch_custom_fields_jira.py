import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv("JIRA_BASE_URL")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

INTERESTING_FIELD_NAMES = {
    "Client's name",
    "Client's country",
    "Client's project SPOC name",
    "Client's project SPOC email",
    "Partner's name",
    "Partner's country",
    "Partner's single point of contact (SPOC)",
    "Integrator's name",
    "Integrator's country",
    "Integrator's single point of contact (SPOC)",
    "Distribution Type",
    "Identity submodules",
    "Threats submodules",
    "Payments submodules",
    "Deployment type",
    "Total active users to be protected by ThreatMark",
    "Support mode",
    "Number of Test environments",
    "Signed NDA URL",
    "Expected project start date",
    "Expected go live date",
    "Project milestones",
    "CFFC services included",
    "Landing page - average impressions per day",
    "Landing page - average impressions per minute",
    "Landing page - peak impressions per day",
    "Landing page - peak impressions per minute",
    "Web apps - average impressions per day",
    "Web apps - average impressions per minute",
    "Web apps - peak impressions per day",
    "Web apps - peak impressions per minute",
    "Mobile apps - average impressions per day",
    "Mobile apps - average impressions per minute",
    "Mobile apps - peak impressions per day",
    "Mobile apps - peak impressions per minute",
    "Requested max API response time",
    "Requested data retention",
    "DR",
    "Critical priority incident - reaction time",
    "Critical priority incident - fix or workaround time",
    "High priority incident - reaction time",
    "High priority incident - fix or workaround time",
    "Medium priority incident - reaction time",
    "Medium priority incident - fix or workaround time",
    "Low priority incident - reaction time",
    "Low priority incident - fix or workaround time",
    "Security incident - reporting time",
    "Security incident - fix proposal time",
    "Security incident - fix implemented",
    "Insignificant security vulnerability - reporting time",
    "Insignificant security vulnerability - mitigating measure time",
    "Insignificant security vulnerability - fixing measure time",
    "Insignificant security vulnerability - impact analysis and measures plan",
    "Significant security vulnerability - reporting time",
    "Significant security vulnerability - mitigating measure time",
    "Significant security vulnerability - fixing measure time",
    "Significant security vulnerability - impact analysis and measures plan",
    "Other notes"
}

def fetch_field_id_name_mapping(issue_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}?expand=names"
    response = requests.get(url, auth=(EMAIL, API_TOKEN), headers={"Accept": "application/json"})
    
    if response.status_code != 200:
        print("Failed to fetch issue data")
        print(response.text)
        return {}

    data = response.json()
    names = data.get("names", {})
    
    # Match only relevant ones
    filtered = {
        field_id: field_name
        for field_id, field_name in names.items()
        if field_name in INTERESTING_FIELD_NAMES
    }

    return filtered

if __name__ == "__main__":
    issue_key = "DELPROJ-2443"
    mapping = fetch_field_id_name_mapping(issue_key)

    print("📋 Custom Field ID ↔ Field Name Mapping:\n")
    for field_id, label in sorted(mapping.items()):
        print(f"{field_id} → {label}")
