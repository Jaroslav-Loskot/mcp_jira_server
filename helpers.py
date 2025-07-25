from dataclasses import dataclass
import json
import logging
import time
from typing import List, Optional
from difflib import get_close_matches
from fastapi import HTTPException
from datetime import datetime, timedelta
import re
from utils.bedrock_wrapper import call_claude  # Your Claude wrapper
from jira import JIRA  # Atlassian Python client
import os
from dotenv import load_dotenv

from utils.parse_time_range import parse_time_range_to_bounds

load_dotenv(override=True)


JIRA_URL = os.getenv("JIRA_BASE_URL")
JIRA_USER = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_USER, JIRA_TOKEN))


def get_clean_comments_from_issue(jira, issue) -> list[dict]:
    """
    Returns raw comments from a Jira issue, including author and created timestamp.
    No filtering or cleaning is applied to avoid losing useful content.
    """
    try:
        comments = jira.comments(issue)
        return [
            {
                "author": c.author.displayName,
                "created": c.created,
                "text": c.body  # raw, full comment content
            }
            for c in comments
        ]
    except Exception as e:
        return [{"error": str(e)}]


def extract_issue_fields(issue, include_comments=False, jira_client=None):
    data = {
        "key": issue.key,
        "summary": issue.fields.summary,
        "status": issue.fields.status.name,
        "priority": issue.fields.priority.name if issue.fields.priority else None,
        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
        "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
        "created": issue.fields.created,
        "updated": issue.fields.updated,
        "task_type": issue.fields.issuetype.name if issue.fields.issuetype else None,
    }

    if include_comments and jira_client is not None:
        from helpers import get_clean_comments_from_issue
        data["comments"] = get_clean_comments_from_issue(jira_client, issue)

    return data





def _resolve_project_keys(human_input: str) -> List[str]:
    """
    Resolve Jira project keys from human-friendly input using Claude.
    Returns a list of project keys.
    """

    try:
        projects = jira.projects()
        candidates = [{"key": p.key, "name": p.name} for p in projects]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira projects: {e}")

    # Fuzzy matching on project names
    name_pool = [proj["name"] for proj in candidates]
    fuzzy_names = get_close_matches(human_input, name_pool, n=10, cutoff=0.4)

    if not fuzzy_names:
        raise HTTPException(status_code=404, detail="No similar project names found.")

    filtered = [proj for proj in candidates if proj["name"] in fuzzy_names]
    options_str = "\n".join(f"- {p['name']} (key: {p['key']})" for p in filtered)

    system_prompt = (
        "You are a precise assistant that helps resolve multiple Jira project keys from user input. "
        "You are expected to return a comma-separated list of matching project keys **only**. "
        "Never explain or justify your answer. Do not return anything else."
    )

    user_input = f"""
    The user provided this input: "{human_input}"

    Here are possible project options:
    {options_str}

    From the list above, identify the project(s) referred to in the input.
    Respond with a comma-separated list of the matching project **keys only**, such as:

    ASUCIT, CFFCSDUCIT

    Do not include any other text, comments, or formatting.
    """

    answer = call_claude(system_prompt, user_input)
    selected_keys = [key.strip().upper() for key in answer.split(",") if key.strip()]

    valid_keys = [p["key"] for p in filtered]
    invalid_keys = [k for k in selected_keys if k not in valid_keys]
    if invalid_keys:
        raise HTTPException(status_code=400, detail=f"Claude returned invalid project keys: {invalid_keys}")

    return selected_keys


from datetime import datetime, timedelta
import re
import calendar

