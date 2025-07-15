import os
import re
import requests
from dotenv import load_dotenv
from typing import Optional
from services.field_mapping import FIELD_LABEL_TO_ID


load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
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
