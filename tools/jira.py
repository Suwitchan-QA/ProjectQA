import re
import requests
from requests.auth import HTTPBasicAuth
from config import ATLASSIAN_URL, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN

auth = HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

_PROJECT_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9]{1,9}$')
_ISSUE_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9]{1,9}-\d+$')
_REQUEST_TIMEOUT = 30


def create_jira_issue(project_key: str, summary: str, issue_type: str = "Bug", description: str = "") -> str:
    if not _PROJECT_KEY_PATTERN.match(project_key):
        return f"Invalid project_key '{project_key}'. Must be uppercase letters/numbers e.g. 'QA', 'ITES'"
    if not summary or len(summary) > 255:
        return "summary must be between 1 and 255 characters"
    valid_types = ["Bug", "Task", "Story", "Epic"]
    if issue_type not in valid_types:
        return f"Invalid issue_type '{issue_type}'. Must be one of: {valid_types}"

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            }
        }
    }
    resp = requests.post(
        f"{ATLASSIAN_URL}/rest/api/3/issue",
        json=payload, auth=auth, headers=headers, timeout=_REQUEST_TIMEOUT
    )
    resp.raise_for_status()
    issue_key = resp.json()["key"]
    return f"Created Jira issue: {issue_key} — {ATLASSIAN_URL}/browse/{issue_key}"


def update_jira_issue(issue_key: str, comment: str = "", transition_name: str = "") -> str:
    if not _ISSUE_KEY_PATTERN.match(issue_key):
        return f"Invalid issue_key '{issue_key}'. Must match format: PROJECT-123"

    results = []

    if comment:
        if len(comment) > 10000:
            return "comment must not exceed 10000 characters"
        payload = {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]}}
        resp = requests.post(
            f"{ATLASSIAN_URL}/rest/api/3/issue/{issue_key}/comment",
            json=payload, auth=auth, headers=headers, timeout=_REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        results.append(f"Added comment to {issue_key}")

    if transition_name:
        tr = requests.get(
            f"{ATLASSIAN_URL}/rest/api/3/issue/{issue_key}/transitions",
            auth=auth, headers=headers, timeout=_REQUEST_TIMEOUT
        )
        tr.raise_for_status()
        transition_id = next((t["id"] for t in tr.json()["transitions"] if t["name"].lower() == transition_name.lower()), None)
        if transition_id:
            requests.post(
                f"{ATLASSIAN_URL}/rest/api/3/issue/{issue_key}/transitions",
                json={"transition": {"id": transition_id}},
                auth=auth, headers=headers, timeout=_REQUEST_TIMEOUT
            ).raise_for_status()
            results.append(f"Transitioned {issue_key} to '{transition_name}'")
        else:
            results.append(f"Transition '{transition_name}' not found")

    return "; ".join(results) if results else f"No updates made to {issue_key}"


JIRA_TOOLS = [
    {
        "name": "create_jira_issue",
        "description": "สร้าง Jira issue ใหม่ (Bug, Task, Story)",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_key": {"type": "string", "description": "Project key เช่น QA, ITES (ตัวพิมพ์ใหญ่เท่านั้น)"},
                "summary": {"type": "string", "description": "หัวข้อของ issue (ไม่เกิน 255 ตัวอักษร)"},
                "issue_type": {"type": "string", "enum": ["Bug", "Task", "Story", "Epic"], "description": "ประเภทของ issue"},
                "description": {"type": "string", "description": "รายละเอียดของ issue"}
            },
            "required": ["project_key", "summary"]
        }
    },
    {
        "name": "update_jira_issue",
        "description": "เพิ่ม comment หรือเปลี่ยน status ของ Jira issue",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "Issue key เช่น QA-123, ITES-456"},
                "comment": {"type": "string", "description": "Comment ที่ต้องการเพิ่ม (ไม่เกิน 10000 ตัวอักษร)"},
                "transition_name": {"type": "string", "description": "ชื่อ transition เช่น In Progress, Done"}
            },
            "required": ["issue_key"]
        }
    }
]
