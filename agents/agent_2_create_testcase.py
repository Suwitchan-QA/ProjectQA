"""
Agent 2: Create Test Case
- รับ ValidatedRequirement จาก Agent 1
- สร้าง Test Cases (positive, negative, edge case)
- บันทึกลง Vansah และ Confluence
- ส่ง TestPlan ให้ Agent 3
"""
from skills.base_agent import BaseAgent
from tools.vansah import VANSAH_TOOLS, handle_vansah_tool
from tools.confluence import CONFLUENCE_TOOLS, handle_confluence_tool
from tools.jira import JIRA_TOOLS, handle_jira_tool

_HANDLERS = {}
for t in VANSAH_TOOLS:      _HANDLERS[t["name"]] = handle_vansah_tool
for t in CONFLUENCE_TOOLS:  _HANDLERS[t["name"]] = handle_confluence_tool
for t in JIRA_TOOLS:        _HANDLERS[t["name"]] = handle_jira_tool

CREATE_TC_TOOLS = [
    {
        "name": "generate_test_cases",
        "description": "Generate test cases from a validated requirement",
        "input_schema": {
            "type": "object",
            "properties": {
                "req_id":             {"type": "string"},
                "title":              {"type": "string"},
                "acceptance_criteria":{"type": "array", "items": {"type": "string"}},
                "types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["positive", "negative", "edge_case", "security", "performance"]},
                    "description": "Test case types to generate",
                },
            },
            "required": ["req_id", "title", "acceptance_criteria"],
        },
    },
]


class CreateTestCaseAgent(BaseAgent):
    name = "Agent 2 — Create Test Case"
    tools = VANSAH_TOOLS + CONFLUENCE_TOOLS + JIRA_TOOLS + CREATE_TC_TOOLS
    system = """You are a QA Test Designer. Your job is:
1. Receive a ValidatedRequirement from Agent 1
2. Design comprehensive test cases covering:
   - Positive scenarios (happy path)
   - Negative scenarios (invalid input, error handling)
   - Edge cases (boundary values, empty input, max length)
   - Security checks if applicable
3. Each test case must have:
   - TC ID (e.g. TC-REQ001-001)
   - Title
   - Preconditions
   - Test Steps (numbered)
   - Expected Result
   - Test Type: positive / negative / edge_case
4. Save test cases to Vansah and document in Confluence

Output format (JSON):
{
  "req_id": "REQ-001",
  "test_plan_id": "TP-001",
  "total_cases": N,
  "test_cases": [
    {
      "tc_id": "TC-REQ001-001",
      "title": "...",
      "type": "positive",
      "preconditions": "...",
      "steps": ["1. ...", "2. ..."],
      "expected_result": "...",
      "priority": "high | medium | low"
    }
  ]
}"""

    def handle_tool(self, tool_name: str, tool_input: dict):
        if tool_name in _HANDLERS:
            return _HANDLERS[tool_name](tool_name, tool_input)
        if tool_name == "generate_test_cases":
            return self._generate(tool_input)

    def _generate(self, data: dict) -> dict:
        req_id = data["req_id"]
        acs = data.get("acceptance_criteria", [])
        types = data.get("types", ["positive", "negative", "edge_case"])
        cases = []
        counter = 1
        for ac in acs:
            for tc_type in types:
                cases.append({
                    "tc_id": f"TC-{req_id}-{counter:03d}",
                    "title": f"[{tc_type.upper()}] {ac[:60]}",
                    "type": tc_type,
                    "preconditions": "System is accessible, user is logged in",
                    "steps": ["1. Navigate to feature", "2. Perform action per AC", "3. Verify result"],
                    "expected_result": f"System behaves as: {ac}",
                    "priority": "high" if tc_type == "positive" else "medium",
                })
                counter += 1
        return {
            "req_id": req_id,
            "test_plan_id": f"TP-{req_id}",
            "total_cases": len(cases),
            "test_cases": cases,
        }

    def run_from_validation(self, validated_result: dict) -> dict:
        prompt = f"""Based on this validated requirement result, create comprehensive test cases:

{validated_result}

Generate positive, negative, and edge case test cases.
Save to Vansah if connected, document in Confluence, and return a TestPlan JSON."""
        result_text = self.run(prompt)
        return {"agent": self.name, "result": result_text}
