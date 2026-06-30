import subprocess
import json
import os
import re
from config import BASE_URL


def run_playwright_test(test_file: str = "", browser: str = "chromium", headed: bool = False, base_url: str = "") -> str:
    valid_browsers = ["chromium", "firefox", "webkit"]
    if browser not in valid_browsers:
        return f"Invalid browser '{browser}'. Must be one of: {valid_browsers}"

    if test_file and not re.match(r'^[\w\-/]+\.spec\.(ts|js)$', test_file):
        return f"Invalid test_file '{test_file}'. Must match pattern: tests/name.spec.ts"
    if test_file and (".." in test_file or test_file.startswith("/")):
        return f"Invalid test_file: path traversal not allowed"

    env = os.environ.copy()
    env["BASE_URL"] = base_url or BASE_URL

    cmd = ["npx", "playwright", "test", "--reporter=json"]
    if test_file:
        cmd.append(test_file)
    cmd += [f"--project={browser}"]
    if headed:
        cmd.append("--headed")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        output = result.stdout or result.stderr

        try:
            report = json.loads(output)
            stats = report.get("stats", {})
            passed = stats.get("expected", 0)
            failed = stats.get("unexpected", 0)
            skipped = stats.get("skipped", 0)
            return f"Playwright [{browser}]: {passed} passed, {failed} failed, {skipped} skipped\nExit code: {result.returncode}"
        except json.JSONDecodeError:
            lines = output.strip().split("\n")[-20:]
            return "Playwright output:\n" + "\n".join(lines)

    except subprocess.TimeoutExpired:
        return "Playwright test timed out after 120 seconds"
    except FileNotFoundError:
        return "Playwright not found. Run: npm install && npx playwright install"


PLAYWRIGHT_TOOLS = [
    {
        "name": "run_playwright_test",
        "description": "รัน Playwright E2E tests และแสดงผลลัพธ์",
        "input_schema": {
            "type": "object",
            "properties": {
                "test_file": {"type": "string", "description": "ชื่อไฟล์ test (เว้นว่างเพื่อรันทั้งหมด)"},
                "browser": {"type": "string", "enum": ["chromium", "firefox", "webkit"], "description": "Browser ที่ใช้ทดสอบ"},
                "headed": {"type": "boolean", "description": "แสดงหน้าต่าง browser หรือไม่"},
                "base_url": {"type": "string", "description": "URL ของ application ที่ทดสอบ"}
            },
            "required": []
        }
    }
]
