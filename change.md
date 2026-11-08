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

## 5. Issue 2: `RuntimeError: Authentication failed: ERP redirected back to login (***Login/)`

### Why Did This Occur?
1. **Wrong Element Clicked**: The ERP portal has an `<h4>` heading: `<h4 class="form-title">LOGIN|LBRCE-ERP</h4>`. The selector `text=Login` was clicking this heading instead of the `<button class="btn blue">` submit button!
2. **AJAX Call Not Waited For**: The ERP login runs an asynchronous AJAX function (`PageMethods.Login`). On success, it redirects to `/Fee/FeeChallanOnline.aspx` or `/Home/`.
3. **Flawed Wait Condition**: The previous code checked `if "login" not in page.url.lower(): break`. Because the initial login page `https://erp.lbrce.ac.in/` does not have `"login"` in the URL, the loop broke in 0 seconds! The script then navigated to the attendance URL immediately, cancelling the in-flight AJAX login request before cookies were saved.

### What Was Done to Fix It:
1. **Target the Exact Button** in `erp_automation/erp_client.py`:
   - Updated button selector to `button.btn.blue, button:has-text('Login'), button[onclick*='login']`.
2. **Proper Session Wait**:
   - Stores `initial_url = page.url` and waits up to 25 seconds for `page.url != initial_url`.
   - Once redirected to `/Fee/...` or `/Home/`, the session is verified and active.
3. **Desktop User-Agent & Anti-Bot Flags**:
   - Added desktop Chrome user-agent and flags (`--disable-blink-features=AutomationControlled`).
4. **Artifact Screenshot Upload** in `.github/workflows/attendance-check.yml`:
   - Saves and uploads `attendance_error.png` directly to GitHub Actions if an error occurs.

---

## 6. How Your Friends Can Apply All Fixes

If your friends need their bot to work on GitHub Actions:

### Step 1: Update `.github/workflows/attendance-check.yml`
Change:
```yaml
runs-on: ubuntu-latest
```
To:
```yaml
runs-on: ubuntu-24.04
```

### Step 2: Update `erp_automation/erp_client.py`
In `fetch_overall_attendance()`, ensure:
- The login button selector uses:
  ```python
  clicked = _click_first(
      page,
      [
          "button.btn.blue",
          "button:has-text('Login')",
          "button[onclick*='login']",
          "input[type='submit']",
      ],
  )
  ```
- And wait for URL to change from `initial_url`:
  ```python
  start_login = time.time()
  login_success = False
  while time.time() - start_login < 25:
      if page.url != initial_url:
          login_success = True
          break
      page.wait_for_timeout(500)
  ```

### Step 3: Verify GitHub Secrets
In GitHub -> **Settings** -> **Secrets and variables** -> **Actions**:
- Ensure `ERP_USERNAME` and `ERP_PASSWORD` have no extra spaces or typos.

