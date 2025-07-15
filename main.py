from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import os
from typing import List, Optional, Union
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pathlib import Path
import base64
from services.project_charter_service import update_project_charter_field
from services.field_mapping import FIELD_LABEL_TO_ID



# Load .env from root directory
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise RuntimeError("❌ Missing one or more required environment variables (JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)")

# Generate Authorization header
auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
b64_auth = base64.b64encode(auth_str.encode()).decode()
HEADERS = {
    "Authorization": f"Basic {b64_auth}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

app = FastAPI()

class MCPQuery(BaseModel):
    user: str
    intent: str
    parameters: dict
    natural_language: Optional[str] = None

class JiraIssue(BaseModel):
    key: str
    summary: str
    status: str
    assignee: Optional[str] = None
    url: str

from datetime import datetime, timedelta
import re

def parse_relative_date(relative_str: str) -> Optional[str]:
    match = re.fullmatch(r"-([0-9]+)([dwmyh])", relative_str.strip())
    if not match:
        return None

    value, unit = int(match.group(1)), match.group(2)
    now = datetime.utcnow()

    if unit == "d":
        dt = now - timedelta(days=value)
    elif unit == "w":
        dt = now - timedelta(weeks=value)
    elif unit == "m":
        dt = now - timedelta(days=value * 30)
    elif unit == "y":
        dt = now - timedelta(days=value * 365)
    elif unit == "h":
        dt = now - timedelta(hours=value)
    else:
        return None

    return dt.strftime("%Y-%m-%d")



@app.post("/jira/query")
async def mcp_query(query: MCPQuery):
    if query.intent == "get_jira_issues":
        project = query.parameters.get("project")
        status_list = query.parameters.get("status", [])
        assignee = query.parameters.get("assignee")
        priority = query.parameters.get("priority")
        issue_type = query.parameters.get("issueType")
        labels = query.parameters.get("labels")
        created_after = query.parameters.get("created_after")
        created_before = query.parameters.get("created_before")
        only_count = query.parameters.get("only_count", False)
        result_limit = query.parameters.get("limit", None)
        raw_jql = query.parameters.get("jql")

        def to_list(val):
            if isinstance(val, list):
                return val
            elif isinstance(val, str):
                return [val]
            return []

        if raw_jql:
            jql = raw_jql
        else:
            jql_parts = []

        if project:
            projects = to_list(project)
            jql_parts.append("project in (" + ",".join(f'"{p}"' for p in projects) + ")")

        if assignee:
            assignees = to_list(assignee)
            jql_parts.append("assignee in (" + ",".join(f'"{a}"' for a in assignees) + ")")

        if status_list:
            statuses = to_list(status_list)
            jql_parts.append("status in (" + ",".join(f'"{s}"' for s in statuses) + ")")

        if priority:
            priorities = to_list(priority)
            jql_parts.append("priority in (" + ",".join(f'"{p}"' for p in priorities) + ")")

        if issue_type:
            types = to_list(issue_type)
            jql_parts.append("issuetype in (" + ",".join(f'"{t}"' for t in types) + ")")

        if labels:
            label_list = to_list(labels)
            jql_parts.append("labels in (" + ",".join(f'"{l}"' for l in label_list) + ")")


        if created_after:
            parsed_after = parse_relative_date(created_after) or created_after
            jql_parts.append(f'created >= "{parsed_after}"')

        if created_before:
            parsed_before = parse_relative_date(created_before) or created_before
            jql_parts.append(f'created <= "{parsed_before}"')


        jql = " AND ".join(jql_parts)

        all_issues = []
        start_at = 0
        max_results = 50
        total = None

        while total is None or start_at < total:
            response = requests.get(
                f"{JIRA_BASE_URL}/rest/api/3/search",
                headers=HEADERS,
                params={
                    "jql": jql,
                    "fields": "summary,status,assignee",
                    "startAt": start_at,
                    "maxResults": max_results
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch Jira issues")

            result_json = response.json()
            total = result_json.get("total", 0)
            issues = result_json.get("issues", [])
            all_issues.extend(issues)
            start_at += max_results

            if result_limit is not None and len(all_issues) >= result_limit:
                all_issues = all_issues[:result_limit]
                break

        if only_count:
            return JSONResponse(content={
                "status": "success",
                "count": len(all_issues),
                "message": f"{len(all_issues)} issues matched your criteria."
            })

        result = []
        for issue in all_issues:
            fields = issue["fields"]
            result.append(JiraIssue(
                key=issue["key"],
                summary=fields["summary"],
                status=fields["status"]["name"],
                assignee=fields["assignee"]["displayName"] if fields.get("assignee") else None,
                url=f"{JIRA_BASE_URL}/browse/{issue['key']}"
            ))

        return JSONResponse(content={
            "status": "success",
            "data": [r.dict() for r in result],
            "total": len(result),
            "message": f"{len(result)} issues returned in total."
        })

    elif query.intent == "get_jira_projects":
        response = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/project",
            headers=HEADERS
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch Jira projects")

        projects = response.json()
        data = [
            {
                "key": project["key"],
                "name": project["name"],
                "id": project["id"],
                "url": f"{JIRA_BASE_URL}/browse/{project['key']}"
            }
            for project in projects
        ]

        return JSONResponse(content={
            "status": "success",
            "data": data,
            "message": f"{len(data)} projects found."
        })

    elif query.intent == "get_project_metadata":
        project_key = query.parameters.get("project")
        if not project_key:
            raise HTTPException(status_code=400, detail="Missing 'project' parameter")

        metadata = {"project": project_key}

        # Fetch statuses
        status_resp = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/project/{project_key}/statuses",
            headers=HEADERS
        )
        if status_resp.status_code == 200:
            statuses_data = status_resp.json()
            status_names = set()
            for wf in statuses_data:
                for s in wf.get("statuses", []):
                    status_names.add(s["name"])
            metadata["statuses"] = sorted(status_names)
        else:
            metadata["statuses"] = []

        # Fetch priorities
        priority_resp = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/priority",
            headers=HEADERS
        )
        if priority_resp.status_code == 200:
            priorities = priority_resp.json()
            metadata["priorities"] = [p["name"] for p in priorities]
        else:
            metadata["priorities"] = []

        # Fetch issue types
        issue_type_resp = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/project/{project_key}",
            headers=HEADERS
        )
        if issue_type_resp.status_code == 200:
            project_data = issue_type_resp.json()
            metadata["issueTypes"] = [t["name"] for t in project_data.get("issueTypes", [])]
        else:
            metadata["issueTypes"] = []

        return JSONResponse(content={
            "status": "success",
            "data": metadata
        })
    
    elif query.intent == "get_ticket_details":
        issue_key = query.parameters.get("ticket")
        if not issue_key:
            raise HTTPException(status_code=400, detail="Missing 'ticket' parameter")

        issue_resp = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}",
            headers=HEADERS,
            params={"fields": "summary,status,assignee,comment"}
        )

        if issue_resp.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")

        issue_data = issue_resp.json()
        fields = issue_data.get("fields", {})
        comments_raw = fields.get("comment", {}).get("comments", [])

        def extract_text(body):
            if isinstance(body, dict) and body.get("type") == "doc":
                paragraphs = []
                for block in body.get("content", []):
                    if block.get("type") == "paragraph":
                        texts = [span.get("text", "") for span in block.get("content", []) if span.get("type") == "text"]
                        paragraphs.append("".join(texts))
                return "\n".join(paragraphs)
            return str(body)

        comments = [{
            "author": c["author"]["displayName"],
            "created": c["created"],
            "text": extract_text(c["body"])
        } for c in comments_raw]

        return JSONResponse(content={
            "status": "success",
            "ticket": issue_key,
            "summary": fields.get("summary"),
            "status_name": fields.get("status", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            "comments": comments,
            "url": f"{JIRA_BASE_URL}/browse/{issue_key}"
        })

    elif query.intent == "get_project_charter":
        issue_key = query.parameters.get("ticket")
        if not issue_key:
            raise HTTPException(status_code=400, detail="Missing 'ticket' parameter")

        issue_resp = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}",
            headers=HEADERS,
            params={"expand": "names"}
        )

        if issue_resp.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")

        issue_data = issue_resp.json()
        fields = issue_data.get("fields", {})
        names = issue_data.get("names", {})

        standard_fields = {
            "Issue Key": issue_data.get("key"),
            "Summary": fields.get("summary"),
            "Status": fields.get("status", {}).get("name"),
            "Assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            "Created": fields.get("created"),
            "Updated": fields.get("updated"),
            "Due Date": fields.get("duedate")
        }

        def format_field(value):
            if isinstance(value, dict) and "value" in value:
                return value["value"]
            elif isinstance(value, list):
                return [v.get("value", str(v)) for v in value if isinstance(v, dict)]
            return value

        interesting_customfields = set(FIELD_LABEL_TO_ID.values())

        custom_fields = {
            names.get(fid, fid): format_field(fields[fid])
            for fid in interesting_customfields
            if fid in fields and fields[fid] is not None
        }

        return JSONResponse(content={
            "status": "success",
            "ticket": issue_key,
            "summary_fields": {**standard_fields, **custom_fields},
            "url": f"{JIRA_BASE_URL}/browse/{issue_key}"
        })

    elif query.intent == "update_project_charter":
        ticket_key = query.parameters.get("ticket")
        message = query.parameters.get("update_instruction")

        if not ticket_key or not message:
            raise HTTPException(status_code=400, detail="Missing 'ticket' or 'update_instruction' parameter")

        result = update_project_charter_field(ticket_key, message)
        return JSONResponse(content=result)

    raise HTTPException(status_code=400, detail="Unsupported intent")

@app.get("/")
async def root():
    return {"message": "MCP Jira Server is running."}

@app.get("/health")
async def health():
    return {"status": "ok"}