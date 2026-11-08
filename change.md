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

## 5. Issue 2: `Authentication failed: URL did not change after login` (The Thai Spam & API Solution)

### Why Did This Occur?
1. **The Server-Side SEO Spam Infection**:
   - In the screenshot taken on GitHub Actions (`attendance_error.png`), the text above the login box showed:
     `U31 เว็บตรง สล็อตแตกง่าย 2026 ทางเข้า U31 VIP สมัครง่าย...`
   - The college server has an SEO spam/malware injection that targets foreign/cloud IP addresses (like GitHub Actions runners in Microsoft Azure US/Europe).
   - When accessed from foreign IPs, the server modifies the HTML page. This injection broke or intercepted the client-side JavaScript (`PageMethods.Login`), so clicking the login button never completed in the cloud!
   - On residential Indian IPs (your laptop), the server served clean HTML without the spam, which is why your laptop worked but GitHub Actions failed.

### The Permanent Fix: Direct WebMethod API Authentication
Instead of relying on the browser to interact with the defaced login webpage:
1. We authenticate **directly** via the backend ASP.NET WebMethod API endpoint:
   `POST https://erp.lbrce.ac.in/Default.aspx/Login`
   Payload: `{"UserID": username, "PWD": password}`
2. The server authenticates, returns `{"d":"2"}`, and immediately issues the valid session cookies (`ASP.NET_SessionId` and `ERP`).
3. The browser navigates directly to `https://erp.lbrce.ac.in/Discipline/StudentHistory.aspx` as an already authenticated user, completely bypassing the defaced login page!
4. If direct API login ever fails, it automatically falls back to UI-based login.

---

## 6. How Your Friends Can Apply All Fixes

If your friends need their bot to work on GitHub Actions:

### Step 1: Update `.github/workflows/attendance-check.yml`
1. Change runner OS:
   ```yaml
   runs-on: ubuntu-24.04
   ```
2. Add unbuffered output to `env:`:
   ```yaml
   PYTHONUNBUFFERED: "1"
   ```
3. Add debug screenshot upload on failure:
   ```yaml
   - name: Upload debug screenshot on failure
     if: failure()
     uses: actions/upload-artifact@v4
     with:
       name: attendance-debug-screenshot
       path: attendance_error.png
       if-no-files-found: ignore
   ```

### Step 2: Update `erp_automation/erp_client.py`
In `fetch_overall_attendance()`, authenticate via direct API before navigating:
```python
login_api_url = ERP_LOGIN_URL.rstrip("/") + "/Default.aspx/Login"
api_res = context.request.post(
    login_api_url,
    headers={
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest",
    },
    data={"UserID": username, "PWD": password},
    timeout=20000,
)
if api_res.status == 200 and ('"d":"1"' in api_res.text() or '"d":"2"' in api_res.text() or 'dbs' in api_res.text()):
    api_login_success = True
```

### Step 3: Verify GitHub Secrets
In GitHub -> **Settings** -> **Secrets and variables** -> **Actions**:
- Ensure `ERP_USERNAME` and `ERP_PASSWORD` match your credentials without spaces.

