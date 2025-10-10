$ErrorActionPreference = "Stop"
.\scripts\preflight.ps1 -Strict
pytest -q -vv
$p = (.\scripts\live\ping_exchange.ps1 | Out-String)
if ($p -notmatch '"status_code":\s*200') { throw "Ping failed" }
$t = (.\scripts\live\read_ticker.ps1 | Out-String)
if ($t -notmatch '"ok":\s*true') { throw "Ticker failed" }
Write-Host "GO"
