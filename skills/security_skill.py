"""
IT-SEC Skill — enforced on every agent by BaseAgent.
Blocks prompts/outputs that attempt to leak credentials or bypass policy.
"""
import re

# Patterns that flag a dangerous prompt or output
_DANGEROUS_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}",                     "AWS Access Key"),
    (r"sk-[a-zA-Z0-9]{32,}",                  "Anthropic/OpenAI Key"),
    (r"xoxb-[0-9]+-[a-zA-Z0-9]+",             "Slack Bot Token"),
    (r"ghp_[a-zA-Z0-9]{36}",                  "GitHub Token"),
    (r"glpat-[a-zA-Z0-9\-]{20}",              "GitLab Token"),
    (r"Bearer [a-zA-Z0-9\-_\.]{20,}",         "Bearer Token"),
    (r'(?i)password\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded Password"),
    (r'(?i)api_key\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded API Key"),
    (r'(?i)secret\s*=\s*["\'][^"\']{4,}["\']',  "Hardcoded Secret"),
    (r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----", "Private Key"),
    (r"https?://[^:]+:[^@]+@",                "Basic Auth in URL"),
]

# Prompt instructions the agent must never follow
_FORBIDDEN_INTENTS = [
    r"(?i)(print|show|display|reveal|expose)\s+(all\s+)?(secret|password|token|credential|api.?key)",
    r"(?i)bypass\s+(security|auth|policy|check)",
    r"(?i)commit\s+\.env",
    r"(?i)(push|upload|send).+(credentials|secrets|\.env)",
    r"(?i)disable\s+(pre.?commit|hook|scan)",
]


class SecuritySkill:
    """Stateless helper — call check_input and check_output on every turn."""

    def check_input(self, text: str) -> tuple[bool, str]:
        """
        Returns (safe, reason).
        safe=False means the agent must refuse the request.
        """
        for pattern, label in _DANGEROUS_PATTERNS:
            if re.search(pattern, text):
                return False, f"[IT-SEC] Input contains {label} — blocked per SECURITY.md"

        for pattern in _FORBIDDEN_INTENTS:
            if re.search(pattern, text):
                return False, "[IT-SEC] Request violates IT security policy — blocked"

        return True, ""

    def check_output(self, text: str) -> tuple[bool, str]:
        """
        Returns (safe, reason).
        safe=False means the agent must redact before replying.
        """
        hits = []
        for pattern, label in _DANGEROUS_PATTERNS:
            if re.search(pattern, text):
                hits.append(label)
        if hits:
            return False, f"[IT-SEC] Output redacted — contains: {', '.join(hits)}"
        return True, ""

    def redact(self, text: str) -> str:
        """Replace secret values with [REDACTED]."""
        result = text
        for pattern, _ in _DANGEROUS_PATTERNS:
            result = re.sub(pattern, "[REDACTED]", result)
        return result
