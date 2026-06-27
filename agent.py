"""
QAAgent — main agent, extends BaseAgent.
All tools + IT-SEC policy inherited automatically.
"""
from skills.base_agent import BaseAgent
from tools.jira import JIRA_TOOLS, handle_jira_tool
from tools.confluence import CONFLUENCE_TOOLS, handle_confluence_tool
from tools.vansah import VANSAH_TOOLS, handle_vansah_tool
from tools.monday import MONDAY_TOOLS, handle_monday_tool
from tools.playwright_tool import PLAYWRIGHT_TOOLS, handle_playwright_tool

_HANDLERS = {}
for _tool in JIRA_TOOLS + CONFLUENCE_TOOLS + VANSAH_TOOLS + MONDAY_TOOLS + PLAYWRIGHT_TOOLS:
    _name = _tool["name"]
    if _name.startswith("jira_"):          _HANDLERS[_name] = handle_jira_tool
    elif _name.startswith("confluence_"):  _HANDLERS[_name] = handle_confluence_tool
    elif _name.startswith("vansah_"):      _HANDLERS[_name] = handle_vansah_tool
    elif _name.startswith("monday_"):      _HANDLERS[_name] = handle_monday_tool
    elif _name.startswith("playwright_"):  _HANDLERS[_name] = handle_playwright_tool


class QAAgent(BaseAgent):
    name = "QA Agent"
    tools = JIRA_TOOLS + CONFLUENCE_TOOLS + VANSAH_TOOLS + MONDAY_TOOLS + PLAYWRIGHT_TOOLS
    system = """You are a QA automation agent. You help QA engineers:
- Create and track bugs in Jira
- Manage test documentation in Confluence
- Log test results in Vansah
- Track QA tasks in Monday.com
- Run and interpret Playwright UI tests

Always confirm before destructive actions. Summarize results clearly."""

    def handle_tool(self, tool_name: str, tool_input: dict):
        handler = _HANDLERS.get(tool_name)
        if not handler:
            raise ValueError(f"No handler for tool: {tool_name}")
        return handler(tool_name, tool_input)


if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "บอกความสามารถของคุณหน่อย"
    agent = QAAgent()
    print("\n" + agent.run(prompt))
