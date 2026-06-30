import anthropic
import logging
from config import ANTHROPIC_API_KEY, AGENT_ID

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def create_agent() -> str:
    """Create a new QA agent (run once, store the returned ID)."""
    agent = client.beta.agents.create(
        name="qa-testing-agent",
        model="claude-opus-4-8",
        description="QA agent สำหรับจัดการ test cases และ integrate กับ Jira, Confluence, Vansah, Monday",
        instructions="""
            คุณเป็น QA Engineer assistant ที่เชี่ยวชาญด้านการทดสอบซอฟต์แวร์
            - สร้างและอัปเดต Jira issues สำหรับ bug reports
            - บันทึกผลการทดสอบไปยัง Vansah
            - สร้าง test documentation ใน Confluence
            - อัปเดตสถานะงานใน Monday.com
            - รัน Playwright tests และแจ้งผลลัพธ์
            - อธิบายผลการทดสอบให้ชัดเจนและ actionable
        """,
        tools=[{"type": "agent_toolset_20260401"}],
        betas=["managed-agents-2026-04-01"]
    )
    print(f"Agent created: {agent.id}")
    return agent.id


def run_session(user_input: str, session_metadata: dict = None) -> str:
    """Run an agent session and return the full response."""
    if not AGENT_ID:
        raise ValueError("AGENT_ID not set. Run create_agent() first and save the ID to .env")

    full_response = []

    try:
        with client.beta.agents.sessions.stream(
            agent_id=AGENT_ID,
            input=[{"type": "human_turn", "content": user_input}],
            metadata=session_metadata or {},
            betas=["managed-agents-2026-04-01"]
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    full_response.append(event.delta.text)
                    print(event.delta.text, end="", flush=True)
                elif event.type == "error":
                    logger.error(f"Stream error: {event.error}")
                    break
    except anthropic.APIError as e:
        logger.error(f"API error: {e}")
        raise

    print()
    return "".join(full_response)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        agent_id = create_agent()
        print(f"\nAdd this to your .env:\nAGENT_ID={agent_id}")
    else:
        result = run_session("สวัสดี! ช่วยสรุปความสามารถของคุณให้หน่อย")
