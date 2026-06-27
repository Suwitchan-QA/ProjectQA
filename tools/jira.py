import requests
from requests.auth import HTTPBasicAuth
from config import JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY


def _auth():
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)


def _headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}


def get_issue(issue_key: str) -> dict:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    resp = requests.get(url, auth=_auth(), headers=_headers())
    resp.raise_for_status()
    return resp.json()


def create_issue(summary: str, description: str, issue_type: str = "Bug") -> dict:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            },
            "issuetype": {"name": issue_type},
        }
    }
    resp = requests.post(url, json=payload, auth=_auth(), headers=_headers())
    resp.raise_for_status()
    return resp.json()


def search_issues(jql: str, max_results: int = 50) -> list:
    url = f"{JIRA_BASE_URL}/rest/api/3/search"
    payload = {"jql": jql, "maxResults": max_results}
    resp = requests.post(url, json=payload, auth=_auth(), headers=_headers())
    resp.raise_for_status()
    return resp.json().get("issues", [])


def add_comment(issue_key: str, comment: str) -> dict:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}],
        }
    }
    resp = requests.post(url, json=payload, auth=_auth(), headers=_headers())
    resp.raise_for_status()
    return resp.json()


JIRA_TOOLS = [
    {
        "name": "jira_get_issue",
        "description": "Get details of a Jira issue by its key (e.g. QA-123)",
        "input_schema": {
            "type": "object",
            "properties": {"issue_key": {"type": "string", "description": "Jira issue key"}},
            "required": ["issue_key"],
        },
    },
    {
        "name": "jira_create_issue",
        "description": "Create a new Jira issue (bug, task, story, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "issue_type": {"type": "string", "enum": ["Bug", "Task", "Story", "Epic"], "default": "Bug"},
            },
            "required": ["summary", "description"],
        },
    },
    {
        "name": "jira_search_issues",
        "description": "Search Jira issues using JQL",
        "input_schema": {
            "type": "object",
            "properties": {
                "jql": {"type": "string", "description": "JQL query string"},
                "max_results": {"type": "integer", "default": 50},
            },
            "required": ["jql"],
        },
    },
    {
        "name": "jira_add_comment",
        "description": "Add a comment to a Jira issue",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string"},
                "comment": {"type": "string"},
            },
            "required": ["issue_key", "comment"],
        },
    },
]


def handle_jira_tool(tool_name: str, tool_input: dict):
    if tool_name == "jira_get_issue":
        return get_issue(**tool_input)
    elif tool_name == "jira_create_issue":
        return create_issue(**tool_input)
    elif tool_name == "jira_search_issues":
        return search_issues(**tool_input)
    elif tool_name == "jira_add_comment":
        return add_comment(**tool_input)
