import anthropic
import json
from config import ANTHROPIC_API_KEY
from tools.jira import JIRA_TOOLS, handle_jira_tool
from tools.confluence import CONFLUENCE_TOOLS, handle_confluence_tool
from tools.vansah import VANSAH_TOOLS, handle_vansah_tool
from tools.monday import MONDAY_TOOLS, handle_monday_tool
from tools.playwright_tool import PLAYWRIGHT_TOOLS, handle_playwright_tool

ALL_TOOLS = JIRA_TOOLS + CONFLUENCE_TOOLS + VANSAH_TOOLS + MONDAY_TOOLS + PLAYWRIGHT_TOOLS

TOOL_HANDLERS = {}
for tool in JIRA_TOOLS:
    TOOL_HANDLERS[tool["name"]] = handle_jira_tool
for tool in CONFLUENCE_TOOLS:
    TOOL_HANDLERS[tool["name"]] = handle_confluence_tool
for tool in VANSAH_TOOLS:
    TOOL_HANDLERS[tool["name"]] = handle_vansah_tool
for tool in MONDAY_TOOLS:
    TOOL_HANDLERS[tool["name"]] = handle_monday_tool
for tool in PLAYWRIGHT_TOOLS:
    TOOL_HANDLERS[tool["name"]] = handle_playwright_tool

SYSTEM_PROMPT = """You are a QA automation agent. You help QA engineers manage test cases,
report bugs, update test results, and run automated tests. You have access to:
- Jira: create/search/update issues and bugs
- Confluence: search and manage test documentation
- Vansah: manage test runs and results
- Monday.com: track QA tasks on the board
- Playwright: run UI automated tests

Always confirm destructive actions before executing. Summarize results clearly."""


def run_agent(user_message: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    print(f"[Tool] {tool_name}({json.dumps(tool_input, ensure_ascii=False)})")
                    try:
                        handler = TOOL_HANDLERS[tool_name]
                        result = handler(tool_name, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True,
                        })
            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "สวัสดี บอกความสามารถของคุณหน่อย"
    print(run_agent(prompt))
