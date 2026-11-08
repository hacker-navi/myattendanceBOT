# GitHub Actions Workflow Fix Guide

See [change.md](change.md) for the full detailed guide.

## Summary of Fixes

### 1. Runner Compatibility Fix
- **File:** `.github/workflows/attendance-check.yml` (around Line 14)
- **Change:** Changed `runs-on: ubuntu-latest` to `runs-on: ubuntu-24.04`
- **Why:** GitHub updated `ubuntu-latest` to an environment (`ubuntu26.04-x64`) that Playwright does not yet support.

### 2. Login & Latency Fix
- **File:** `erp_automation/erp_client.py`
- **Change:** Dynamic wait for login redirect (up to 15s instead of 3s), trimmed credentials, desktop Chrome user-agent, auto dialog dismissal, and clearer authentication error reporting.
- **Why:** Cloud runners experienced high latency connecting to the college ERP server, causing navigation before session cookies finished registering.

### 3. Screenshot Artifact on Failure
- **File:** `.github/workflows/attendance-check.yml`
- **Change:** Added `actions/upload-artifact@v4` on failure to preserve `attendance_error.png` in GitHub Actions for easy debugging.
