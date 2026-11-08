# GitHub Actions Workflow Fix Guide

See [change.md](change.md) for the full guide.

## Summary of the Fix

### File:
`.github/workflows/attendance-check.yml` (around Line 14)

### Change:
```yaml
# Before:
runs-on: ubuntu-latest

# After:
runs-on: ubuntu-24.04
```

### Why:
GitHub updated `ubuntu-latest` to an environment (`ubuntu26.04-x64`) that Playwright does not yet support. Pinning to `ubuntu-24.04` resolves the issue immediately.
