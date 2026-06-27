# ProjectQA — QA Automation Agent

Claude-powered QA agent พร้อม integrations ครบ: Jira, Confluence, Vansah, Monday.com, Playwright, AS400, JMeter, K6, Postman

---

## Quick Start (เครื่องใหม่)

### Mac / Linux
```bash
git clone https://github.com/Suwitchan-QA/ProjectQA.git
cd ProjectQA
bash scripts/setup.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/Suwitchan-QA/ProjectQA.git
cd ProjectQA
.\scripts\setup.ps1
```

Setup script จะติดตั้งทุกอย่างอัตโนมัติ:
- Python virtual environment + dependencies
- Node.js + Playwright browsers
- สร้าง `.env` จาก template
- ติดตั้ง pre-commit security hook

---

## การตั้งค่า Credentials

เปิดไฟล์ `.env` แล้วใส่ค่าจริง ดู `.env.example` สำหรับ credentials ทั้งหมดที่รองรับ

---

## วิธีใช้งาน

```bash
# เปิด virtual environment
source .venv/bin/activate        # Mac/Linux
.\.venv\Scripts\Activate.ps1    # Windows

# รัน QA Agent
python agent.py "สร้าง bug report ใน Jira"

# รัน Playwright tests
npm test

# ตรวจ connection ทุก tool
python -c "from agent import QAAgent; QAAgent()"

# สแกน security ก่อน share โค้ด
python scripts/security_scan.py
```

---

## โครงสร้างโปรเจค

```
ProjectQA/
├── skills/
│   ├── base_agent.py       ← BaseAgent (ทุก agent ต้อง extend)
│   ├── connect_skill.py    ← เช็ค connection ทุก tool
│   └── security_skill.py   ← สแกน secrets ทุก input/output
├── tools/
│   ├── jira.py
│   ├── confluence.py
│   ├── vansah.py
│   ├── monday.py
│   └── playwright_tool.py
├── tests/
│   └── example.spec.ts
├── scripts/
│   ├── setup.sh            ← Mac/Linux setup
│   ├── setup.ps1           ← Windows setup
│   └── security_scan.py    ← manual secret scanner
├── .git-hooks/
│   └── pre-commit          ← IT-SEC hook (ติดตั้งโดย setup)
├── agent.py                ← QAAgent (ตัวอย่างการใช้ BaseAgent)
├── config.py               ← โหลด env vars ทั้งหมด
├── .env.example            ← template credentials
├── SECURITY.md             ← IT Security policy
├── pyproject.toml          ← Python package config
└── package.json            ← Node/Playwright config
```

---

## สร้าง Agent ใหม่

```python
from skills.base_agent import BaseAgent

class MyAgent(BaseAgent):
    name = "My Custom Agent"
    tools = [...]
    system = "..."

    def handle_tool(self, tool_name, tool_input):
        ...

agent = MyAgent()
print(agent.run("ทำอะไรสักอย่าง"))
```

ConnectSkill + SecuritySkill ทำงานอัตโนมัติทุก agent ที่ extend BaseAgent

---

## IT Security

ดูนโยบายทั้งหมดใน [SECURITY.md](SECURITY.md)
- ❌ ห้าม commit `.env` หรือ credentials ใดๆ ขึ้น git
- ✅ ใช้ `.env` เก็บ credentials เสมอ
- 🔒 Pre-commit hook สแกน secrets อัตโนมัติทุก commit
