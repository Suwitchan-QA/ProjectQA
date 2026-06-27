"""
QA Workflow Orchestrator — Automated pipeline with Approval Gates

Flow:
  Input → [Agent 1] → ⏸ GATE 1 → [Agent 2] → ⏸ GATE 2
       → [Agent 3] → ⏸ GATE 3 → [Agent 4] → ✅ Done

Usage:
  python agents/qa_workflow.py --jira QA-123
  python agents/qa_workflow.py --req REQ-001 --title "Login" --desc "..." --ac "..."
  python agents/qa_workflow.py --req REQ-001 --title "Login" --desc "..." --no-gates
"""
import json
import sys
import argparse
from datetime import datetime

from agents.agent_1_validate_requirement import ValidateRequirementAgent
from agents.agent_2_create_testcase import CreateTestCaseAgent
from agents.agent_3_execute_testcase import ExecuteTestCaseAgent
from agents.agent_4_uat_signoff import UATSignoffAgent
from agents.approval_gate import ApprovalGate

DIV = "=" * 60


def print_stage(n: int, name: str):
    print(f"\n{DIV}")
    print(f"  🤖 STAGE {n}: {name}")
    print(f"{DIV}")


def run_qa_workflow(
    project_name: str = "ProjectQA",
    version: str = "1.0.0",
    tester_name: str = "QA Team",
    approver_name: str = "QA Lead",
    jira_issue: str = None,
    req_id: str = None,
    req_title: str = None,
    req_desc: str = None,
    req_ac: str = None,
    skip_gates: bool = False,
    skip_connection_check: bool = False,
) -> dict:

    started_at = datetime.now()
    gate = ApprovalGate(project=project_name, version=version, approver=approver_name)

    print(f"\n{'#'*60}")
    print(f"  QA AUTOMATED WORKFLOW — {project_name} v{version}")
    print(f"  Started : {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Approver: {approver_name}")
    print(f"  Gates   : {'DISABLED (--no-gates)' if skip_gates else 'ENABLED'}")
    print(f"{'#'*60}")

    results = {}

    # ══════════════════════════════════════════════════════════
    # STAGE 1 — Validate Requirement
    # ══════════════════════════════════════════════════════════
    print_stage(1, "Validate Requirement")
    agent1 = ValidateRequirementAgent(skip_connection_check=skip_connection_check)

    if jira_issue:
        s1 = agent1.run_on_jira_issue(jira_issue)
    else:
        s1 = agent1.run_on_text(
            req_id=req_id or "REQ-001",
            title=req_title or "Untitled",
            description=req_desc or "",
            ac=req_ac or "",
        )
    results["stage_1"] = s1
    print("\n✔ Stage 1 complete")

    # ── Gate 1 ────────────────────────────────────────────────
    if not skip_gates:
        gate.request(
            stage=1,
            name="Validate Requirement",
            summary=_format_summary(s1["result"]),
            details=s1,
        )

    # ══════════════════════════════════════════════════════════
    # STAGE 2 — Create Test Cases
    # ══════════════════════════════════════════════════════════
    print_stage(2, "Create Test Cases")
    agent2 = CreateTestCaseAgent(skip_connection_check=skip_connection_check)
    s2 = agent2.run_from_validation(s1["result"])
    results["stage_2"] = s2
    print("\n✔ Stage 2 complete")

    # ── Gate 2 ────────────────────────────────────────────────
    if not skip_gates:
        gate.request(
            stage=2,
            name="Create Test Cases",
            summary=_format_summary(s2["result"]),
            details=s2,
        )

    # ══════════════════════════════════════════════════════════
    # STAGE 3 — Execute Test Cases
    # ══════════════════════════════════════════════════════════
    print_stage(3, "Execute Test Cases")
    agent3 = ExecuteTestCaseAgent(skip_connection_check=skip_connection_check)
    s3 = agent3.run_from_test_plan(s2["result"])
    results["stage_3"] = s3
    print("\n✔ Stage 3 complete")

    # ── Gate 3 ────────────────────────────────────────────────
    if not skip_gates:
        gate.request(
            stage=3,
            name="Execute Test Cases",
            summary=_format_summary(s3["result"]),
            details=s3,
        )

    # ══════════════════════════════════════════════════════════
    # STAGE 4 — UAT Signoff Document
    # ══════════════════════════════════════════════════════════
    print_stage(4, "Create UAT Signoff Document")
    agent4 = UATSignoffAgent(skip_connection_check=skip_connection_check)
    s4 = agent4.run_from_execution(
        execution_report=s3["result"],
        project_name=project_name,
        version=version,
        tester_name=tester_name,
    )
    results["stage_4"] = s4
    print("\n✔ Stage 4 complete")

    # ══════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ══════════════════════════════════════════════════════════
    ended_at = datetime.now()
    duration = (ended_at - started_at).seconds

    print(gate.summary_report())

    print(f"\n{'#'*60}")
    print(f"  ✅ QA WORKFLOW COMPLETE")
    print(f"  Duration: {duration}s")
    print(f"{'#'*60}\n")

    final = {
        "project": project_name,
        "version": version,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_seconds": duration,
        "approver": approver_name,
        **results,
    }

    output_file = f"qa_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"📁 Result saved: {output_file}\n")

    return final


def _format_summary(text: str) -> str:
    if not text:
        return "(no output)"
    return text[:800] + ("..." if len(text) > 800 else "")


# ── CLI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="QA Automated Workflow Pipeline with Approval Gates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From Jira issue (with approval gates)
  python agents/qa_workflow.py --jira QA-123 --project MyApp --version 2.0

  # From requirement text
  python agents/qa_workflow.py \\
    --req REQ-001 --title "User Login" \\
    --desc "User can login with email and password" \\
    --ac "Login succeeds with valid credentials" \\
    --project MyApp --version 2.0 --approver "Suwitchan"

  # Skip gates (fully automated, no prompts)
  python agents/qa_workflow.py --jira QA-123 --no-gates
        """,
    )
    parser.add_argument("--jira",     help="Jira issue key (e.g. QA-123)")
    parser.add_argument("--req",      help="Requirement ID")
    parser.add_argument("--title",    help="Requirement title")
    parser.add_argument("--desc",     help="Requirement description")
    parser.add_argument("--ac",       help="Acceptance criteria")
    parser.add_argument("--project",  default="ProjectQA", help="Project name")
    parser.add_argument("--version",  default="1.0.0",     help="Version")
    parser.add_argument("--tester",   default="QA Team",   help="Tester name")
    parser.add_argument("--approver", default="QA Lead",   help="Approver name")
    parser.add_argument("--no-gates", action="store_true", help="Skip all approval gates")
    parser.add_argument("--no-connect-check", action="store_true",
                        help="Skip tool connection check")
    args = parser.parse_args()

    if not args.jira and not args.req:
        parser.error("Provide either --jira <key> or --req <id> with --title and --desc")

    run_qa_workflow(
        project_name=args.project,
        version=args.version,
        tester_name=args.tester,
        approver_name=args.approver,
        jira_issue=args.jira,
        req_id=args.req,
        req_title=args.title,
        req_desc=args.desc,
        req_ac=args.ac,
        skip_gates=args.no_gates,
        skip_connection_check=args.no_connect_check,
    )
