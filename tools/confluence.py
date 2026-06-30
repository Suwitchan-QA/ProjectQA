import requests
from requests.auth import HTTPBasicAuth
from config import ATLASSIAN_URL, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN

auth = HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}

# Space constants
KNOWLEDGE_SPACE = "~70121afebf570c9494abb86e687f692cf7d89"  # IT-ES Knowledge (read only)
TESTCASE_SPACE = "ITK"  # ITES Testcase knowledge (write)


def get_confluence_pages(space_key: str, title_filter: str = "", limit: int = 25) -> str:
    """Read pages from a Confluence space (e.g. IT-ES Knowledge)."""
    params = {"spaceKey": space_key, "limit": limit, "expand": "body.storage,version"}
    if title_filter:
        params["title"] = title_filter
    resp = requests.get(f"{ATLASSIAN_URL}/wiki/rest/api/content", params=params, auth=auth, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return f"ไม่พบหน้าใน space '{space_key}'"
    lines = [f"พบ {len(results)} หน้าใน space '{space_key}':"]
    for p in results:
        lines.append(f"  - [{p['id']}] {p['title']}")
    return "\n".join(lines)


def get_confluence_page_content(page_id: str) -> str:
    """Read full content of a Confluence page by ID."""
    resp = requests.get(
        f"{ATLASSIAN_URL}/wiki/rest/api/content/{page_id}",
        params={"expand": "body.storage,version,title"},
        auth=auth, headers=headers
    )
    resp.raise_for_status()
    data = resp.json()
    title = data.get("title", "")
    version = data.get("version", {}).get("number", 1)
    body = data.get("body", {}).get("storage", {}).get("value", "")
    import re
    text = re.sub(r"<[^>]+>", " ", body).strip()
    text = re.sub(r"\s+", " ", text)
    return f"Title: {title}\nVersion: {version}\nPage ID: {page_id}\n\nContent:\n{text}"


def search_knowledge_base(query: str, space_key: str = KNOWLEDGE_SPACE, limit: int = 10) -> str:
    """Search IT-ES Knowledge space by keyword to find relevant content for test case creation."""
    params = {
        "cql": f'space = "{space_key}" AND text ~ "{query}" AND type = page',
        "limit": limit,
        "expand": "body.storage"
    }
    resp = requests.get(f"{ATLASSIAN_URL}/wiki/rest/api/search", params=params, auth=auth, headers=headers)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return f"ไม่พบข้อมูลที่เกี่ยวข้องกับ '{query}' ใน IT-ES Knowledge"
    import re
    lines = [f"พบ {len(results)} หน้าที่เกี่ยวข้องกับ '{query}':"]
    for r in results:
        content = r.get("excerpt", "")
        content = re.sub(r"<[^>]+>", " ", content).strip()
        lines.append(f"\n[{r['content']['id']}] {r['content']['title']}")
        if content:
            lines.append(f"  {content[:300]}...")
    return "\n".join(lines)


def create_confluence_page(space_key: str, title: str, content: str, parent_page_id: str = None) -> str:
    """Create a new page in Confluence (default: ITES Testcase knowledge space)."""
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": f"<p>{content}</p>", "representation": "storage"}}
    }
    if parent_page_id:
        payload["ancestors"] = [{"id": parent_page_id}]
    resp = requests.post(f"{ATLASSIAN_URL}/wiki/rest/api/content", json=payload, auth=auth, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    page_url = f"{ATLASSIAN_URL}/wiki{data['_links']['webui']}"
    return f"Created Confluence page: {data['id']} — {page_url}"


def update_confluence_page(page_id: str, title: str, content: str, version: int) -> str:
    payload = {
        "version": {"number": version + 1},
        "title": title,
        "type": "page",
        "body": {"storage": {"value": f"<p>{content}</p>", "representation": "storage"}}
    }
    resp = requests.put(f"{ATLASSIAN_URL}/wiki/rest/api/content/{page_id}", json=payload, auth=auth, headers=headers)
    resp.raise_for_status()
    return f"Updated Confluence page {page_id} to version {version + 1}"


CONFLUENCE_TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": "ค้นหาข้อมูลจาก IT-ES Knowledge space เพื่อนำไปสร้าง test cases",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "คำค้นหา เช่น 'login', 'payment', 'user registration'"},
                "limit": {"type": "integer", "description": "จำนวนผลลัพธ์สูงสุด (default: 10)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_confluence_page_content",
        "description": "อ่านเนื้อหาเต็มของ Confluence page เพื่อวิเคราะห์และสร้าง test cases",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "Page ID ที่ต้องการอ่าน"}
            },
            "required": ["page_id"]
        }
    },
    {
        "name": "get_confluence_pages",
        "description": "ดูรายการหน้าทั้งหมดใน Confluence space",
        "input_schema": {
            "type": "object",
            "properties": {
                "space_key": {"type": "string", "description": "Space key เช่น ITK หรือ space key ของ IT-ES Knowledge"},
                "title_filter": {"type": "string", "description": "กรองตามชื่อหน้า (optional)"},
                "limit": {"type": "integer", "description": "จำนวนสูงสุด (default: 25)"}
            },
            "required": ["space_key"]
        }
    },
    {
        "name": "create_confluence_page",
        "description": "สร้าง test case page ใหม่ใน ITES Testcase knowledge (ITK) หลังจากอ่านข้อมูลจาก IT-ES Knowledge แล้ว",
        "input_schema": {
            "type": "object",
            "properties": {
                "space_key": {"type": "string", "description": "Space key — ใช้ 'ITK' สำหรับ ITES Testcase knowledge"},
                "title": {"type": "string", "description": "ชื่อ test case"},
                "content": {"type": "string", "description": "เนื้อหา test case (steps, expected results)"},
                "parent_page_id": {"type": "string", "description": "ID ของ parent page (optional)"}
            },
            "required": ["space_key", "title", "content"]
        }
    },
    {
        "name": "update_confluence_page",
        "description": "อัปเดต test case page ที่มีอยู่แล้ว",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "Page ID"},
                "title": {"type": "string", "description": "ชื่อหน้า"},
                "content": {"type": "string", "description": "เนื้อหาใหม่"},
                "version": {"type": "integer", "description": "Version ปัจจุบัน"}
            },
            "required": ["page_id", "title", "content", "version"]
        }
    }
]
