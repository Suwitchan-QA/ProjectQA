"""
Agent 4: Create UAT Signoff Document
- รับ ExecutionReport จาก Agent 3
- สรุปผลการทดสอบทั้งหมด
- สร้าง UAT Signoff Document ใน Confluence
- ปิด Jira issues ที่ผ่าน UAT
- แจ้งผลผ่าน Monday.com
"""
from datetime import date
from skills.base_agent import BaseAgent
from tools.confluence import CONFLUENCE_TOOLS, handle_confluence_tool
from tools.jira import JIRA_TOOLS, handle_jira_tool
from tools.monday import MONDAY_TOOLS, handle_monday_tool

_HANDLERS = {}
for t in CONFLUENCE_TOOLS: _HANDLERS[t["name"]] = handle_confluence_tool
for t in JIRA_TOOLS:       _HANDLERS[t["name"]] = handle_jira_tool
for t in MONDAY_TOOLS:     _HANDLERS[t["name"]] = handle_monday_tool

SIGNOFF_TOOLS = [
    {
        "name": "generate_uat_document",
        "description": "Generate a UAT Signoff document from test execution results",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name":  {"type": "string"},
                "version":       {"type": "string"},
                "test_plan_id":  {"type": "string"},
                "total":         {"type": "integer"},
                "passed":        {"type": "integer"},
                "failed":        {"type": "integer"},
                "blocked":       {"type": "integer"},
                "bugs_created":  {"type": "array", "items": {"type": "string"}},
                "pass_rate":     {"type": "string"},
                "tester_name":   {"type": "string"},
                "signoff_decision": {"type": "string", "enum": ["APPROVED", "REJECTED", "CONDITIONAL"]},
                "conditions":    {"type": "string", "description": "Required if CONDITIONAL"},
            },
            "required": ["project_name", "version", "test_plan_id", "total", "passed", "failed",
                         "pass_rate", "tester_name", "signoff_decision"],
        },
    },
    {
        "name": "determine_signoff_decision",
        "description": "Automatically determine UAT signoff decision based on pass rate and critical bugs",
        "input_schema": {
            "type": "object",
            "properties": {
                "pass_rate_pct":      {"type": "number", "description": "Pass rate 0-100"},
                "critical_bugs":      {"type": "integer"},
                "high_bugs":          {"type": "integer"},
                "total_test_cases":   {"type": "integer"},
            },
            "required": ["pass_rate_pct", "critical_bugs", "high_bugs"],
        },
    },
]


