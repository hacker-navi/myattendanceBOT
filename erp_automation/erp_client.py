import re
import time
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
        r"Overall\s*\(?%\)?\s*:?\s*([0-9]+(?:\.[0-9]+)?)\s*%?",
        r"Attendance\s*Percentage\s*([0-9]+(?:\.[0-9]+)?)",
        r"Attendance\s*%\s*:?\s*([0-9]+(?:\.[0-9]+)?)\s*%?",
        r"([0-9]+(?:\.[0-9]+)?)\s*%",
    ]

    for pattern in patterns:
        match = re.search(pattern, page_text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    raise RuntimeError("Could not extract attendance percentage from ERP page.")


def _calculate_overall_percent_from_subjects(subjects: List[Dict[str, str]]) -> str:
    total_held = 0
    total_present = 0

    for item in subjects:
        try:
            held = int(float(item["held"]))
            present = int(float(item["present"]))
        except (KeyError, TypeError, ValueError):
            continue

        if held <= 0:
            continue

        total_held += held
        total_present += present

    if total_held <= 0:
        raise RuntimeError("Could not derive overall attendance from subject rows.")

    percent = (total_present / total_held) * 100
    return f"{percent:.2f}".rstrip("0").rstrip(".")


def _extract_subject_rows_from_scope(scope) -> List[Dict[str, str]]:
    tables = scope.locator("table")
    table_count = tables.count()

    for index in range(table_count):
        table = tables.nth(index)
        try:
            table_text = table.inner_text()
        except Exception:
            continue
        if not re.search(r"Subject", table_text, flags=re.IGNORECASE):
            continue
        if not re.search(r"Held", table_text, flags=re.IGNORECASE):
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


def _extract_subject_rows(page) -> List[Dict[str, str]]:
    subjects = _extract_subject_rows_from_scope(page)
    if subjects:
        return subjects
    for frame in page.frames:
        subjects = _extract_subject_rows_from_scope(frame)
        if subjects:
            return subjects
    return []


def _launch_browser(playwright):
    browser_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-blink-features=AutomationControlled",
    ]
    launch_attempts = [
        ("bundled-chromium", {"headless": HEADLESS, "args": browser_args}),
        ("chrome", {"headless": HEADLESS, "channel": "chrome", "args": browser_args}),
        ("msedge", {"headless": HEADLESS, "channel": "msedge", "args": browser_args}),
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
    username = ERP_USERNAME.strip()
    password = ERP_PASSWORD.strip()
    if not username or not password:
        raise RuntimeError("Missing ERP_USERNAME or ERP_PASSWORD in .env / GitHub Secrets")

    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
        )
        page = context.new_page()

        # Handle any alert or confirm dialogs automatically
        def _handle_dialog(dialog):
            print(f"ERP Dialog appeared: '{dialog.message}' -> accepting")
            try:
                dialog.accept()
            except Exception:
                pass

        page.on("dialog", _handle_dialog)

        # Capture login API responses for precise diagnostics
        login_api_response = {"status": None, "body": ""}

        def _on_response(res):
            if "Default.aspx/Login" in res.url or "PageMethods" in res.url:
                try:
                    login_api_response["status"] = res.status
                    login_api_response["body"] = res.text()
                    print(f"Login API response: status={res.status}, body={res.text()[:200]}")
                except Exception:
                    pass

        page.on("response", _on_response)

        try:
            page.goto(ERP_LOGIN_URL, timeout=45000, wait_until="domcontentloaded")

            user_ok = _fill_first(
                page,
                [
                    "#txtusername",
                    "input[name='txtusername']",
                    "input[name*='User' i][type='text']",
                    "input[type='text']",
                ],
                username,
            )
            pass_ok = _fill_first(
                page,
                [
                    "#txtpassword",
                    "input[name='txtpassword']",
                    "input[name*='Pass' i][type='password']",
                    "input[type='password']",
                ],
                password,
            )

            if not user_ok or not pass_ok:
                raise RuntimeError("Login fields were not found on ERP login page.")

            initial_url = page.url

            clicked = _click_first(
                page,
                [
                    "button.btn.blue",
                    "button:has-text('Login')",
                    "button[onclick*='login']",
                    "input[type='submit']",
                ],
            )
            if not clicked:
                try:
                    page.evaluate("() => typeof login === 'function' && login()")
                    clicked = True
                except Exception:
                    page.keyboard.press("Enter")

            # Wait dynamically up to 25s for login submission and redirect
            start_login = time.time()
            login_success = False
            while time.time() - start_login < 25:
                # When PageMethods.Login succeeds, the portal redirects to /Home/ or /Fee/...
                if page.url != initial_url:
                    login_success = True
                    break

                # Check if server explicitly returned an error response
                api_body = login_api_response.get("body", "")
                if api_body and ("check User Name" in api_body or "Invalid" in api_body or "Error" in api_body):
                    break

                page.wait_for_timeout(500)

            if not login_success:
                page.screenshot(path="attendance_error.png")
                err_text = ""
                try:
                    alert_el = page.locator("#alert_container, #alert_div").first
                    if alert_el.is_visible(timeout=500):
                        err_text = alert_el.inner_text().replace("×", "").strip()
                except Exception:
                    pass

                if not err_text and login_api_response.get("body"):
                    err_text = login_api_response["body"]

                err_detail = f" Server response: '{err_text}'." if err_text else ""
                raise RuntimeError(
                    f"Authentication failed.{err_detail} URL did not change after login ({page.url}). "
                    "Please verify ERP_USERNAME and ERP_PASSWORD in GitHub Secrets."
                )

            # Session is established! Navigate to attendance page
            page.wait_for_timeout(1000)
            page.goto(ERP_ATTENDANCE_URL, timeout=45000, wait_until="domcontentloaded")

            # Check if ERP redirected back to login (indicates invalid credentials or session rejection)
            if "login" in page.url.lower():
                page.screenshot(path="attendance_error.png")
                # Check for error text on login page
                err_text = ""
                try:
                    for sel in [".error", "#lblError", "[id*='error' i]", "[class*='alert' i]", "font[color='red']"]:
                        el = page.locator(sel).first
                        if el.is_visible(timeout=500):
                            err_text = el.inner_text().strip()
                            if err_text:
                                break
                except Exception:
                    pass

                err_detail = f" Message on page: '{err_text}'" if err_text else ""
                raise RuntimeError(
                    f"Authentication failed: ERP redirected back to login ({page.url}).{err_detail} "
                    "Please verify ERP_USERNAME and ERP_PASSWORD in GitHub Secrets."
                )

            _click_first(
                page,
                [
                    "button:has-text('Attendance')",
                    "a:has-text('Attendance')",
                    "input[value*='Attendance' i]",
                    "[id*='Attendance' i]",
                    "span:has-text('Attendance')",
                    "text=Attendance",
                    "text=attandance",
                ],
            )

            # Wait dynamically up to 25s for attendance table and percentage to load
            start_time = time.time()
            max_wait = 25
            subjects = []
            percent = ""

            while time.time() - start_time < max_wait:
                subjects = _extract_subject_rows(page)
                try:
                    body_text = page.locator("body").inner_text()
                    percent = _extract_attendance_percent(body_text)
                except Exception:
                    if subjects:
                        try:
                            percent = _calculate_overall_percent_from_subjects(subjects)
                        except Exception:
                            percent = ""

                if subjects and percent:
                    break

                page.wait_for_timeout(1000)

            if not percent and subjects:
                try:
                    percent = _calculate_overall_percent_from_subjects(subjects)
                except Exception:
                    pass

            if not subjects or not percent:
                try:
                    page.screenshot(path="attendance_error.png")
                    print("Attendance load incomplete. Saved debug screenshot to attendance_error.png")
                except Exception:
                    pass

                if not HEADLESS:
                    page.wait_for_timeout(5000)

                raise RuntimeError(
                    f"Could not extract attendance data. Found {len(subjects)} subjects, percent='{percent}'. "
                    f"Current URL: {page.url}"
                )

            source = page.url
            return {"percent": percent, "source": source, "subjects": subjects}
        finally:
            context.close()
            browser.close()
