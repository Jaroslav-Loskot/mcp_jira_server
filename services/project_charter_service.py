import json
import logging
import os
import re
import requests
from dotenv import load_dotenv
from typing import Optional
from services.field_mapping import FIELD_LABEL_TO_ID
from utils.bedrock_wrapper import call_claude
from services.jira_metadata_service import get_field_definitions, get_issue_metadata
from services.field_formatting import format_value_for_field, resolve_field_id_fuzzy


from difflib import get_close_matches
from services.jira_metadata_service import get_issue_details  # or the correct module where it's defined


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
    # Step 1: LLM parses the instruction
    parsed = parse_charter_update_with_claude(message)
    if "error" in parsed:
        return {"status": "error", "message": parsed["error"]}

    user_label = parsed.get("field_label", "").strip()
    new_value = parsed.get("value")
    action = parsed.get("action", "replace").lower()  # default to replace

    if not user_label or "value" not in parsed:
        return {"status": "error", "message": "Missing field label or value."}


    # Step 2: Fuzzy match the user label to field_id
    match = resolve_field_id_fuzzy(user_label, message)
    if not match:
        return {"status": "error", "message": f"No matching field found for '{user_label}'."}

    matched_label, field_id = match

    # Step 3: Get metadata and schema
    try:
        project_key, issue_type = get_issue_metadata(ticket_key)
        field_defs = get_field_definitions(project_key, issue_type)

        logging.info(f"🔧 Looking up field schema for field_id: {field_id}")
        logging.info(f"All field definitions keys: {list(field_defs.keys())}")

        field_schema = field_defs.get(field_id)
        if not field_schema:
            return {"status": "error", "message": f"Could not find field schema for {field_id}."}
    except Exception as e:
        return {"status": "error", "message": f"Metadata lookup failed: {str(e)}"}

    # Step 4: For array fields, get current value from issue
    try:
        current_values = []
        if field_schema.get("schema", {}).get("type") == "array":
            issue_details = get_issue_details(ticket_key)
            current_raw = issue_details["fields"].get(field_id, [])
            current_values = [v["value"] for v in current_raw if isinstance(v, dict) and "value" in v]
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch current values: {str(e)}"}

    # Step 5: Format value with context (including current values if array field)
    try:
        formatted_value = format_value_for_field(
            field_schema=field_schema,
            value=new_value,
            current_values=current_values,
            action=action
        )
        print(f"INFO: formatted_value type: {type(formatted_value)}, value: {formatted_value}")
    except ValueError as ve:
        return {"status": "error", "message": str(ve)}

    # Extract final resolved value for logging/response
    if isinstance(formatted_value, dict) and "value" in formatted_value:
        resolved_value = formatted_value["value"]
    elif isinstance(formatted_value, list) and all(isinstance(i, dict) and "value" in i for i in formatted_value):
        resolved_value = [i["value"] for i in formatted_value]
    else:
        resolved_value = formatted_value

    # Step 6: Build update payload
    payload = {
        "fields": {
            field_id: formatted_value
        }
    }

    print(f"Updating {field_id} with: {json.dumps(payload, indent=2)}")

    response = requests.put(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{ticket_key}",
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers=HEADERS,
        json=payload
    )

    if response.status_code != 204:
        return {
            "status": "error",
            "message": f"Jira update failed with status code {response.status_code}",
            "jira_response": response.text
        }

    return {
        "status": "success",
        "ticket": ticket_key,
        "field_label": matched_label,
        "field_id": field_id,
        "new_value": resolved_value,
        "action": action,
        "message": f"Field '{matched_label}' ({field_id}) updated via '{action}' successfully."
    }



import json
import re

def parse_charter_update_with_claude(instruction: str) -> dict:
    system_prompt = """
You are an assistant that parses user instructions for updating Jira project charters.

Given a natural language instruction like:
- "Set expected go-live date to 12-12-2026"
- "Add CFFC service, Phishing detection"
- "Remove Brand Abuse Mitigation from CFFC"
- "Change support mode to L1+L2"
- "Clear the project start date"

Your task is to extract:
1. `field_label` — name of the field being updated
2. `value` — the new value (can be a string, list, or `null`)
3. `action` — one of "replace", "add", or "remove"

Return **only** a JSON object in this format:
```json
{
  "field_label": "cffc services included",
  "value": ["Phishing detection"],
  "action": "add"
}
Rules:

Use "add" if the instruction says things like "add", "include", "append", or "also".

Use "remove" if it says "remove", "delete", "exclude".

Use "replace" for set/change/update/modify.

If the instruction is about clearing or emptying a field, set value to null and use "replace" as the action.

Be strict about outputting valid JSON only.
"""

    raw_response = call_claude(system_prompt, instruction)

    logging.info(f"📥 LLM raw response: {raw_response}")


    try:
        # Strip markdown block formatting if present
        match = re.search(r'{.*}', raw_response, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in Claude response")

        cleaned = match.group(0)
        return json.loads(cleaned)

    except Exception as e:
        return {"error": f"Failed to parse Claude response: {e}", "raw": raw_response}
