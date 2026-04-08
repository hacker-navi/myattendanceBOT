from datetime import datetime
from zoneinfo import ZoneInfo

from erp_automation.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE

import requests


def send_telegram_message(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, data=payload, timeout=20)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def _status_icon(percent_text: str) -> str:
    try:
        value = float(percent_text)
    except ValueError:
        return "⚪"

    if value >= 90:
        return "🟢"
    if value >= 75:
        return "🟡"
    return "🔴"


def build_attendance_update_message(
    overall_percent: str,
    subjects,
    no_new_classes: bool,
) -> str:
    now = datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M")

    lines = [
        "📊 ATTENDANCE UPDATE",
        f"🕒 {now}",
        f"📈 Overall: {overall_percent} %",
        "",
    ]

    for item in subjects:
        icon = _status_icon(item["percent"])
        lines.append(
            f"{icon} {item['subject']} {item['present']}/{item['held']} {item['percent']}%"
        )

    lines.extend(["", "====================", ""])
    lines.append("➖ No new classes" if no_new_classes else "✅ New class data found")

    return "\n".join(lines)
