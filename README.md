# MCP Jira Server

A lightweight FastAPI-based server for connecting to your Jira account using a Model Context Protocol (MCP) interface.

## 🚀 Features

* Query Jira issues using structured or free-form parameters
* Fetch ticket details including comments, assignee, and status
* List all Jira projects
* Get project metadata: statuses, priorities, issue types
* `/health` endpoint for Docker health checks

## 📦 Setup

### 1. Clone this repository

```bash
git clone https://github.com/your-org/mcp-jira-server.git
cd mcp-jira-server
```

### 2. Create `.env`

```env
JIRA_BASE_URL=https://yourdomain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

### 3. Build and run with Docker Compose

```bash
docker-compose up --build
```

### 4. Access

* MCP API: [http://localhost:8000/jira/query](http://localhost:8000/jira/query)
* Health check: [http://localhost:8000/health](http://localhost:8000/health)

## 🔧 Supported Intents

### `get_jira_issues`

Fetch issues by JQL or parameters:

```json
{
  "user": "jaroslav",
  "intent": "get_jira_issues",
  "parameters": {
    "project": ["AFS"],
    "priority": ["High", "Highest"],
    "created_after": "-2w",
    "only_count": false
  }
}
```

### `get_ticket_details`

Get full ticket info:

```json
{
  "user": "jaroslav",
  "intent": "get_ticket_details",
  "parameters": {
    "ticket": "AFS-123"
  }
}
```

### `get_jira_projects`

```json
{
  "user": "jaroslav",
  "intent": "get_jira_projects",
  "parameters": {}
}
```

### `get_project_metadata`

```json
{
  "user": "jaroslav",
  "intent": "get_project_metadata",
  "parameters": {
    "project": "AFS"
  }
}
```

## 📁 File Structure

```
/                # Project root
│
├── main.py      # FastAPI app
├── .env         # Jira credentials
├── Dockerfile   # Container definition
├── docker-compose.yml
├── .dockerignore
└── .gitignore
```

## 🧪 Testing with REST Client (VS Code)

You can use `.rest` files with VS Code extension [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client):

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

## 📃 License

MIT or internal use only.
