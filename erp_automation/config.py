import os
from dotenv import load_dotenv


load_dotenv()


ERP_LOGIN_URL = os.getenv("ERP_LOGIN_URL", "https://erp.lbrce.ac.in/")
ERP_ATTENDANCE_URL = os.getenv(
    "ERP_ATTENDANCE_URL", "https://erp.lbrce.ac.in/Discipline/StudentHistory.aspx"
)
ERP_USERNAME = os.getenv("ERP_USERNAME", "")
ERP_PASSWORD = os.getenv("ERP_PASSWORD", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

HEADLESS = os.getenv("HEADLESS", "true").strip().lower() in {"1", "true", "yes", "y"}
CHECK_INTERVAL_HOURS = float(os.getenv("CHECK_INTERVAL_HOURS", "3"))
CHECK_TIMES = os.getenv("CHECK_TIMES", "")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
ALWAYS_NOTIFY = os.getenv("ALWAYS_NOTIFY", "false").strip().lower() in {"1", "true", "yes", "y"}
STATE_FILE = os.getenv("STATE_FILE", "attendance_state.json")
