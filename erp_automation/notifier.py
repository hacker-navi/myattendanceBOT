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
    class_updates,
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

    if class_updates:
        lines.append("")
        lines.append("🆕 Updated classes:")
        for update in class_updates:
            subject = update["subject"]
            held_before = update["held_before"]
            held_after = update["held_after"]
            present_before = update["present_before"]
            present_after = update["present_after"]
            change = update["change"]
            lines.append(
                f"• {subject} ({change}) Held: {held_before}->{held_after}, Present: {present_before}->{present_after}"
            )

        subject_map = {item["subject"]: item for item in subjects}
        today_lines = []
        for update in class_updates:
            subject = update["subject"]
            try:
                held_before = int(update.get("held_before", 0))
                held_after = int(update.get("held_after", 0))
                present_before = int(update.get("present_before", 0))
                present_after = int(update.get("present_after", 0))
            except (TypeError, ValueError):
                continue

            new_held = held_after - held_before
            new_present = present_after - present_before
            new_absent = new_held - new_present

            if held_before == 0 and held_after > 5:
                continue

            subj_item = subject_map.get(subject, {})
            percent = subj_item.get("percent") if subj_item.get("percent") is not None else update.get("percent", "")
            icon = _status_icon(str(percent))

            if new_held > 0:
                if new_present == new_held:
                    status_text = "✅ Attended"
                elif new_present == 0:
                    status_text = "❌ Absent"
                elif new_present > 0 and new_absent > 0:
                    status_text = f"✅ {new_present} Attended, ❌ {new_absent} Absent"
                elif new_present > new_held:
                    status_text = f"✅ Attended (+{new_present})"
                else:
                    status_text = "❌ Absent"
                detail_line = f"➕ New: {new_held} | {status_text}"
            else:
                if new_present > 0:
                    detail_line = f"✅ Attended: +{new_present}"
                elif new_present < 0:
                    detail_line = f"❌ Absent ({new_present})"
                else:
                    detail_line = "ℹ️ Updated"

            today_lines.extend(["", f"{icon} {subject}", detail_line])

        if today_lines:
            lines.extend(["", "====================", "", "🆕 TODAY'S CLASS UPDATES"])
            lines.extend(today_lines)

    return "\n".join(lines)
