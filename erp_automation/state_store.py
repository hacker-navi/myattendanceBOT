import json
from pathlib import Path
from typing import Dict

from erp_automation.config import STATE_FILE


DEFAULT_STATE = {
    "last_percent": "",
    "last_checked_at": "",
    "subjects": {},
}


def load_state() -> Dict[str, str]:
    state_path = Path(STATE_FILE)
    if not state_path.exists():
        return dict(DEFAULT_STATE)

    try:
        raw = state_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return dict(DEFAULT_STATE)
        merged = dict(DEFAULT_STATE)
        merged["last_percent"] = str(data.get("last_percent", ""))
        merged["last_checked_at"] = str(data.get("last_checked_at", ""))

        subjects = data.get("subjects", {})
        merged["subjects"] = subjects if isinstance(subjects, dict) else {}
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_STATE)


def save_state(state: Dict[str, str]) -> None:
    state_path = Path(STATE_FILE)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
