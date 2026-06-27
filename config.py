import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "QA")

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")

VANSAH_API_TOKEN = os.getenv("VANSAH_API_TOKEN")
VANSAH_BASE_URL = os.getenv("VANSAH_BASE_URL", "https://prod.vansah.com/api/v1")

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")

PLAYWRIGHT_BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost:3000")
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
PLAYWRIGHT_TIMEOUT = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))
PLAYWRIGHT_SCREENSHOTS_DIR = os.getenv("PLAYWRIGHT_SCREENSHOTS_DIR", "./test-results/screenshots")

CURSOR_AI_API_KEY = os.getenv("CURSOR_AI_API_KEY")
CURSOR_AI_BASE_URL = os.getenv("CURSOR_AI_BASE_URL", "https://api.cursor.sh")

AS400_HOST = os.getenv("AS400_HOST")
AS400_PORT = int(os.getenv("AS400_PORT", "446"))
AS400_USERNAME = os.getenv("AS400_USERNAME")
AS400_PASSWORD = os.getenv("AS400_PASSWORD")
AS400_LIBRARY = os.getenv("AS400_LIBRARY")
AS400_DATABASE = os.getenv("AS400_DATABASE")

JMETER_HOME = os.getenv("JMETER_HOME", "/usr/local/apache-jmeter")
JMETER_RESULTS_DIR = os.getenv("JMETER_RESULTS_DIR", "./jmeter-results")
JMETER_TEST_PLAN_DIR = os.getenv("JMETER_TEST_PLAN_DIR", "./jmeter-plans")
JMETER_REMOTE_HOST = os.getenv("JMETER_REMOTE_HOST")

K6_CLOUD_TOKEN = os.getenv("K6_CLOUD_TOKEN")
K6_CLOUD_PROJECT_ID = os.getenv("K6_CLOUD_PROJECT_ID")
K6_BASE_URL = os.getenv("K6_BASE_URL", "http://localhost:3000")
K6_RESULTS_DIR = os.getenv("K6_RESULTS_DIR", "./k6-results")
K6_VUS = int(os.getenv("K6_VUS", "10"))
K6_DURATION = os.getenv("K6_DURATION", "30s")

POSTMAN_API_KEY = os.getenv("POSTMAN_API_KEY")
POSTMAN_WORKSPACE_ID = os.getenv("POSTMAN_WORKSPACE_ID")
POSTMAN_COLLECTION_ID = os.getenv("POSTMAN_COLLECTION_ID")
POSTMAN_ENVIRONMENT_ID = os.getenv("POSTMAN_ENVIRONMENT_ID")
