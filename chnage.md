# GitHub Actions Workflow Fix Guide

See [change.md](change.md) for the full detailed guide.

## Summary of Fixes

### 1. Runner Compatibility Fix
- **File:** `.github/workflows/attendance-check.yml` (around Line 14)
- **Change:** Changed `runs-on: ubuntu-latest` to `runs-on: ubuntu-24.04`
- **Why:** GitHub updated `ubuntu-latest` to an environment (`ubuntu26.04-x64`) that Playwright does not yet support.

### 2. Direct API Login (Bypasses Server-Side Thai SEO Spam)
- **File:** `erp_automation/erp_client.py`
- **Change:** Directly POSTs credentials to `https://erp.lbrce.ac.in/Default.aspx/Login` to obtain session cookies (`ASP.NET_SessionId` and `ERP`), completely bypassing the defaced HTML and JavaScript login form.
- **Why:** The college server was infected with Thai gambling SEO spam that only targets foreign/cloud IP addresses (like GitHub Actions runners). That injection broke client-side JavaScript on the page. Direct API login bypasses the corrupted UI entirely.

### 3. Screenshot Artifact on Failure
- **File:** `.github/workflows/attendance-check.yml`
- **Change:** Added `actions/upload-artifact@v4` on failure to preserve `attendance_error.png` in GitHub Actions for easy debugging.
