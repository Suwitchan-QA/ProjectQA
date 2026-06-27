"""
QA Workflow Orchestrator
เชื่อม Agent 1 → 2 → 3 → 4 เป็น pipeline อัตโนมัติ

Usage:
    python agents/qa_workflow.py --jira QA-123
    python agents/qa_workflow.py --req "REQ-001" --title "Login" --desc "User can login"
"""
import json
import sys
import argparse
from datetime import datetime

from agents.agent_1_validate_requirement import ValidateRequirementAgent
from agents.agent_2_create_testcase import CreateTestCaseAgent
from agents.agent_3_execute_testcase import ExecuteTestCaseAgent
from agents.agent_4_uat_signoff import UATSignoffAgent

DIVIDER = "=" * 60


def print_stage(n: int, name: str):
    print(f"\n{DIVIDER}")
    print(f"  STAGE {n}: {name}")
    print(f"{DIVIDER}")


def run_qa_workflow(
    project_name: str = "ProjectQA",
    version: str = "1.0.0",
    tester_name: str = "QA Team",
    jira_issue: str = None,
    req_id: str = None,
    req_title: str = None,
    req_desc: str = None,
    req_ac: str = None,
    skip_connection_check: bool = False,
) -> dict:

    started_at = datetime.now()
    print(f"\n{'#'*60}")
    print(f"  QA WORKFLOW PIPELINE — {project_name} v{version}")
    print(f"  Started: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    # ── Stage 1: Validate Requirement ────────────────────────
    print_stage(1, "Validate Requirement")
    agent1 = ValidateRequirementAgent(skip_connection_check=skip_connection_check)

    if jira_issue:
        stage1_result = agent1.run_on_jira_issue(jira_issue)
    else:
        stage1_result = agent1.run_on_text(
            req_id=req_id or "REQ-001",
            title=req_title or "Untitled Requirement",
            description=req_desc or "",
            ac=req_ac or "",
        )

    print(f"\n✔ Stage 1 complete")
    _print_result(stage1_result)

    # ── Stage 2: Create Test Cases ────────────────────────────
    print_stage(2, "Create Test Cases")
    agent2 = CreateTestCaseAgent(skip_connection_check=skip_connection_check)
    stage2_result = agent2.run_from_validation(stage1_result["result"])

    print(f"\n✔ Stage 2 complete")
    _print_result(stage2_result)

    # ── Stage 3: Execute Test Cases ───────────────────────────
    print_stage(3, "Execute Test Cases")
    agent3 = ExecuteTestCaseAgent(skip_connection_check=skip_connection_check)
    stage3_result = agent3.run_from_test_plan(stage2_result["result"])

    print(f"\n✔ Stage 3 complete")
    _print_result(stage3_result)

    # ── Stage 4: UAT Signoff Document ────────────────────────
    print_stage(4, "Create UAT Signoff Document")
    agent4 = UATSignoffAgent(skip_connection_check=skip_connection_check)
    stage4_result = agent4.run_from_execution(
        execution_report=stage3_result["result"],
        project_name=project_name,
        version=version,
        tester_name=tester_name,
    )

    print(f"\n✔ Stage 4 complete")
    _print_result(stage4_result)

    # ── Final Summary ─────────────────────────────────────────
    ended_at = datetime.now()
    duration = (ended_at - started_at).seconds

    print(f"\n{'#'*60}")
    print(f"  QA WORKFLOW COMPLETE")
    print(f"  Duration: {duration}s")
    print(f"{'#'*60}\n")

    return {
        "project": project_name,
        "version": version,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_seconds": duration,
        "stage_1_validate": stage1_result,
        "stage_2_testcases": stage2_result,
        "stage_3_execution": stage3_result,
        "stage_4_signoff": stage4_result,
    }


def _print_result(result: dict):
    text = result.get("result", "")
    preview = text[:300] + "..." if len(text) > 300 else text
    print(f"\n{preview}")


# ── CLI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QA Workflow Pipeline")
    parser.add_argument("--jira",    help="Jira issue key (e.g. QA-123)")
    parser.add_argument("--req",     help="Requirement ID (e.g. REQ-001)")
    parser.add_argument("--title",   help="Requirement title")
    parser.add_argument("--desc",    help="Requirement description")
    parser.add_argument("--ac",      help="Acceptance criteria")
    parser.add_argument("--project", default="ProjectQA", help="Project name")
    parser.add_argument("--version", default="1.0.0",     help="Version")
    parser.add_argument("--tester",  default="QA Team",   help="Tester name")
    parser.add_argument("--no-connect-check", action="store_true",
                        help="Skip tool connection check on startup")
    args = parser.parse_args()

    result = run_qa_workflow(
        project_name=args.project,
        version=args.version,
        tester_name=args.tester,
        jira_issue=args.jira,
        req_id=args.req,
        req_title=args.title,
        req_desc=args.desc,
        req_ac=args.ac,
        skip_connection_check=args.no_connect_check,
    )

    output_file = f"qa_workflow_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"📁 Full result saved to: {output_file}")
