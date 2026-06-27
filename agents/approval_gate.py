"""
Approval Gate — human-in-the-loop checkpoint between pipeline stages.
Pauses execution, shows stage output, waits for APPROVE / REJECT / COMMENT.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from skills.email_skill import send_rejection_email

GATE_LOG = Path("approval_log.json")

GREEN  = "\033[0;32m"
RED    = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN   = "\033[0;36m"
BOLD   = "\033[1m"
NC     = "\033[0m"


class ApprovalGate:
    """
    Call gate.request(stage_number, stage_name, summary) between agents.
    Returns True if approved, raises SystemExit if rejected.
    """

    def __init__(self, project: str, version: str, approver: str = "QA Lead",
                 run_id: str = "", jira: str = ""):
        self.project  = project
        self.version  = version
        self.approver = approver
        self.run_id   = run_id
        self.jira     = jira
        self._log: list[dict] = []

    def request(self, stage: int, name: str, summary: str, details: dict = None) -> bool:
        """
        Show stage output and wait for human approval.
        Returns True  → proceed to next stage
        Raises SystemExit if rejected.
        """
        self._print_gate_header(stage, name)
        self._print_summary(summary)

        while True:
            print(f"\n{BOLD}  Action required:{NC}")
            print(f"  {GREEN}[A]{NC} Approve — proceed to next stage")
            print(f"  {RED}[R]{NC} Reject  — stop pipeline")
            print(f"  {YELLOW}[C]{NC} Comment — add note then approve")
            print(f"  {CYAN}[D]{NC} Details — show full output")
            print()

            try:
                choice = input("  Your choice (A/R/C/D): ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{RED}  Pipeline interrupted by user.{NC}")
                self._record(stage, name, "INTERRUPTED", "")
                self._save_log()
                sys.exit(1)

            if choice == "D":
                if details:
                    print(f"\n{CYAN}--- Full Details ---{NC}")
                    print(json.dumps(details, ensure_ascii=False, indent=2)[:2000])
                else:
                    print(f"  (No additional details available)")
                continue

            if choice == "A":
                comment = ""
                self._print_approved(stage, name)
                self._record(stage, name, "APPROVED", comment)
                self._save_log()
                return True

            if choice == "C":
                try:
                    comment = input("  Comment: ").strip()
                except (EOFError, KeyboardInterrupt):
                    comment = ""
                self._print_approved(stage, name, comment)
                self._record(stage, name, "APPROVED", comment)
                self._save_log()
                return True

            if choice == "R":
                try:
                    reason = input("  Reason for rejection: ").strip()
                except (EOFError, KeyboardInterrupt):
                    reason = "No reason given"
                self._print_rejected(stage, name, reason)
                self._record(stage, name, "REJECTED", reason)
                self._save_log()
                # ── Send rejection email ──────────────────────
                print(f"  📧 Sending rejection notification...")
                send_rejection_email(
                    stage=stage,
                    stage_name=name,
                    project=self.project,
                    version=self.version,
                    jira=self.jira or "N/A",
                    reason=reason,
                    approver=self.approver,
                    run_id=self.run_id or "N/A",
                )
                print(f"\n{RED}  Pipeline stopped at Stage {stage}: {name}{NC}\n")
                sys.exit(0)

            print(f"  {YELLOW}Invalid choice. Enter A, R, C, or D.{NC}")

    def summary_report(self) -> str:
        lines = [f"\n{'='*55}", f"  Approval Log — {self.project} v{self.version}", f"{'='*55}"]
        for entry in self._log:
            icon = "✅" if entry["decision"] == "APPROVED" else "❌"
            lines.append(f"  {icon} Stage {entry['stage']}: {entry['name']}")
            lines.append(f"     Decision : {entry['decision']}")
            lines.append(f"     By       : {entry['approver']}")
            lines.append(f"     At       : {entry['timestamp']}")
            if entry.get("comment"):
                lines.append(f"     Comment  : {entry['comment']}")
        return "\n".join(lines)

    # ── private ──────────────────────────────────────────────

    def _print_gate_header(self, stage: int, name: str):
        print(f"\n{'━'*55}")
        print(f"{BOLD}{YELLOW}  ⏸  APPROVAL GATE — Stage {stage}: {name}{NC}")
        print(f"{'━'*55}")
        print(f"  Project  : {self.project} v{self.version}")
        print(f"  Approver : {self.approver}")
        print(f"  Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _print_summary(self, summary: str):
        print(f"\n{CYAN}  Stage Output Summary:{NC}")
        lines = summary.strip().split("\n")
        for line in lines[:30]:
            print(f"  {line}")
        if len(lines) > 30:
            print(f"  ... ({len(lines)-30} more lines — press D to view all)")

    def _print_approved(self, stage: int, name: str, comment: str = ""):
        print(f"\n  {GREEN}✅ APPROVED — Stage {stage}: {name}{NC}")
        if comment:
            print(f"  Note: {comment}")

    def _print_rejected(self, stage: int, name: str, reason: str):
        print(f"\n  {RED}❌ REJECTED — Stage {stage}: {name}{NC}")
        print(f"  Reason: {reason}")

    def _record(self, stage: int, name: str, decision: str, comment: str):
        self._log.append({
            "stage": stage,
            "name": name,
            "decision": decision,
            "comment": comment,
            "approver": self.approver,
            "timestamp": datetime.now().isoformat(),
        })

    def _save_log(self):
        existing = []
        if GATE_LOG.exists():
            try:
                existing = json.loads(GATE_LOG.read_text())
            except Exception:
                existing = []
        existing.extend(self._log[-1:])
        GATE_LOG.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