def _parse_jira_date(input_str: str) -> str:
    """
    Parses flexible date inputs into Jira-compatible YYYY-MM-DD format.

    Supports:
    - Relative keywords: today, yesterday, last week, last month, this year, etc.
    - Shorthands: -1w, -3d, -2m, -1y
    - Date strings: 2025-07-01, 07/01/2025, 1 Jul 2025, July 1, 2025, etc.
    """
    input_str = input_str.strip().lower()
    now = datetime.utcnow()

    # Handle natural keywords
    if input_str in ["today", "now"]:
        return now.strftime("%Y-%m-%d")
    if input_str == "yesterday":
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # Handle relative phrases
    if input_str == "last week":
        last_week_start = now - timedelta(days=now.weekday() + 7)
        return last_week_start.strftime("%Y-%m-%d")
    if input_str == "this week":
        this_week_start = now - timedelta(days=now.weekday())
        return this_week_start.strftime("%Y-%m-%d")

    if input_str == "last month":
        year = now.year
        month = now.month - 1
        if month == 0:
            month = 12
            year -= 1
        return datetime(year, month, 1).strftime("%Y-%m-%d")

    if input_str == "this month":
        return datetime(now.year, now.month, 1).strftime("%Y-%m-%d")

    if input_str == "last year":
        return datetime(now.year - 1, 1, 1).strftime("%Y-%m-%d")

    if input_str == "this year":
        return datetime(now.year, 1, 1).strftime("%Y-%m-%d")

    # Handle shorthands like -3d, -2w, etc.
    match = re.match(r"^-(\d+)([dwmy])$", input_str)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        delta = timedelta(days={
            "d": amount,
            "w": 7 * amount,
            "m": 30 * amount,
            "y": 365 * amount
        }[unit])
        return (now - delta).strftime("%Y-%m-%d")

    # Try parsing flexible date formats
    known_formats = [
        "%Y-%m-%d",         # 2025-07-01
        "%d/%m/%Y",         # 01/07/2025 (EU)
        "%m/%d/%Y",         # 07/01/2025 (US)
        "%d-%m-%Y",         # 01-07-2025
        "%m-%d-%Y",         # 07-01-2025
        "%d %b %Y",         # 1 Jul 2025
        "%d %B %Y",         # 1 July 2025
        "%B %d, %Y",        # July 1, 2025
        "%b %d, %Y",        # Jul 1, 2025
    ]

    for fmt in known_formats:
        try:
            parsed = datetime.strptime(input_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError(f"Unrecognized date format: '{input_str}'")


def find_existing_issue(jira: JIRA, project_key: str) -> Optional[str]:
    """
    Tries to find an existing issue in the form PROJECT_KEY-1 through PROJECT_KEY-5.

    Parameters:
    - jira: An instance of the authenticated JIRA client.
    - project_key: The Jira project key (e.g., 'DELPROJ').

    Returns:
    - The first valid issue key found (e.g., 'DELPROJ-2'), or None if none exist.
    """
    for i in range(1, 6):
        issue_key = f"{project_key}-{i}"
        try:
            jira.issue(issue_key)
            return issue_key
        except Exception:
            time.sleep(0.1)  # 100ms pause

    return None


def get_all_jira_statuses() -> List[str]:
    """
    Fetches all available Jira statuses.

    Returns:
        A list of status names (e.g. ['Open', 'In Progress', 'Resolved', 'Closed'])
    """
    try:
        statuses = jira.statuses()
        return [s.name for s in statuses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira statuses: {e}")


def get_all_jira_priorities() -> list[str]:
    """
    Fetches all available Jira priorities.
    Returns:
        A list of priority names (e.g. ['Highest', 'High', 'Medium', 'Low', 'Lowest'])
    """
    try:
        priorities = jira.priorities()
        return [p.name for p in priorities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira priorities: {e}")
    

def get_all_jira_projects() -> List[str]:
    """
    Fetches all available Jira projects.
    
    Returns:
        A list of project names (e.g. ['UCB Italy', 'SLSP', 'CAF'])
    """
    try:
        projects = jira.projects()
        return [p.name for p in projects]  # or use p.key if you want keys
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Jira projects: {e}")
    

def _generate_jql_from_input(user_input: str,) -> dict:
    allowed_projects=get_all_jira_projects()
    allowed_priorities=get_all_jira_priorities()

    system_prompt = (
        "You are a Jira assistant that converts natural language requests into structured JSON "
        "for querying Jira issues.\n\n"
        "RULES:\n"
        "- Only use the provided project keys and priorities.\n"
        "- For issue status, DO NOT use raw status names (like 'In Progress', 'To Do', etc).\n"
        "- Instead, determine the resolution type from the user input:\n"
        "   - Use 'resolution = Unresolved' for open/incomplete issues\n"
        "   - Use 'resolution != Unresolved' for closed/completed issues\n"
        "   - Omit resolution condition if the user meant 'all' issues\n"
        "- If a priority is mentioned, use it in a priority clause.\n"
        "- If no priority is mentioned, omit it.\n"
        "- If the user input includes a limit (e.g. 'top 10'), extract it as max_results.\n"
        "- If no limit is mentioned, set max_results to null.\n"
        "- Return a JSON object ONLY with these fields:\n"
        "   - jql: string\n"
        "   - max_results: integer or null\n"
        "- DO NOT include explanations or markdown, just return the JSON.\n"
    )

    user_message = f"""
User Input:
{user_input}

Allowed project keys:
{', '.join(allowed_projects)}

Allowed priorities:
{', '.join(allowed_priorities)}

Expected output format:

{{
  "jql": "<VALID_JQL_STRING>",
  "max_results": <integer or null>
}}
"""

    response = call_claude(system_prompt, user_message).strip()

    # Extract JSON
    try:
        fenced = re.search(r"\{.*\}", response, re.DOTALL)
        response_json = fenced.group(0) if fenced else response
        result = json.loads(response_json)
    except Exception as e:
        raise ValueError(f"Failed to parse Claude's JSON output: {e}\n\nRaw response:\n{response}")

    if not isinstance(result, dict) or "jql" not in result or "max_results" not in result:
        raise ValueError(f"Claude did not return a valid structure: {result}")

    return result