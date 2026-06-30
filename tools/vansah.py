import urllib.parse
import requests
from config import VANSAH_API_TOKEN, VANSAH_URL

_ALLOWED_VANSAH_HOST = "prod.vansah.com"
_REQUEST_TIMEOUT = 30

headers = {
    "Authorization": f"Bearer {VANSAH_API_TOKEN}",
    "Content-Type": "application/json"
}


def _validate_vansah_url(url: str) -> bool:
    """Ensure VANSAH_URL points to the expected host to prevent SSRF."""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in ("https",) and parsed.netloc == _ALLOWED_VANSAH_HOST
    except Exception:
        return False


def submit_test_result(test_case_key: str, status: str, comment: str = "", environment: str = "production") -> str:
    valid_statuses = ["passed", "failed", "blocked", "untested"]
    if status not in valid_statuses:
        return f"Invalid status '{status}'. Must be one of: {valid_statuses}"

    if not test_case_key or not test_case_key.strip():
        return "test_case_key must not be empty"

    if not _validate_vansah_url(VANSAH_URL):
        return f"VANSAH_URL is invalid or points to an unexpected host. Expected: {_ALLOWED_VANSAH_HOST}"

    payload = {
        "testCaseKey": test_case_key.strip(),
        "testRunStatus": status,
        "environment": environment,
        "comment": comment[:1000] if comment else ""
    }
    resp = requests.post(
        f"{VANSAH_URL}/testRuns",
        json=payload, headers=headers, timeout=_REQUEST_TIMEOUT
    )
    resp.raise_for_status()
    return f"Submitted test result for {test_case_key}: {status} in {environment}"


VANSAH_TOOLS = [
    {
        "name": "submit_test_result",
        "description": "บันทึกผลการทดสอบไปยัง Vansah Test Management",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_case_key": {"type": "string", "description": "Test case key เช่น TC-001"},
                "status": {"type": "string", "enum": ["passed", "failed", "blocked", "untested"], "description": "ผลการทดสอบ"},
                "comment": {"type": "string", "description": "หมายเหตุเพิ่มเติม (ไม่เกิน 1000 ตัวอักษร)"},
                "environment": {"type": "string", "description": "สภาพแวดล้อมที่ทดสอบ เช่น production, staging"}
            },
            "required": ["test_case_key", "status"]
        }
    }
]
