# Live Bridge Fix Pack v1
Fixes HTTP 400 on live order by:
- Setting leverage via `/fapi/v1/leverage` **before** sending the order
- Removing unsupported `leverage` field from `/fapi/v1/order` payload
- Writing full error body on failures

Usage (LIVE):
```powershell
# Ensure keys loaded into current session, DRY_RUN_ONLY=0
& .\scripts\tools\load_env.ps1 .\.env
$env:DRY_RUN_ONLY="0"

# One-shot live with optional SL/TP
& .\scripts\tools\go_live.ps1 BUY MARKET -SL 110000 -TP 120000
# or: & .\scripts\tools\go_live.ps1 BUY LIMIT 120000 -SL 110000 -TP 120000
```
Logs: `logs\orders\YYYYMMDD\preview_*.json` and `sent_*.json` (contains leverage + order responses).
