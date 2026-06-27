"""
Agent 3: Execute Test Case
- รับ TestPlan จาก Agent 2
- รัน Playwright tests อัตโนมัติ
- บันทึกผล PASSED/FAILED ลง Vansah
- สร้าง Bug ใน Jira ถ้า FAILED
- ส่ง ExecutionReport ให้ Agent 4
"""
from skills.base_agent import BaseAgent
from tools.playwright_tool import PLAYWRIGHT_TOOLS, handle_playwright_tool
from tools.vansah import VANSAH_TOOLS, handle_vansah_tool
from tools.jira import JIRA_TOOLS, handle_jira_tool
from tools.monday import MONDAY_TOOLS, handle_monday_tool

_HANDLERS = {}
for t in PLAYWRIGHT_TOOLS: _HANDLERS[t["name"]] = handle_playwright_tool
for t in VANSAH_TOOLS:     _HANDLERS[t["name"]] = handle_vansah_tool
for t in JIRA_TOOLS:       _HANDLERS[t["name"]] = handle_jira_tool
for t in MONDAY_TOOLS:     _HANDLERS[t["name"]] = handle_monday_tool

EXECUTE_TOOLS = [
    {
        "name": "record_test_result",
        "description": "Record the result of a test case execution",
        "input_schema": {
            "type": "object",
            "properties": {
                "tc_id":          {"type": "string"},
                "status":         {"type": "string", "enum": ["PASSED", "FAILED", "BLOCKED", "SKIPPED"]},
                "actual_result":  {"type": "string"},
                "error_message":  {"type": "string"},
                "screenshot_path":{"type": "string"},
                "duration_ms":    {"type": "integer"},
            },
            "required": ["tc_id", "status", "actual_result"],
        },
    },
    {
        "name": "create_bug_from_failure",
        "description": "Auto-create a Jira bug when a test case fails",
        "input_schema": {
            "type": "object",
            "properties": {
                "tc_id":         {"type": "string"},
                "tc_title":      {"type": "string"},
                "error_message": {"type": "string"},
                "steps_to_reproduce": {"type": "string"},
                "severity":      {"type": "string", "enum": ["critical", "high", "medium", "low"]},
            },
            "required": ["tc_id", "tc_title", "error_message"],
        },
    },
]


class ExecuteTestCaseAgent(BaseAgent):
    name = "Agent 3 — Execute Test Case"
    tools = PLAYWRIGHT_TOOLS + VANSAH_TOOLS + JIRA_TOOLS + MONDAY_TOOLS + EXECUTE_TOOLS
    system = """You are a QA Test Executor. Your job is:
1. Receive a TestPlan from Agent 2
2. Execute test cases:
   - Run automated Playwright tests where applicable
   - Record manual test results for non-automatable cases
3. For each FAILED test:
   - Record error details and screenshot path
   - Auto-create a Jira bug with severity and steps to reproduce
   - Update Monday.com task status
4. Log all results to Vansah test runs

Output format (JSON):
{
  "test_plan_id": "TP-001",
  "execution_date": "YYYY-MM-DD",
  "total": N,
  "passed": N,
  "failed": N,
  "blocked": N,
  "pass_rate": "85%",
  "bugs_created": ["BUG-001", "BUG-002"],
  "results": [
    {
      "tc_id": "TC-REQ001-001",
      "status": "PASSED | FAILED | BLOCKED",
      "actual_result": "...",
      "error_message": "...",
      "bug_id": "BUG-001 or null",
      "duration_ms": 1200
    }
  ],
  "ready_for_uat": true | false
}"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._results: list[dict] = []
        self._bugs_created: list[str] = []

    def handle_tool(self, tool_name: str, tool_input: dict):
        if tool_name in _HANDLERS:
            return _HANDLERS[tool_name](tool_name, tool_input)
        if tool_name == "record_test_result":
            return self._record_result(tool_input)
        if tool_name == "create_bug_from_failure":
            return self._create_bug(tool_input)

    def _record_result(self, data: dict) -> dict:
        self._results.append(data)
        icon = "✅" if data["status"] == "PASSED" else "❌" if data["status"] == "FAILED" else "⚠️"
        print(f"  {icon} {data['tc_id']}: {data['status']} — {data['actual_result'][:60]}")
        return {"recorded": True, **data}

    def _create_bug(self, data: dict) -> dict:
        bug_id = f"BUG-{len(self._bugs_created) + 1:03d}"
        self._bugs_created.append(bug_id)
        print(f"  🐛 Bug created: {bug_id} — {data['tc_title']}")
        return {"bug_id": bug_id, "tc_id": data["tc_id"], "created": True}

    def run_from_test_plan(self, test_plan: dict) -> dict:
        prompt = f"""Execute all test cases from this TestPlan:

{test_plan}

For each test case:
1. Run Playwright automation if it's a UI test
2. Record result as PASSED/FAILED/BLOCKED
3. For any FAILED test, create a Jira bug automatically
4. Update Vansah with all results

Return an ExecutionReport JSON with pass rate and bug list."""
        result_text = self.run(prompt)
        return {"agent": self.name, "result": result_text,
                "bugs_created": self._bugs_created, "results": self._results}
