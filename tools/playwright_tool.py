import subprocess
import json
from pathlib import Path


def run_playwright_tests(spec_file: str = None, headed: bool = False) -> dict:
    cmd = ["npx", "playwright", "test"]
    if spec_file:
        cmd.append(spec_file)
    if headed:
        cmd.append("--headed")
    cmd += ["--reporter=json"]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    output = result.stdout
    try:
        report = json.loads(output)
    except json.JSONDecodeError:
        report = {"raw": output, "stderr": result.stderr}

    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "report": report,
    }


def get_test_list() -> list:
    cmd = ["npx", "playwright", "test", "--list", "--reporter=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    try:
        data = json.loads(result.stdout)
        return data.get("suites", [])
    except json.JSONDecodeError:
        return []


PLAYWRIGHT_TOOLS = [
    {
        "name": "playwright_run_tests",
        "description": "Run Playwright test suite and return results",
        "input_schema": {
            "type": "object",
            "properties": {
                "spec_file": {"type": "string", "description": "Path to a specific spec file (optional)"},
                "headed": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "playwright_list_tests",
        "description": "List all available Playwright tests without running them",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def handle_playwright_tool(tool_name: str, tool_input: dict):
    if tool_name == "playwright_run_tests":
        return run_playwright_tests(**tool_input)
    elif tool_name == "playwright_list_tests":
        return get_test_list()
