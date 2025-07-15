import os
import re
import requests
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Mapping of plain-language labels to custom field IDs
# Mapping of plain-language labels to custom field IDs
FIELD_LABEL_TO_ID = {
    "deployment type": "customfield_10149",
    "project start date": "customfield_10150",
    "expected project start date": "customfield_10150",
    "go live date": "customfield_10151",
    "expected go live date": "customfield_10151",
    "cffc services included": "customfield_10154",
    
    "web impressions per day": "customfield_10158",
    "web impressions per minute": "customfield_10159",
    "web peak impressions per day": "customfield_10160",
    "web peak impressions per minute": "customfield_10161",
    
    "distribution type": "customfield_10176",
    
    "landing page impressions per day": "customfield_10184",
    "landing page impressions per minute": "customfield_10185",
    "landing page peak impressions per day": "customfield_10186",
    "landing page peak impressions per minute": "customfield_10187",
    
    "mobile impressions per day": "customfield_10188",
    "mobile impressions per minute": "customfield_10189",
    "mobile peak impressions per day": "customfield_10190",
    "mobile peak impressions per minute": "customfield_10191",
    
    "requested max api response time": "customfield_10192",
    
    "number of protected users": "customfield_10193",
    "total active users to be protected by threatmark": "customfield_10193",
    
    "requested data retention": "customfield_10195",
    "dr": "customfield_10199",
    "other notes": "customfield_10200",
    "support mode": "customfield_10201",
    "project milestones": "customfield_10204",
    
    "identity submodules": "customfield_10208",
    "threats submodules": "customfield_10209",
    "payments submodules": "customfield_10210",
    
    "signed nda url": "customfield_10238",
    "nda url": "customfield_10238",
    
    "number of test environments": "customfield_10240",
    
    "critical priority reaction time": "customfield_10248",
    "high priority reaction time": "customfield_10249",
    "medium priority reaction time": "customfield_10250",
    "low priority reaction time": "customfield_10251",
    
    "security incident reporting time": "customfield_10252",
    
    "critical priority fix time": "customfield_10253",
    "high priority fix time": "customfield_10254",
    "medium priority fix time": "customfield_10255",
    "low priority fix time": "customfield_10256",
    
    "security incident fix proposal time": "customfield_10257",
    
    "significant vulnerability mitigating time": "customfield_10258",
    "insignificant vulnerability mitigating time": "customfield_10259",
    "significant vulnerability fixing time": "customfield_10260",
    "insignificant vulnerability fixing time": "customfield_10261",
    
    "security incident fix implemented": "customfield_10262",
    
    "insignificant vulnerability reporting time": "customfield_10263",
    "insignificant vulnerability analysis plan": "customfield_10264",
    
    "significant vulnerability reporting time": "customfield_10265",
    "significant vulnerability analysis plan": "customfield_10266",
}

def resolve_field_id_from_message(message: str) -> Optional[str]:
    message = message.lower()
    for label, fid in FIELD_LABEL_TO_ID.items():
        if label in message:
            return fid
    return None

def extract_value_from_message(message: str) -> Optional[str]:
    message = message.strip()
    number_match = re.search(r"\bto (\d+)", message)
    quote_match = re.search(r'"([^"]+)"', message)

    if number_match:
        return int(number_match.group(1))
    elif quote_match:
        return quote_match.group(1)
    return None

def update_project_charter_field(ticket_key: str, message: str) -> dict:
    field_id = resolve_field_id_from_message(message)
    if not field_id:
        return {"status": "error", "message": "Could not resolve target field from input."}

    new_value = extract_value_from_message(message)
    if new_value is None:
        return {"status": "error", "message": "Could not extract new value from input."}

    payload = {
        "fields": {
            field_id: new_value
        }
    }

    response = requests.put(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{ticket_key}",
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers=HEADERS,
        json=payload
    )

    if response.status_code != 204:
        return {
            "status": "error",
            "message": f"Jira update failed: {response.status_code}",
            "jira_response": response.text
        }

    return {
        "status": "success",
        "field_id": field_id,
        "new_value": new_value,
        "message": f"Field {field_id} updated successfully"
    }
