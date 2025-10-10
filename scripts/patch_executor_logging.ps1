<#
      patches ExecutorService.place() to write logs/orders/YYYY-MM-DD/orders.csv in PAPER mode
      - searches repo for *.py with 'class ExecutorService' and 'def place('
      - injects idempotent block marked '# __PAPER_LOGGING__'
      Usage:
        .\scripts\patch_executor_logging.ps1
    #>
    Set-StrictMode -Version Latest
    $ErrorActionPreference = "Stop"

    $RepoRoot = Split-Path $PSScriptRoot -Parent
    Set-Location $RepoRoot

    $marker = "# __PAPER_LOGGING__"
    $logBlock = @'
            # __PAPER_LOGGING__
            try:
                import os as _EP_os
                from pathlib import Path as _EP_Path
                from datetime import datetime as _EP_dt, timezone as _EP_tz
                paper = str(_EP_os.environ.get("PAPER_TRADING","1")).strip().lower() in {"1","true","yes","on"}
                trade_enabled = str(_EP_os.environ.get("TRADE_ENABLED","0")).strip().lower() in {"1","true","yes","on"}
                if paper and not trade_enabled:
                    d = _EP_Path("logs") / "orders" / _EP_dt.now(_EP_tz.utc).strftime("%Y-%m-%d")
                    d.mkdir(parents=True, exist_ok=True)
                    f = d / "orders.csv"
                    hdr = "ts,symbol,side,price,sl,tp"
                    side = (decision or {}).get("side") if isinstance(decision, dict) else None
                    price = (decision or {}).get("price") if isinstance(decision, dict) else None
                    sl = (decision or {}).get("sl") if isinstance(decision, dict) else None
                    tp = (decision or {}).get("tp") if isinstance(decision, dict) else None
                    line = f"{_EP_dt.now(_EP_tz.utc).isoformat()},{getattr(self,'symbol','?')},{side},{price},{sl},{tp}"
                    if not f.exists():
                        f.write_text(hdr + "\n", encoding="utf-8")
                    with f.open("a", encoding="utf-8") as fh:
                        fh.write(line + "\n")
            except Exception:
                pass

'@

    $patched = 0
    $cands = Get-ChildItem -LiteralPath $RepoRoot -Recurse -Filter *.py |
      Where-Object { $_.FullName -notmatch '\\.venv\\|site-packages' }

    foreach ($f in $cands) {
      try {
        $txt = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
      } catch { continue }

      if ($txt -notmatch 'class\s+ExecutorService\b' -or $txt -notmatch 'def\s+place\(') { continue }
      if ($txt -match [regex]::Escape($marker)) { continue }

      # Find the 'def place(' line and its indentation
      $lines = $txt -split "`r?`n"
      $idx = -1
      for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match '^\s*def\s+place\(') { $idx = $i; break }
      }
      if ($idx -lt 0) { continue }

      # Determine indentation for the function body
      $indent = ""
      for ($j = $idx+1; $j -lt $lines.Length; $j++) {
        if ($lines[$j].Trim().Length -eq 0) { continue }
        $m = [regex]::Match($lines[$j], '^\s+')
        if ($m.Success) { $indent = $m.Value } else { $indent = "    " }
        break
      }
      if (-not $indent) { $indent = "    " }

      # Build injected text with proper indent
      $blockIndented = ($logBlock -split "`r?`n" | ForEach-Object { $indent + $_ }) -join "`r`n"
      # Insert right after signature line
      $newLines = @()
      for ($k = 0; $k -lt $lines.Length; $k++) {
        $newLines += $lines[$k]
        if ($k -eq $idx) {
          $newLines += $blockIndented
        }
      }
      $newTxt = ($newLines -join "`r`n")

      try {
        Set-Content -LiteralPath $f.FullName -Value $newTxt -Encoding UTF8
        Write-Host "Patched: $($f.FullName)" -ForegroundColor Green
        $patched++
      } catch {
        Write-Warning "Failed to patch $($f.FullName): $_"
      }
    }

    if ($patched -eq 0) {
      Write-Host "No files patched (ExecutorService.place() not found or already patched)." -ForegroundColor Yellow
    } else {
      Write-Host "Done. Patched files: $patched" -ForegroundColor Cyan
    }
