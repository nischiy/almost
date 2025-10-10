# Env Loader Pack v1
Purpose: make PowerShell see your `.env` values as $env:* variables.

Usage:
```powershell
# 1) load .env into current session
powershell -ExecutionPolicy Bypass -File .\scripts\tools\load_env.ps1 .\.env

# 2) verify
if ([string]::IsNullOrEmpty($env:API_KEY)) { "API_KEY missing" } else { "API_KEY set ✅" }
if ([string]::IsNullOrEmpty($env:API_SECRET)) { "API_SECRET missing" } else { "API_SECRET set ✅" }

# 3) run live
$env:DRY_RUN_ONLY="0"
powershell -ExecutionPolicy Bypass -File .\scripts\tools\go_live.ps1 BUY MARKET -SL 110000 -TP 120000
```
Notes:
- The loader ignores comments and blank lines.
- Quotes around values in `.env` are stripped automatically.
- It only sets variables for the **current** PowerShell session.
