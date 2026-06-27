import requests
from requests.auth import HTTPBasicAuth
from config import CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN, CONFLUENCE_SPACE_KEY


def _auth():
    return HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)


def _headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}


def get_page(page_id: str) -> dict:
    url = f"{CONFLUENCE_BASE_URL}/wiki/rest/api/content/{page_id}?expand=body.storage"
    resp = requests.get(url, auth=_auth(), headers=_headers())
    resp.raise_for_status()
    return resp.json()


def search_pages(query: str, limit: int = 10) -> list:
    url = f"{CONFLUENCE_BASE_URL}/wiki/rest/api/content/search"
    params = {"cql": f'space="{CONFLUENCE_SPACE_KEY}" AND text~"{query}"', "limit": limit}
    resp = requests.get(url, auth=_auth(), headers=_headers(), params=params)
    resp.raise_for_status()
    return resp.json().get("results", [])


def create_page(title: str, content: str, parent_id: str = None) -> dict:
    url = f"{CONFLUENCE_BASE_URL}/wiki/rest/api/content"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {"storage": {"value": content, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]
    resp = requests.post(url, json=payload, auth=_auth(), headers=_headers())
    resp.raise_for_status()
    return resp.json()


def update_page(page_id: str, title: str, content: str, version: int) -> dict:
    url = f"{CONFLUENCE_BASE_URL}/wiki/rest/api/content/{page_id}"
    payload = {
        "version": {"number": version + 1},
        "title": title,
        "type": "page",
        "body": {"storage": {"value": content, "representation": "storage"}},
    }
    resp = requests.put(url, json=payload, auth=_auth(), headers=_headers())
    resp.raise_for_status()
    return resp.json()


CONFLUENCE_TOOLS = [
    {
        "name": "confluence_get_page",
        "description": "Get a Confluence page by its ID",
        "input_schema": {
            "type": "object",
            "properties": {"page_id": {"type": "string"}},
            "required": ["page_id"],
        },
    },
    {
        "name": "confluence_search_pages",
        "description": "Search Confluence pages by keyword",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "confluence_create_page",
        "description": "Create a new Confluence page",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string", "description": "HTML or Confluence storage format"},
                "parent_id": {"type": "string", "description": "Optional parent page ID"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "confluence_update_page",
        "description": "Update an existing Confluence page",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "version": {"type": "integer", "description": "Current version number"},
            },
            "required": ["page_id", "title", "content", "version"],
        },
    },
]


def handle_confluence_tool(tool_name: str, tool_input: dict):
    if tool_name == "confluence_get_page":
        return get_page(**tool_input)
    elif tool_name == "confluence_search_pages":
        return search_pages(**tool_input)
    elif tool_name == "confluence_create_page":
        return create_page(**tool_input)
    elif tool_name == "confluence_update_page":
        return update_page(**tool_input)
