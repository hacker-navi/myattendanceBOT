# GitHub Actions Workflow Fix Guide

See [change.md](change.md) for the full detailed guide.

## Summary of Fixes

### 1. Runner Compatibility Fix
- **File:** `.github/workflows/attendance-check.yml` (around Line 14)
- **Change:** Changed `runs-on: ubuntu-latest` to `runs-on: ubuntu-24.04`
- **Why:** GitHub updated `ubuntu-latest` to an environment (`ubuntu26.04-x64`) that Playwright does not yet support.

### 2. Login & AJAX Submission Fix
- **File:** `erp_automation/erp_client.py`
- **Change:** 
  1. Targeted the real login button (`button.btn.blue, button[onclick*='login']`) instead of the `<h4>` heading.
  2. Waited dynamically for `page.url != initial_url` (since `PageMethods.Login` redirects to `/Home/` or `/Fee/...` upon success).
  3. Added desktop Chrome user-agent, anti-bot flags, and auto dialog handler.
- **Why:** The login uses ASP.NET AJAX (`PageMethods.Login`). Navigating before the AJAX call completed aborted the request, causing ERP to redirect back to login.

### 3. Screenshot Artifact on Failure
- **File:** `.github/workflows/attendance-check.yml`
- **Change:** Added `actions/upload-artifact@v4` on failure to preserve `attendance_error.png` in GitHub Actions for easy debugging.
