"""
Agent 1: Validate Requirement
- รับ Requirement จาก Jira / ข้อความ
- ตรวจสอบความครบถ้วน, ความชัดเจน, testability
- ส่งผล ValidatedRequirement ให้ Agent 2
"""
from skills.base_agent import BaseAgent
from tools.jira import JIRA_TOOLS, handle_jira_tool
from tools.confluence import CONFLUENCE_TOOLS, handle_confluence_tool

_TOOLS = JIRA_TOOLS + CONFLUENCE_TOOLS
_HANDLERS = {}
for t in JIRA_TOOLS:        _HANDLERS[t["name"]] = handle_jira_tool
for t in CONFLUENCE_TOOLS:  _HANDLERS[t["name"]] = handle_confluence_tool

VALIDATE_TOOLS = [
    {
        "name": "validate_requirement",
        "description": "Validate a single requirement for completeness, clarity, and testability",
        "input_schema": {
            "type": "object",
            "properties": {
                "req_id":       {"type": "string", "description": "Requirement ID (e.g. REQ-001)"},
                "title":        {"type": "string"},
                "description":  {"type": "string"},
                "acceptance_criteria": {"type": "string"},
            },
            "required": ["req_id", "title", "description"],
        },
    },
    {
        "name": "flag_requirement_issue",
        "description": "Flag a requirement as having issues that need clarification",
        "input_schema": {
            "type": "object",
            "properties": {
                "req_id":   {"type": "string"},
                "issue":    {"type": "string", "description": "Description of the issue"},
                "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
            },
            "required": ["req_id", "issue", "severity"],
        },
    },
]


class ValidateRequirementAgent(BaseAgent):
    name = "Agent 1 — Validate Requirement"
    tools = _TOOLS + VALIDATE_TOOLS
    system = """You are a QA Requirements Analyst. Your job is:
1. Read requirements from Jira issues or user input
2. Check each requirement for:
   - Completeness (who, what, when, where, why)
   - Clarity (no ambiguous language)
   - Testability (can be verified with a test case)
   - Acceptance Criteria presence
3. Flag issues with severity: critical / major / minor
4. Produce a structured ValidatedRequirement report

Output format (JSON):
{
  "req_id": "REQ-001",
  "title": "...",
  "status": "PASSED" | "FAILED" | "NEEDS_CLARIFICATION",
  "issues": [{"severity": "major", "issue": "..."}],
  "testability_score": 1-10,
  "validated_description": "...",
  "acceptance_criteria": ["AC-1: ...", "AC-2: ..."],
  "ready_for_test_design": true | false
}"""

    def handle_tool(self, tool_name: str, tool_input: dict):
        if tool_name in _HANDLERS:
            return _HANDLERS[tool_name](tool_name, tool_input)
        if tool_name == "validate_requirement":
            return self._validate(tool_input)
        if tool_name == "flag_requirement_issue":
            return self._flag(tool_input)

    def _validate(self, req: dict) -> dict:
        issues = []
        score = 10
        if not req.get("acceptance_criteria"):
            issues.append({"severity": "critical", "issue": "Missing acceptance criteria"})
            score -= 3
        if len(req.get("description", "")) < 20:
            issues.append({"severity": "major", "issue": "Description too vague or too short"})
            score -= 2
        for vague in ["should", "might", "could", "etc", "TBD", "TBC"]:
            if vague.lower() in req.get("description", "").lower():
                issues.append({"severity": "minor", "issue": f"Vague term found: '{vague}'"})
                score -= 1
        return {
            "req_id": req["req_id"],
            "title": req["title"],
            "issues": issues,
            "testability_score": max(score, 0),
            "ready_for_test_design": len([i for i in issues if i["severity"] == "critical"]) == 0,
        }

    def _flag(self, data: dict) -> dict:
        print(f"  ⚠️  [{data['severity'].upper()}] {data['req_id']}: {data['issue']}")
        return {"flagged": True, **data}

    def run_on_jira_issue(self, issue_key: str) -> dict:
        prompt = f"""Fetch Jira issue {issue_key}, then validate it as a requirement.
Check completeness, clarity, testability, and acceptance criteria.
Return a structured ValidatedRequirement JSON."""
        result_text = self.run(prompt)
        return {"agent": self.name, "jira_issue": issue_key, "result": result_text}

    def run_on_text(self, req_id: str, title: str, description: str, ac: str = "") -> dict:
        prompt = f"""Validate this requirement:
ID: {req_id}
Title: {title}
Description: {description}
Acceptance Criteria: {ac or 'Not provided'}

Check and return a structured ValidatedRequirement JSON."""
        result_text = self.run(prompt)
        return {"agent": self.name, "req_id": req_id, "result": result_text}
