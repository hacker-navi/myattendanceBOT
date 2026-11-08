# GitHub Actions Workflow Fix Guide

## 1. What Was the Error?
In GitHub Actions, the workflow failed at the step `Install dependencies` with the following message:

```text
BEWARE: your OS is not officially supported by Playwright; installing dependencies for ubuntu26.04-x64 as a fallback.
Cannot install dependencies for ubuntu26.04-x64 with Playwright 1.52.0!
Failed to install browsers
Error: ERROR: Playwright does not support chromium on ubuntu26.04-x64
```

---

## 2. Why Did It Occur?
* In the GitHub Actions workflow file, the virtual runner OS was defined as:
  ```yaml
  runs-on: ubuntu-latest
  ```
* GitHub recently updated `ubuntu-latest` to an environment running an unsupported or preview Ubuntu version (`ubuntu26.04`).
* Playwright (including version `1.52.0`) does not yet have precompiled OS packages or official support for Ubuntu 26.04.
* When `python -m playwright install --with-deps chromium` ran, it checked `/etc/os-release`, detected `ubuntu26.04-x64`, and aborted because dependency packages could not be located.

---

## 3. What Changes Were Made?

### **File Modified:**
📁 `.github/workflows/attendance-check.yml` (Line 14)

### **Diff / Exact Change:**

#### ❌ Before:
```yaml
jobs:
  check-attendance:
    runs-on: ubuntu-latest
```

#### ✅ After:
```yaml
jobs:
  check-attendance:
    runs-on: ubuntu-24.04
```

---

## 4. How to Apply This to Your Friend's Workflow

If your friends are experiencing the same error in their repositories:

1. Open their repository on GitHub (or locally in VS Code / IDE).
2. Open the workflow file:
   `.github/workflows/attendance-check.yml` (or whatever their `.yml` file is named inside `.github/workflows/`).
3. Search for:
   ```yaml
   runs-on: ubuntu-latest
   ```
4. Replace it with:
   ```yaml
   runs-on: ubuntu-24.04
   ```
5. Commit and push the change to GitHub:
   ```bash
   git add .github/workflows/
   git commit -m "fix: pin ubuntu runner to 24.04 for Playwright compatibility"
   git push origin main
   ```
6. Re-run the workflow in **GitHub Actions** -> It will use Ubuntu 24.04 LTS and install Playwright Chromium without any errors.

---

## 5. Issue 2: `RuntimeError: Could not extract attendance data... Current URL: ***Login/`

### Why Did This Occur?
* When navigating to `ERP_ATTENDANCE_URL`, the portal redirected back to `Login/`.
* On GitHub Actions (cloud runners outside India), network latency is higher. The script was waiting only a fixed 3 seconds before navigating, cutting off the login postback before session cookies were stored.
* Additionally, Headless Chromium on Linux can be challenged by ERP security if standard browser user agents and dialog handlers are missing.
* Finally, if `ERP_USERNAME` or `ERP_PASSWORD` in GitHub Secrets has a typo, leading/trailing spaces, or was recently changed, ERP rejects the login.

### What Was Done to Fix It:
1. **Dynamic Login Wait & Verification** in `erp_automation/erp_client.py`:
   - Waits up to 15s for the URL to change from the login page instead of a hardcoded 3s.
   - Trims whitespace from `ERP_USERNAME` and `ERP_PASSWORD`.
   - Adds desktop Windows Chrome User-Agent and automation avoidance flags.
   - Automatically accepts any session popup dialogs.
   - If ERP redirects back to login, extracts and prints the exact error message from the page.
2. **Artifact Screenshot Upload** in `.github/workflows/attendance-check.yml`:
   - If attendance extraction fails, GitHub Actions now saves `attendance_error.png` under workflow run artifacts so you can inspect the exact browser screen.

### Checklist for You and Your Friends:
1. In your GitHub repository, go to **Settings** -> **Secrets and variables** -> **Actions**.
2. Verify **`ERP_USERNAME`** and **`ERP_PASSWORD`**:
   - Ensure there are no accidental spaces before or after the username or password.
   - Verify roll number characters (e.g. check letter `O` vs digit `0`).
   - If college portal password was changed recently, update it in GitHub Secrets.

