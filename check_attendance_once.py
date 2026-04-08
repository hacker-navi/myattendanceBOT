from datetime import datetime

from erp_automation.config import ALWAYS_NOTIFY
from erp_automation.erp_client import fetch_overall_attendance
from erp_automation.notifier import (
    build_attendance_update_message,
    send_telegram_message,
)
from erp_automation.state_store import load_state, save_state


def _to_int(value: str) -> int:
    return int(float(value))


def _build_subject_map(subjects):
    out = {}
    for item in subjects:
        out[item["subject"]] = {
            "held": _to_int(item["held"]),
            "present": _to_int(item["present"]),
            "percent": item["percent"],
        }
    return out


def _detect_no_new_classes(previous_subjects, current_subjects) -> bool:
    if not previous_subjects or not current_subjects:
        return False

    for subject_name, current in current_subjects.items():
        previous = previous_subjects.get(subject_name)
        if previous is None:
            return False
        if current["held"] > int(previous.get("held", 0)):
            return False
    return True


def run_check() -> bool:
    result = fetch_overall_attendance()
    percent = result["percent"]
    subjects = result.get("subjects", [])

    state = load_state()
    previous_subjects = state.get("subjects", {})
    current_subjects = _build_subject_map(subjects)

    overall_changed = state.get("last_percent", "") != percent
    classes_changed = previous_subjects != current_subjects
    changed = overall_changed or classes_changed
    no_new_classes = _detect_no_new_classes(previous_subjects, current_subjects)

    print(f"Current overall attendance: {percent}%")
    print(f"Subjects parsed: {len(subjects)}")

    should_notify = changed or ALWAYS_NOTIFY
    if should_notify:
        message = build_attendance_update_message(
            overall_percent=percent,
            subjects=subjects,
            no_new_classes=no_new_classes,
        )
        sent = send_telegram_message(message)
        print("Telegram sent." if sent else "Telegram not sent (check bot config).")

    state["last_percent"] = percent
    state["last_checked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state["subjects"] = current_subjects
    save_state(state)

    if changed:
        print("Attendance changed since last check.")
    else:
        print("No attendance change since last check.")

    return changed


if __name__ == "__main__":
    try:
        run_check()
    except Exception as exc:
        print(f"Attendance check failed: {exc}")
        raise
