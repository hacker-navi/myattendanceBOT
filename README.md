# ERP Attendance Automation

This project automates your ERP attendance check by:

- Logging in to https://erp.lbrce.ac.in/
- Opening the student attendance page
- Clicking the Attendance section
- Extracting overall attendance percentage
- Extracting subject-wise attendance rows
- Sending Telegram notification
- Running either every 3 hours or at specific schedule times
- Running automatically via GitHub Actions

## Project Structure

```
LBRCE_ATT/
├── .github/workflows/
│   └── attendance-check.yml
├── erp_automation/
│   ├── __init__.py
│   ├── config.py
│   ├── erp_client.py
│   ├── notifier.py
│   └── state_store.py
├── attendance_state.json
├── check_attendance_once.py
├── run_attendance_scheduler.py
├── .env.example
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.9+
- Internet access to ERP portal

## Setup

1. Create and activate virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

3. Configure environment.

```bash
copy .env.example .env
```

Edit `.env` and set at minimum:

- `ERP_USERNAME`
- `ERP_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Run

### One-time check

```bash
python check_attendance_once.py
```

### Scheduled checks

```bash
python run_attendance_scheduler.py
```

Scheduler behavior:

- If `CHECK_TIMES` is empty, it runs every `CHECK_INTERVAL_HOURS` (default 3).
- If `CHECK_TIMES` has values like `09:00,13:00,18:00`, it runs at those times daily.

## Telegram Output Format

The notification is sent like:

```text
📊 ATTENDANCE UPDATE
🕒 23/02/2026 03:24
📈 Overall: 84.53 %

🟡 Compiler Design 29/35 82.9%
...

====================

➖ No new classes
```

Rules:

- `🟢` for >= 90%
- `🟡` for >= 75% and < 90%
- `🔴` for < 75%
- Bottom line shows `No new classes` when total held classes did not increase since last saved state.

## GitHub Actions Automation

Workflow file: `.github/workflows/attendance-check.yml`

It runs every 3 hours and can also be started manually with `workflow_dispatch`.

### Required GitHub Secrets

Set these in your repository Settings -> Secrets and variables -> Actions:

- `ERP_LOGIN_URL` (example: `https://erp.lbrce.ac.in/`)
- `ERP_ATTENDANCE_URL` (example: `https://erp.lbrce.ac.in/Discipline/StudentHistory.aspx`)
- `ERP_USERNAME`
- `ERP_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

The workflow commits updated `attendance_state.json` back to your repo to keep history for change detection.

## Notes

- `HEADLESS=true` runs browser in background.
- `ALWAYS_NOTIFY=false` sends Telegram only when attendance changes.
- Local state is saved in `attendance_state.json`.
