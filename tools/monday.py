import requests
from config import MONDAY_API_KEY, MONDAY_BOARD_ID


def _headers():
    return {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json",
    }


def _query(query: str, variables: dict = None) -> dict:
    url = "https://api.monday.com/v2"
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def get_items(board_id: str = None) -> list:
    bid = board_id or MONDAY_BOARD_ID
    query = """
    query ($boardId: ID!) {
        boards(ids: [$boardId]) {
            items_page { items { id name state column_values { id text } } }
        }
    }
    """
    result = _query(query, {"boardId": bid})
    boards = result.get("data", {}).get("boards", [])
    if boards:
        return boards[0].get("items_page", {}).get("items", [])
    return []


def create_item(item_name: str, board_id: str = None) -> dict:
    bid = board_id or MONDAY_BOARD_ID
    query = """
    mutation ($boardId: ID!, $itemName: String!) {
        create_item(board_id: $boardId, item_name: $itemName) { id name }
    }
    """
    result = _query(query, {"boardId": bid, "itemName": item_name})
    return result.get("data", {}).get("create_item", {})


def update_item_status(item_id: str, column_id: str, status_label: str) -> dict:
    query = """
    mutation ($itemId: ID!, $boardId: ID!, $columnId: String!, $value: JSON!) {
        change_simple_column_value(item_id: $itemId, board_id: $boardId, column_id: $columnId, value: $value) { id }
    }
    """
    result = _query(query, {
        "itemId": item_id,
        "boardId": MONDAY_BOARD_ID,
        "columnId": column_id,
        "value": status_label,
    })
    return result.get("data", {})


MONDAY_TOOLS = [
    {
        "name": "monday_get_items",
        "description": "Get all items from a Monday.com board",
        "input_schema": {
            "type": "object",
            "properties": {"board_id": {"type": "string", "description": "Board ID (optional, uses default)"}},
        },
    },
    {
        "name": "monday_create_item",
        "description": "Create a new item on a Monday.com board",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string"},
                "board_id": {"type": "string"},
            },
            "required": ["item_name"],
        },
    },
    {
        "name": "monday_update_item_status",
        "description": "Update the status column of a Monday.com item",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "column_id": {"type": "string"},
                "status_label": {"type": "string"},
            },
            "required": ["item_id", "column_id", "status_label"],
        },
    },
]


def handle_monday_tool(tool_name: str, tool_input: dict):
    if tool_name == "monday_get_items":
        return get_items(**tool_input)
    elif tool_name == "monday_create_item":
        return create_item(**tool_input)
    elif tool_name == "monday_update_item_status":
        return update_item_status(**tool_input)
