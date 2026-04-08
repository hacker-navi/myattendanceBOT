import re
from typing import Dict, List

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from erp_automation.config import (
    ERP_ATTENDANCE_URL,
    ERP_LOGIN_URL,
    ERP_PASSWORD,
    ERP_USERNAME,
    HEADLESS,
)


def _fill_first(page, selectors, value: str) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=3000)
            locator.fill(value)
            return True
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue
    return False


def _click_first(page, selectors) -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=3000)
            locator.click()
            return True
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue
    return False


def _extract_attendance_percent(page_text: str) -> str:
    patterns = [
        r"Overall\(%\)\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%",
        r"Attendance\s*Percentage\s*([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*%",
    ]

    for pattern in patterns:
        match = re.search(pattern, page_text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    raise RuntimeError("Could not extract attendance percentage from ERP page.")


def _extract_subject_rows(page) -> List[Dict[str, str]]:
    tables = page.locator("table")
    table_count = tables.count()

    for index in range(table_count):
        table = tables.nth(index)
        table_text = table.inner_text()
        if not re.search(r"Subject", table_text, flags=re.IGNORECASE):
            continue
        if not re.search(r"Classes\s*Held", table_text, flags=re.IGNORECASE):
            continue

        rows = table.locator("tr")
        row_count = rows.count()
        subjects: List[Dict[str, str]] = []

        for row_index in range(row_count):
            row = rows.nth(row_index)
            cells = [cell.inner_text().strip() for cell in row.locator("th,td").all()]
            if len(cells) < 5:
                continue

            if re.search(r"Subject", cells[0], flags=re.IGNORECASE) or re.search(
                r"Subject", cells[1], flags=re.IGNORECASE
            ):
                continue

            subject_name = cells[1]
            held = cells[2]
            present = cells[3]
            percent = cells[4].replace("%", "").strip()

            if not subject_name:
                continue
            if not re.match(r"^\d+(?:\.\d+)?$", held):
                continue
            if not re.match(r"^\d+(?:\.\d+)?$", present):
                continue
            if not re.match(r"^\d+(?:\.\d+)?$", percent):
                continue

            subjects.append(
                {
                    "subject": subject_name,
                    "held": held,
                    "present": present,
                    "percent": percent,
                }
            )

        if subjects:
            return subjects

    return []


def _launch_browser(playwright):
    launch_attempts = [
        ("bundled-chromium", {"headless": HEADLESS}),
        ("chrome", {"headless": HEADLESS, "channel": "chrome"}),
        ("msedge", {"headless": HEADLESS, "channel": "msedge"}),
    ]

    last_error = None
    for _, kwargs in launch_attempts:
        try:
            return playwright.chromium.launch(**kwargs)
        except PlaywrightError as exc:
            last_error = exc

    raise RuntimeError(
        "Could not launch any browser. Install Chromium with 'python -m playwright install chromium' "
        "or ensure Chrome/Edge is installed locally."
    ) from last_error


def fetch_overall_attendance() -> Dict[str, object]:
    if not ERP_USERNAME or not ERP_PASSWORD:
        raise RuntimeError("Missing ERP_USERNAME or ERP_PASSWORD in .env")

    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(ERP_LOGIN_URL, timeout=45000, wait_until="domcontentloaded")

            user_ok = _fill_first(
                page,
                [
                    "input[name*='User'][type='text']",
                    "input[id*='User'][type='text']",
                    "input[type='text']",
                ],
                ERP_USERNAME,
            )
            pass_ok = _fill_first(
                page,
                [
                    "input[name*='Pass'][type='password']",
                    "input[id*='Pass'][type='password']",
                    "input[type='password']",
                ],
                ERP_PASSWORD,
            )

            if not user_ok or not pass_ok:
                raise RuntimeError("Login fields were not found on ERP login page.")

            clicked = _click_first(
                page,
                [
                    "button:has-text('Login')",
                    "input[type='submit']",
                    "text=Login",
                ],
            )
            if not clicked:
                page.keyboard.press("Enter")

            page.wait_for_timeout(3000)
            page.goto(ERP_ATTENDANCE_URL, timeout=45000, wait_until="domcontentloaded")

            _click_first(
                page,
                [
                    "button:has-text('Attendance')",
                    "a:has-text('Attendance')",
                    "text=Attendance",
                    "text=attandance",
                ],
            )
            page.wait_for_timeout(2500)

            body_text = page.locator("body").inner_text()
            percent = _extract_attendance_percent(body_text)
            subjects = _extract_subject_rows(page)
            source = page.url

            return {"percent": percent, "source": source, "subjects": subjects}
        finally:
            context.close()
            browser.close()
