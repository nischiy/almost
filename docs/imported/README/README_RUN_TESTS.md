# Running the full test suite

From the project root in PowerShell:

```powershell
# 1) Activate your venv if not already
# .\.venv\Scripts\Activate.ps1

# 2) Run all tests (auto-installs pytest if missing)
powershell -ExecutionPolicy Bypass -File .\scripts\run_all_tests.ps1
```

Reports are written to:
- `logs/reports/pytest_YYYYMMDD_HHMMSS.txt`
- `logs/reports/pytest_YYYYMMDD_HHMMSS.junit.xml`

If everything is green you'll see: **ALL TESTS PASSED ✅**
