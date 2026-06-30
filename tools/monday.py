import json
import requests
from config import MONDAY_API_TOKEN

MONDAY_API_URL = "https://api.monday.com/v2"
headers = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json"
}

# G7 workspace constants
G7_WORKSPACE_ID = "382526"
PROJECT_QA_BOARD_ID = "5025911240"  # 2026 New Board Project QA


def update_monday_item(board_id: str = PROJECT_QA_BOARD_ID, item_name: str = "", status: str = "", group_id: str = None) -> str:
    mutation = """
    mutation ($boardId: ID!, $itemName: String!, $groupId: String, $colVals: JSON) {
        create_item (
            board_id: $boardId
            item_name: $itemName
            group_id: $groupId
            column_values: $colVals
        ) {
            id
            name
        }
    }
    """
    variables = {
        "boardId": str(board_id),
        "itemName": item_name,
        "groupId": group_id,
        "colVals": json.dumps({"status": {"label": status}}) if status else None,
    }
    resp = requests.post(MONDAY_API_URL, json={"query": mutation, "variables": variables}, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        return f"Monday.com error: {data['errors']}"
    item = data["data"]["create_item"]
    return f"Created Monday item: {item['name']} (ID: {item['id']}) with status '{status}'"


def get_monday_items(board_id: str = PROJECT_QA_BOARD_ID) -> str:
    query = f"""
    query {{
        boards(ids: [{board_id}]) {{
            name
            items_page {{
                items {{
                    id
                    name
                    column_values {{
                        column {{ title }}
                        text
                    }}
                }}
            }}
        }}
    }}
    """
    resp = requests.post(MONDAY_API_URL, json={"query": query}, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        return f"Monday.com error: {data['errors']}"
    boards = data["data"]["boards"]
    if not boards:
        return f"Board {board_id} not found"
    items = boards[0]["items_page"]["items"]
    lines = [f"Board: {boards[0]['name']} ({len(items)} items)"]
    for item in items:
        status = next((cv["text"] for cv in item["column_values"] if cv["column"]["title"].lower() == "status"), "N/A")
        lines.append(f"  - [{item['id']}] {item['name']} | Status: {status}")
    return "\n".join(lines)


MONDAY_TOOLS = [
    {
        "name": "update_monday_item",
        "description": "สร้าง item ใหม่ใน Monday.com board พร้อม status — default คือ '2026 New Board Project QA' (ID: 5025911240) ใน G7 workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "board_id": {"type": "string", "description": f"Monday.com Board ID (default: {PROJECT_QA_BOARD_ID} = 2026 New Board Project QA, G7 workspace)"},
                "item_name": {"type": "string", "description": "ชื่อ item"},
                "status": {"type": "string", "description": "สถานะ เช่น Done, In Progress, Stuck"},
                "group_id": {"type": "string", "description": "Group ID (optional)"}
            },
            "required": ["board_id", "item_name", "status"]
        }
    },
    {
        "name": "get_monday_items",
        "description": "ดึงรายการ items ทั้งหมดจาก Monday.com board — default คือ '2026 New Board Project QA' (ID: 5025911240) ใน G7 workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "board_id": {"type": "string", "description": f"Monday.com Board ID (default: {PROJECT_QA_BOARD_ID} = 2026 New Board Project QA, G7 workspace)"}
            },
            "required": ["board_id"]
        }
    }
]