class UATSignoffAgent(BaseAgent):
    name = "Agent 4 — UAT Signoff Document"
    tools = CONFLUENCE_TOOLS + JIRA_TOOLS + MONDAY_TOOLS + SIGNOFF_TOOLS
    system = """You are a QA Lead responsible for UAT sign-off. Your job is:
1. Receive ExecutionReport from Agent 3
2. Evaluate overall quality:
   - APPROVED:    pass rate >= 95%, no critical bugs
   - CONDITIONAL: pass rate 80-94%, or has high bugs (no critical)
   - REJECTED:    pass rate < 80%, or any critical bug exists
3. Create a formal UAT Signoff document in Confluence containing:
   - Executive Summary
   - Test Scope & Coverage
   - Test Results Summary (table)
   - Defects Found (list of Jira bugs)
   - Risk Assessment
   - Sign-off Decision with rationale
   - Conditions (if CONDITIONAL)
   - Approver signature placeholder
4. Close resolved Jira issues
5. Update Monday.com with final UAT status

Output format (JSON):
{
  "signoff_id": "UAT-SIGNOFF-001",
  "project_name": "...",
  "version": "...",
  "date": "YYYY-MM-DD",
  "decision": "APPROVED | REJECTED | CONDITIONAL",
  "pass_rate": "95%",
  "total_bugs": N,
  "critical_bugs": N,
  "conditions": "...",
  "confluence_page_id": "...",
  "confluence_page_url": "...",
  "summary": "...",
  "ready_for_release": true | false
}"""

    def handle_tool(self, tool_name: str, tool_input: dict):
        if tool_name in _HANDLERS:
            return _HANDLERS[tool_name](tool_name, tool_input)
        if tool_name == "generate_uat_document":
            return self._generate_doc(tool_input)
        if tool_name == "determine_signoff_decision":
            return self._determine_decision(tool_input)

    def _determine_decision(self, data: dict) -> dict:
        rate = data["pass_rate_pct"]
        critical = data.get("critical_bugs", 0)
        high = data.get("high_bugs", 0)

        if critical > 0 or rate < 80:
            decision = "REJECTED"
            rationale = f"Critical bugs: {critical}, Pass rate: {rate:.1f}%"
        elif rate < 95 or high > 0:
            decision = "CONDITIONAL"
            rationale = f"Pass rate {rate:.1f}% or {high} high-severity bugs must be resolved"
        else:
            decision = "APPROVED"
            rationale = f"Pass rate {rate:.1f}%, no critical/high bugs"

        return {"decision": decision, "rationale": rationale,
                "ready_for_release": decision == "APPROVED"}

    def _generate_doc(self, data: dict) -> dict:
        today = date.today().isoformat()
        decision = data["signoff_decision"]
        icon = "✅ APPROVED" if decision == "APPROVED" else "❌ REJECTED" if decision == "REJECTED" else "⚠️ CONDITIONAL"
        bugs = "\n".join([f"<li>{b}</li>" for b in data.get("bugs_created", [])])
        conditions_section = ""
        if decision == "CONDITIONAL" and data.get("conditions"):
            conditions_section = f"<h2>Conditions for Approval</h2><p>{data['conditions']}</p>"

        html = f"""<h1>UAT Sign-off Document</h1>
<table>
  <tr><th>Project</th><td>{data['project_name']}</td></tr>
  <tr><th>Version</th><td>{data['version']}</td></tr>
  <tr><th>Test Plan</th><td>{data['test_plan_id']}</td></tr>
  <tr><th>Date</th><td>{today}</td></tr>
  <tr><th>Tester</th><td>{data['tester_name']}</td></tr>
</table>

<h2>Executive Summary</h2>
<p>UAT for <strong>{data['project_name']} v{data['version']}</strong> has been completed
with a pass rate of <strong>{data['pass_rate']}</strong>.</p>
<p>Decision: <strong>{icon}</strong></p>

<h2>Test Results Summary</h2>
<table>
  <tr><th>Total</th><th>Passed</th><th>Failed</th><th>Blocked</th><th>Pass Rate</th></tr>
  <tr>
    <td>{data['total']}</td>
    <td>{data['passed']}</td>
    <td>{data['failed']}</td>
    <td>{data.get('blocked', 0)}</td>
    <td>{data['pass_rate']}</td>
  </tr>
</table>

<h2>Defects Found</h2>
<ul>{bugs if bugs else '<li>No defects found</li>'}</ul>

{conditions_section}

<h2>Sign-off Decision</h2>
<p><strong>{icon}</strong></p>

<h2>Approver</h2>
<table>
  <tr><th>Name</th><th>Role</th><th>Signature</th><th>Date</th></tr>
  <tr><td></td><td>QA Lead</td><td>___________</td><td>{today}</td></tr>
  <tr><td></td><td>Product Owner</td><td>___________</td><td></td></tr>
</table>"""

        signoff_id = f"UAT-SIGNOFF-{today.replace('-', '')}"
        print(f"  📄 UAT Document generated: {signoff_id}")
        return {
            "signoff_id": signoff_id,
            "project_name": data["project_name"],
            "version": data["version"],
            "date": today,
            "decision": decision,
            "pass_rate": data["pass_rate"],
            "html_content": html,
            "ready_for_release": decision == "APPROVED",
        }

    def run_from_execution(self, execution_report: dict, project_name: str,
                           version: str, tester_name: str) -> dict:
        prompt = f"""Create a UAT Signoff document from this execution report:

Project: {project_name}
Version: {version}
Tester: {tester_name}

Execution Report:
{execution_report}

Steps:
1. Determine sign-off decision (APPROVED/REJECTED/CONDITIONAL)
2. Generate the full UAT Signoff document
3. Save to Confluence
4. Update Monday.com with UAT status
5. Return the signoff result JSON."""
        result_text = self.run(prompt)
        return {"agent": self.name, "result": result_text}
