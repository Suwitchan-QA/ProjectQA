# Agent Creation Workflow Guide

คู่มือสร้าง Claude Agent แบบ Step-by-Step ตั้งแต่ Explore ไปจนถึง Integration

---

## Overview

---

## Phase 1: Explore Tools

ก่อนสร้าง Agent ต้องรู้ก่อนว่า tools ที่มีคืออะไร และใช้งานอย่างไร

### 1.1 ประเภทของ Tools ที่ใช้ได้

| ประเภท | คำอธิบาย | เมื่อใช้ |
|--------|-----------|----------|
| **Prebuilt Agent Toolset** | Bash, File ops, Code execution (server-side) | งานทั่วไป, prototype |
| **MCP Tools** | เชื่อมต่อกับ external services (GitHub, Slack, DB) | integration กับ 3rd party |
| **Custom Client-side Tools** | ฟังก์ชันที่เขียนเอง | business logic เฉพาะ |
| **Server Tools** | Web search, web fetch (Anthropic-hosted) | ค้นหาข้อมูล real-time |

### 1.2 Prebuilt Agent Toolset

```python
# tools ที่ได้มาทันทีเมื่อใช้ agent_toolset_20260401
tools = [{"type": "agent_toolset_20260401"}]
# รวม: bash, file read/write, code execution, text editor

tools = [
    {"type": "web_search_20260209"},   # ค้นหาเว็บ
    {"type": "web_fetch_20260209"},    # ดึงเนื้อหาจาก URL
    {"type": "code_execution_20250522"} # รัน code บน server
]

ต้องการอะไร?
├── Single task (summarize, classify, Q&A)
│   └── Claude API — messages.create()
├── Multi-step pipeline (code-controlled)
│   └── Claude API + Tool Use
├── Stateful agent + workspace per session
│   └── Managed Agents (Anthropic runs the loop)
└── Agent with your own compute
    └── Claude API agentic loop

# ติดตั้ง SDK
pip install anthropic

# ตั้งค่า API key
export ANTHROPIC_API_KEY="sk-ant-..."

import anthropic

client = anthropic.Anthropic()

# Step 1: สร้าง Agent (ทำครั้งเดียว — เก็บ ID ไว้ใช้ซ้ำ)
agent = client.beta.agents.create(
    name="my-coding-agent",
    model="claude-opus-4-8",
    description="Agent สำหรับช่วยเขียนโค้ดและรัน tests",
    instructions="""
        คุณเป็น coding assistant ที่เชี่ยวชาญด้าน Python
        - วิเคราะห์โค้ดและหา bugs
        - เขียน unit tests
        - อธิบายผลลัพธ์ให้ชัดเจน
    """,
    tools=[{"type": "agent_toolset_20260401"}],
    betas=["managed-agents-2026-04-01"]
)

AGENT_ID = agent.id
print(f"Agent ID: {AGENT_ID}")  # เก็บ ID นี้ไว้!

# Step 2: สร้าง Session ทุกครั้งที่ต้องการใช้งาน
with client.beta.agents.sessions.stream(
    agent_id=AGENT_ID,
    input=[{
        "type": "human_turn",
        "content": "วิเคราะห์โค้ดนี้และหา bugs: def add(a,b): return a-b"
    }],
    betas=["managed-agents-2026-04-01"]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)

tools = [
    {
        "name": "run_test",
        "description": "รัน unit test สำหรับโค้ด",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "โค้ดที่จะทดสอบ"},
                "test_name": {"type": "string"}
            },
            "required": ["code"]
        }
    }
]

def run_test(code: str, test_name: str = "test") -> str:
    return f"Test {test_name}: PASSED"

messages = [{"role": "user", "content": "ทดสอบฟังก์ชัน add นี้ให้หน่อย"}]

while True:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8096,
        thinking={"type": "adaptive"},
        tools=tools,
        messages=messages
    )

    if response.stop_reason == "end_turn":
        break

    if response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = run_test(**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
    else:
        break

for block in response.content:
    if hasattr(block, "text"):
        print(block.text)

agent = client.beta.agents.create(
    name="github-agent",
    model="claude-opus-4-8",
    tools=[
        {"type": "agent_toolset_20260401"},
        {
            "type": "mcp",
            "server_name": "github",
            "server_url": "https://mcp.github.com",
            "allowed_tools": ["read_file", "create_issue", "list_prs"]
        }
    ],
    betas=["managed-agents-2026-04-01"]
)

import psycopg2

def query_db(sql: str) -> str:
    conn = psycopg2.connect(database="mydb", user="user", password="pass")
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return str(rows)

db_tool = {
    "name": "query_database",
    "description": "Query ข้อมูลจาก PostgreSQL database",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "SQL query"}
        },
        "required": ["sql"]
    }
}

from slack_sdk import WebClient

slack_client = WebClient(token="xoxb-...")

def send_slack_message(channel: str, message: str) -> str:
    slack_client.chat_postMessage(channel=channel, text=message)
    return f"ส่งข้อความไปที่ #{channel} แล้ว"

slack_tool = {
    "name": "send_slack",
    "description": "ส่งข้อความไปยัง Slack channel",
    "input_schema": {
        "type": "object",
        "properties": {
            "channel": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": ["channel", "message"]
    }
}
import httpx

def call_api(url: str, method: str = "GET", body: dict = None) -> str:
    with httpx.Client() as http:
        if method == "GET":
            resp = http.get(url)
        elif method == "POST":
            resp = http.post(url, json=body)
        return resp.text

api_tool = {
    "name": "call_external_api",
    "description": "เรียก external REST API",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT"]},
            "body": {"type": "object"}
        },
        "required": ["url"]
    }
}

def search_knowledge_base(query: str, top_k: int = 5) -> str:
    # ตัวอย่างกับ Pinecone / Weaviate / Chroma
    return f"ผลการค้นหา '{query}': [document excerpts here]"

rag_tool = {
    "name": "search_knowledge_base",
    "description": "ค้นหาข้อมูลจาก knowledge base ด้วย semantic search",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    }
}

from anthropic import Anthropic

client = Anthropic()

@client.beta.tools.beta_tool
def get_weather(city: str) -> str:
    """ดึงข้อมูลสภาพอากาศของเมือง"""
    return f"Bangkok: 32°C, Sunny"

@client.beta.tools.beta_tool
def send_notification(message: str, recipient: str) -> str:
    """ส่ง notification ไปยัง recipient"""
    return f"Sent to {recipient}: {message}"

response = client.beta.tools.run(
    model="claude-opus-4-8",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    tools=[get_weather, send_notification],
    messages=[{
        "role": "user",
        "content": "เช็คอากาศกรุงเทพแล้วแจ้ง john@example.com"
    }]
)

print(response.final_message.content[-1].text)

my-agent/
├── agent.py
├── tools/
│   ├── __init__.py
│   ├── database.py
│   ├── api.py
│   └── slack.py
├── config.py
└── requirements.txt

anthropic>=0.50.0
slack-sdk>=3.0.0
httpx>=0.27.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0

import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
AGENT_ID = os.environ.get("AGENT_ID")

import anthropic
import logging
from config import ANTHROPIC_API_KEY, AGENT_ID

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def run_agent_session(user_input: str, session_metadata: dict = None) -> str:
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
                elif event.type == "error":
                    logger.error(f"Stream error: {event.error}")
                    break
    except anthropic.APIError as e:
        logger.error(f"API error: {e}")
        raise
    return "".join(full_response)


---

พอ copy เสร็จแล้วทำตาม step ด้านบนได้เลยครับ แจ้งกลับมาถ้าติดตรงไหน
