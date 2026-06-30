import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
AGENT_ID = os.environ.get("AGENT_ID")

ATLASSIAN_URL = os.environ.get("ATLASSIAN_URL")
ATLASSIAN_EMAIL = os.environ.get("ATLASSIAN_EMAIL")
ATLASSIAN_API_TOKEN = os.environ.get("ATLASSIAN_API_TOKEN")

VANSAH_API_TOKEN = os.environ.get("VANSAH_API_TOKEN")
VANSAH_URL = os.environ.get("VANSAH_URL", "https://prod.vansah.com/vansah-io/api/v1")

MONDAY_API_TOKEN = os.environ.get("MONDAY_API_TOKEN")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

BASE_URL = os.environ.get("BASE_URL", "https://example.com")
