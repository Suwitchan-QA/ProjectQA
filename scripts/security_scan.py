"""
IT-SEC: Secret scanner — run before sharing or publishing code.
Usage: python scripts/security_scan.py [path]
"""
import os
import re
import sys
from pathlib import Path

RED = "\033[0;31m"
YELLOW = "\033[1;33m"
GREEN = "\033[0;32m"
NC = "\033[0m"

SECRET_PATTERNS = [
    ("AWS Access Key",          r"AKIA[0-9A-Z]{16}"),
    ("Anthropic/OpenAI Key",    r"sk-[a-zA-Z0-9]{32,}"),
    ("Slack Bot Token",         r"xoxb-[0-9]+-[a-zA-Z0-9]+"),
    ("GitHub Token",            r"ghp_[a-zA-Z0-9]{36}"),
    ("GitLab Token",            r"glpat-[a-zA-Z0-9\-]{20}"),
    ("Bearer Token",            r"Bearer [a-zA-Z0-9\-_\.]{20,}"),
    ("Hardcoded Password",      r'(?i)password\s*=\s*["\'][^"\']{4,}["\']'),
    ("Hardcoded API Key",       r'(?i)api_key\s*=\s*["\'][^"\']{4,}["\']'),
    ("Hardcoded Secret",        r'(?i)secret\s*=\s*["\'][^"\']{4,}["\']'),
    ("Hardcoded Token",         r'(?i)token\s*=\s*["\'][^"\']{8,}["\']'),
    ("IP:Port Exposure",        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}"),
    ("AS400 Connection String", r'(?i)(as400|iseries|ibmi)\S*password\S*'),
    ("Private Key Block",       r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----"),
    ("Basic Auth in URL",       r"https?://[^:]+:[^@]+@"),
]

SKIP_FILES = {".env.example", "security_scan.py", ".gitignore"}
SKIP_DIRS  = {"node_modules", "__pycache__", ".git", "venv", ".venv"}
SKIP_EXTS  = {".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz",
              ".pyc", ".pyo", ".woff", ".ttf", ".ico"}

findings = []

def scan_file(filepath: Path):
    if filepath.name in SKIP_FILES:
        return
    if filepath.suffix in SKIP_EXTS:
        return
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return
    for label, pattern in SECRET_PATTERNS:
        for match in re.finditer(pattern, content):
            line_no = content[: match.start()].count("\n") + 1
            findings.append((str(filepath), line_no, label, match.group()[:60]))


def scan_dir(root: Path):
    for path in root.rglob("*"):
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.is_file():
            scan_file(path)


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print(f"🔒 [IT-SEC] Scanning: {target.resolve()}\n")

    if target.is_file():
        scan_file(target)
    else:
        scan_dir(target)

    if findings:
        print(f"{RED}{'='*60}")
        print(f"  {len(findings)} potential secret(s) found!")
        print(f"{'='*60}{NC}\n")
        for filepath, line, label, snippet in findings:
            print(f"{RED}[RISK]{NC}  {label}")
            print(f"        File : {filepath}:{line}")
            print(f"        Match: {snippet}...\n")
        print(f"{YELLOW}Action required:{NC}")
        print("  1. Remove secrets from code — use .env variables instead")
        print("  2. Rotate any exposed credentials immediately")
        print("  3. Run: git filter-repo or BFG to purge from git history")
        sys.exit(1)
    else:
        print(f"{GREEN}✔ No secrets detected. Safe to share.{NC}")
        sys.exit(0)
