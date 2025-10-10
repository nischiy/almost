Write-Host "=== All Checks (preflight + tests + offline backtest) ==="
.\scripts\preflight.ps1 -Strict
if ($LASTEXITCODE -ne 0) { exit 1 }

pytest -q -vv
if ($LASTEXITCODE -ne 0) { exit 1 }

python tools\smoke_pipeline.py
exit $LASTEXITCODE
