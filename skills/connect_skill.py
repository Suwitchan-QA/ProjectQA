"""
Connect Skill — checks live connectivity to all registered tools.
Every agent calls self.connect_skill.verify() on startup.
"""
import os
import subprocess
import requests
from requests.auth import HTTPBasicAuth

import config


class ConnectionResult:
    def __init__(self, tool: str, ok: bool, message: str):
        self.tool = tool
        self.ok = ok
        self.message = message

    def __repr__(self):
        icon = "✅" if self.ok else "❌"
        return f"{icon} {self.tool}: {self.message}"


class ConnectSkill:
    """Run verify() to get a list of ConnectionResult for every tool."""

    def verify(self) -> list[ConnectionResult]:
        results = []
        results.append(self._check_jira())
        results.append(self._check_confluence())
        results.append(self._check_vansah())
        results.append(self._check_monday())
        results.append(self._check_postman())
        results.append(self._check_k6())
        results.append(self._check_playwright())
        results.append(self._check_as400())
        results.append(self._check_jmeter())
        results.append(self._check_cursor_ai())
        return results

    def summary(self) -> str:
        results = self.verify()
        lines = ["=== Tool Connection Status ==="]
        for r in results:
            lines.append(str(r))
        failed = [r for r in results if not r.ok]
        lines.append("")
        if failed:
            lines.append(f"⚠️  {len(failed)} tool(s) not connected. Fill in .env to fix.")
        else:
            lines.append("🎉 All tools connected.")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Individual checks                                                   #
    # ------------------------------------------------------------------ #

    def _check_jira(self) -> ConnectionResult:
        if not all([config.JIRA_BASE_URL, config.JIRA_EMAIL, config.JIRA_API_TOKEN]):
            return ConnectionResult("Jira", False, "Missing credentials in .env")
        try:
            r = requests.get(
                f"{config.JIRA_BASE_URL}/rest/api/3/myself",
                auth=HTTPBasicAuth(config.JIRA_EMAIL, config.JIRA_API_TOKEN),
                timeout=5,
            )
            if r.status_code == 200:
                return ConnectionResult("Jira", True, f"Connected as {r.json().get('displayName','?')}")
            return ConnectionResult("Jira", False, f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectionResult("Jira", False, str(e))

    def _check_confluence(self) -> ConnectionResult:
        if not all([config.CONFLUENCE_BASE_URL, config.CONFLUENCE_EMAIL, config.CONFLUENCE_API_TOKEN]):
            return ConnectionResult("Confluence", False, "Missing credentials in .env")
        try:
            r = requests.get(
                f"{config.CONFLUENCE_BASE_URL}/wiki/rest/api/user/current",
                auth=HTTPBasicAuth(config.CONFLUENCE_EMAIL, config.CONFLUENCE_API_TOKEN),
                timeout=5,
            )
            if r.status_code == 200:
                return ConnectionResult("Confluence", True, f"Connected as {r.json().get('displayName','?')}")
            return ConnectionResult("Confluence", False, f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectionResult("Confluence", False, str(e))

    def _check_vansah(self) -> ConnectionResult:
        if not config.VANSAH_API_TOKEN:
            return ConnectionResult("Vansah", False, "Missing VANSAH_API_TOKEN in .env")
        try:
            r = requests.get(
                f"{config.VANSAH_BASE_URL}/health",
                headers={"Authorization": f"Bearer {config.VANSAH_API_TOKEN}"},
                timeout=5,
            )
            if r.status_code in (200, 404):
                return ConnectionResult("Vansah", True, "API reachable")
            return ConnectionResult("Vansah", False, f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectionResult("Vansah", False, str(e))

    def _check_monday(self) -> ConnectionResult:
        if not config.MONDAY_API_KEY:
            return ConnectionResult("Monday.com", False, "Missing MONDAY_API_KEY in .env")
        try:
            r = requests.post(
                "https://api.monday.com/v2",
                json={"query": "{ me { name } }"},
                headers={"Authorization": config.MONDAY_API_KEY},
                timeout=5,
            )
            if r.status_code == 200:
                name = r.json().get("data", {}).get("me", {}).get("name", "?")
                return ConnectionResult("Monday.com", True, f"Connected as {name}")
            return ConnectionResult("Monday.com", False, f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectionResult("Monday.com", False, str(e))

    def _check_postman(self) -> ConnectionResult:
        if not config.POSTMAN_API_KEY:
            return ConnectionResult("Postman", False, "Missing POSTMAN_API_KEY in .env")
        try:
            r = requests.get(
                "https://api.getpostman.com/me",
                headers={"X-Api-Key": config.POSTMAN_API_KEY},
                timeout=5,
            )
            if r.status_code == 200:
                user = r.json().get("user", {}).get("username", "?")
                return ConnectionResult("Postman", True, f"Connected as {user}")
            return ConnectionResult("Postman", False, f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectionResult("Postman", False, str(e))

    def _check_k6(self) -> ConnectionResult:
        if not config.K6_CLOUD_TOKEN:
            return ConnectionResult("K6 Cloud", False, "Missing K6_CLOUD_TOKEN in .env")
        try:
            r = requests.get(
                "https://api.k6.io/v3/account/me",
                headers={"Authorization": f"Token {config.K6_CLOUD_TOKEN}"},
                timeout=5,
            )
            if r.status_code == 200:
                return ConnectionResult("K6 Cloud", True, "Connected")
            return ConnectionResult("K6 Cloud", False, f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectionResult("K6 Cloud", False, str(e))

    def _check_playwright(self) -> ConnectionResult:
        try:
            result = subprocess.run(
                ["npx", "playwright", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return ConnectionResult("Playwright", True, version)
            return ConnectionResult("Playwright", False, "npx playwright not found — run: npm install @playwright/test")
        except Exception as e:
            return ConnectionResult("Playwright", False, str(e))

    def _check_as400(self) -> ConnectionResult:
        if not all([config.AS400_HOST, config.AS400_USERNAME, config.AS400_PASSWORD]):
            return ConnectionResult("IBM AS400", False, "Missing AS400 credentials in .env")
        try:
            import socket
            sock = socket.create_connection((config.AS400_HOST, config.AS400_PORT), timeout=5)
            sock.close()
            return ConnectionResult("IBM AS400", True, f"Port {config.AS400_PORT} reachable at {config.AS400_HOST}")
        except Exception as e:
            return ConnectionResult("IBM AS400", False, str(e))

    def _check_jmeter(self) -> ConnectionResult:
        jmeter_bin = os.path.join(config.JMETER_HOME, "bin", "jmeter")
        if os.path.isfile(jmeter_bin):
            return ConnectionResult("JMeter", True, f"Found at {jmeter_bin}")
        # fallback: check PATH
        result = subprocess.run(["which", "jmeter"], capture_output=True, text=True)
        if result.returncode == 0:
            return ConnectionResult("JMeter", True, f"Found at {result.stdout.strip()}")
        return ConnectionResult("JMeter", False, f"Not found — set JMETER_HOME in .env or install JMeter")

    def _check_cursor_ai(self) -> ConnectionResult:
        if not config.CURSOR_AI_API_KEY:
            return ConnectionResult("Cursor AI", False, "Missing CURSOR_AI_API_KEY in .env")
        try:
            r = requests.get(
                config.CURSOR_AI_BASE_URL,
                headers={"Authorization": f"Bearer {config.CURSOR_AI_API_KEY}"},
                timeout=5,
            )
            if r.status_code in (200, 401, 403, 404):
                return ConnectionResult("Cursor AI", True, "API endpoint reachable")
            return ConnectionResult("Cursor AI", False, f"HTTP {r.status_code}")
        except Exception as e:
            return ConnectionResult("Cursor AI", False, str(e))
