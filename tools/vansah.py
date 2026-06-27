import requests
from config import VANSAH_API_TOKEN, VANSAH_BASE_URL


def _headers():
    return {
        "Authorization": f"Bearer {VANSAH_API_TOKEN}",
        "Content-Type": "application/json",
    }


def get_test_runs(project_key: str) -> list:
    url = f"{VANSAH_BASE_URL}/testRuns"
    params = {"projectKey": project_key}
    resp = requests.get(url, headers=_headers(), params=params)
    resp.raise_for_status()
    return resp.json()


def add_test_result(test_run_id: str, test_case_key: str, status: str, comment: str = "") -> dict:
    url = f"{VANSAH_BASE_URL}/testRuns/{test_run_id}/results"
    payload = {
        "testCaseKey": test_case_key,
        "status": status,
        "comment": comment,
    }
    resp = requests.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def create_test_run(project_key: str, name: str) -> dict:
    url = f"{VANSAH_BASE_URL}/testRuns"
    payload = {"projectKey": project_key, "name": name}
    resp = requests.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


VANSAH_TOOLS = [
    {
        "name": "vansah_get_test_runs",
        "description": "Get all test runs for a project in Vansah",
        "input_schema": {
            "type": "object",
            "properties": {"project_key": {"type": "string"}},
            "required": ["project_key"],
        },
    },
    {
        "name": "vansah_create_test_run",
        "description": "Create a new test run in Vansah",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_key": {"type": "string"},
                "name": {"type": "string"},
            },
            "required": ["project_key", "name"],
        },
    },
    {
        "name": "vansah_add_test_result",
        "description": "Add a test result to a Vansah test run",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_run_id": {"type": "string"},
                "test_case_key": {"type": "string"},
                "status": {"type": "string", "enum": ["PASSED", "FAILED", "BLOCKED", "UNTESTED"]},
                "comment": {"type": "string"},
            },
            "required": ["test_run_id", "test_case_key", "status"],
        },
    },
]


def handle_vansah_tool(tool_name: str, tool_input: dict):
    if tool_name == "vansah_get_test_runs":
        return get_test_runs(**tool_input)
    elif tool_name == "vansah_create_test_run":
        return create_test_run(**tool_input)
    elif tool_name == "vansah_add_test_result":
        return add_test_result(**tool_input)
