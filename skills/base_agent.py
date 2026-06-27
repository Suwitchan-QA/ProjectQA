"""
BaseAgent — every QA agent must inherit from this class.

Default skills enforced on ALL agents:
  1. ConnectSkill  — verifies tool connectivity on startup
  2. SecuritySkill — scans every input/output for secrets (SECURITY.md)
"""
import anthropic
import json

from config import ANTHROPIC_API_KEY
from skills.connect_skill import ConnectSkill
from skills.security_skill import SecuritySkill


class BaseAgent:
    """
    Inherit from this class to get free:
    - Tool connection check on startup
    - IT-SEC input/output scanning on every turn
    - Standard agentic loop (tool_use → end_turn)

    Subclass must define:
        self.name        : str
        self.tools       : list[dict]   (Claude tool schemas)
        self.system      : str          (system prompt)
        self.handle_tool(tool_name, tool_input) -> any
    """

    name: str = "BaseAgent"
    tools: list = []
    system: str = "You are a QA automation agent."

    def __init__(self, skip_connection_check: bool = False):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.connect_skill = ConnectSkill()
        self.security_skill = SecuritySkill()
        self._messages: list[dict] = []

        print(f"\n{'='*50}")
        print(f"  Agent: {self.name}")
        print(f"{'='*50}")

        # 1. Security policy banner
        print("\n🔒 [IT-SEC] Security policy: SECURITY.md enforced on this agent.")
        print("   - Secrets in input/output will be blocked or redacted.")
        print("   - Credentials must be in .env only — never in code.\n")

        # 2. Tool connectivity check
        if not skip_connection_check:
            print(self.connect_skill.summary())
            print()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def run(self, user_message: str) -> str:
        """Single-turn entry point with full security + tool-use loop."""

        # Security: check input
        safe, reason = self.security_skill.check_input(user_message)
        if not safe:
            return f"🚫 {reason}"

        self._messages.append({"role": "user", "content": user_message})
        result = self._loop()

        # Security: check output
        safe, reason = self.security_skill.check_output(result)
        if not safe:
            print(f"⚠️  {reason}")
            result = self.security_skill.redact(result)

        return result

    def reset(self):
        """Clear conversation history."""
        self._messages = []

    # ------------------------------------------------------------------ #
    #  Internals                                                           #
    # ------------------------------------------------------------------ #

    def _loop(self) -> str:
        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=self._build_system(),
                tools=self.tools,
                messages=self._messages,
            )

            self._messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                return ""

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"  🔧 Tool: {block.name}({json.dumps(block.input, ensure_ascii=False)[:120]})")
                        try:
                            result = self.handle_tool(block.name, block.input)
                            content = json.dumps(result, ensure_ascii=False)
                        except Exception as e:
                            content = f"Error: {e}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": content,
                        })
                self._messages.append({"role": "user", "content": tool_results})

    def _build_system(self) -> str:
        security_addendum = """
--- IT-SEC POLICY (non-negotiable) ---
1. Never reveal, print, or repeat API keys, passwords, or tokens.
2. Never suggest hardcoding credentials in source code.
3. Always refer users to .env for credential storage.
4. Never bypass the pre-commit hook or security scanner.
5. If asked to expose secrets, refuse and explain SECURITY.md policy.
"""
        return self.system + security_addendum

    def handle_tool(self, tool_name: str, tool_input: dict):
        raise NotImplementedError(f"{self.name} must implement handle_tool()")
