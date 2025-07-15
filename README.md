# 🧠 MCP Jira Server

A powerful, modular, and extendable FastAPI-based server for interacting with Jira using a Model Context Protocol (MCP). It enables intelligent querying, retrieval, and modification of Jira tickets using structured or natural language inputs. Built with LLM integration in mind (Claude via Amazon Bedrock).

---

## 🚀 Features

* 🔍 Query Jira issues with structured filters or natural language.
* 📟 Get full ticket details including comments, status, and assignee.
* 🏗️ Fetch project-level metadata: statuses, priorities, issue types.
* 📊 Retrieve and update "Project Charter" custom fields via LLM-assisted interpretation.
* ⚙️ Automatically map user instructions to Jira field schema and values.
* 📦 Designed to run in Docker and be consumed as an API endpoint.

---

## 📁 Project Structure

```
├── main.py                      # Entry point for FastAPI application
├── services/                   # Business logic and service layer
│   ├── field_mapping.py        # Mapping from human field names to Jira customfield IDs
│   ├── field_formatting.py     # Field schema-aware value formatting
│   ├── jira_metadata_service.py
│   ├── project_charter_service.py
│   └── get_custom_fields.py
├── utils/                      # Bedrock + embeddings helpers
│   ├── bedrock_wrapper.py
│   ├── generate_field_embeddings.py
│   └── field_embeddings.json
├── test/                       # Integration test scripts + REST Client requests
├── .env                        # Jira and AWS credentials
├── Dockerfile                  # Container image setup
├── docker-compose.yml          # Local dev environment
└── requirements.txt
```

---

## ⚙️ Setup

### 1. Clone and configure

```bash
git clone https://github.com/your-org/mcp-jira-server.git
cd mcp-jira-server
cp .env.example .env
```

Populate `.env` with:

```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your-jira-api-token

AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=...
BEDROCK_MODEL_ID=eu.anthropic.claude-3-7-sonnet-20250219-v1:0
BEDROCK_INFERENCE_CONFIG_ARN=...
```

---

### 2. Run locally with Docker

```bash
docker-compose up --build
```

Once started:

* API root: [http://localhost:8000](http://localhost:8000)
* Health check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🤖 Supported MCP Intents

### `get_jira_issues`

Retrieve issues with flexible filtering:

```json
{
  "user": "jaroslav",
  "intent": "get_jira_issues",
  "parameters": {
    "project": ["AFS"],
    "priority": ["High"],
    "created_after": "-1w",
    "only_count": false
  }
}
```

---

### `get_ticket_details`

Get detailed ticket info:

```json
{
  "user": "jaroslav",
  "intent": "get_ticket_details",
  "parameters": {
    "ticket": "AFS-123"
  }
}
```

---

### `get_jira_projects`

List all accessible projects:

```json
{
  "user": "jaroslav",
  "intent": "get_jira_projects",
  "parameters": {}
}
```

---

### `get_project_metadata`

Fetch metadata (statuses, priorities, issue types):

```json
{
  "user": "jaroslav",
  "intent": "get_project_metadata",
  "parameters": {
    "project": "AFS"
  }
}
```

---

### `get_project_charter`

Summarize key custom fields from a Jira ticket:

```json
{
  "user": "jaroslav",
  "intent": "get_project_charter",
  "parameters": {
    "ticket": "DELPROJ-2443"
  }
}
```

---

### `update_project_charter`

Update a Jira ticket’s custom field using natural language:

```json
{
  "user": "jaroslav",
  "intent": "update_project_charter",
  "parameters": {
    "ticket": "DELTP-7867",
    "update_instruction": "Remove the project start date"
  }
}
```

---

## 🧪 Testing

Use the [REST Client VS Code extension](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) and `.rest` files from `/test/`:

Example:

```http
POST http://localhost:8000/jira/query
Content-Type: application/json

{
  "user": "jaroslav",
  "intent": "get_ticket_details",
  "parameters": {
    "ticket": "AFS-123"
  }
}
```

---

## 🧠 LLM + Embedding

* Claude is used via Amazon Bedrock for interpreting update instructions.
* Titan embeddings are used for semantic search and field similarity.
* Run `python utils/generate_field_embeddings.py` to regenerate `field_embeddings.json`.

---

## 📃 License

MIT (or internal enterprise use only).
