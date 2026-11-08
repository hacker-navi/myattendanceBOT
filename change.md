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
