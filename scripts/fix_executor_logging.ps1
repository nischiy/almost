
param(
  [string]$PathGuess = ".\core\executor_service.py"
)

$ErrorActionPreference = "Stop"

function Inject-Logging {
  param([string]$File)
  Write-Host "Patching $File ..." -ForegroundColor Cyan
  $code = Get-Content -LiteralPath $File -Raw

  if ($code -notmatch 'class\s+ExecutorService\b') {
    Write-Warning "ExecutorService class not found in $File. Skipping."
    return
  }

  # Ensure imports once
  if ($code -notmatch 'from\s+datetime\s+import\s+datetime') {
    $code = "from datetime import datetime`n" + $code
  }
  if ($code -notmatch 'from\s+pathlib\s+import\s+Path') {
    $code = "from pathlib import Path`n" + $code
  }

  $logBlock = @'
        # paper-mode CSV logging (idempotent)
        try:
            import os
            paper = str(os.environ.get("PAPER_TRADING","1")).lower() in {"1","true","yes","on"}
            trade_enabled = str(os.environ.get("TRADE_ENABLED","0")).lower() in {"1","true","yes","on"}
            if paper and not trade_enabled:
                d = Path("logs") / "orders" / datetime.utcnow().strftime("%Y-%m-%d")
                d.mkdir(parents=True, exist_ok=True)
                f = d / "orders.csv"
                hdr = "ts,symbol,side,price,sl,tp"
                line = f"{datetime.utcnow().isoformat()},{getattr(self,'symbol','?')},{decision.get('side')},{decision.get('price')},{decision.get('sl')},{decision.get('tp')}"
                if not f.exists():
                    f.write_text(hdr + "\n", encoding="utf-8")
                with f.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
        except Exception as _e:
            pass
'@

  # Inject into place() body after signature line
  $pattern = [regex]::Escape("def place(")
  if ($code -match "def\s+place\([^\)]*\):") {
    if ($code -notmatch "paper-mode CSV logging") {
      $code = $code -replace "(def\s+place\([^\)]*\):\s*\r?\n)", "`$1" + $logBlock.Replace("`r`n","`n")
      Write-Host "Injected logging into place()" -ForegroundColor Green
    } else {
      Write-Host "Logging already present; nothing to do." -ForegroundColor Gray
    }
  } else {
    Write-Warning "place() method not found; skipping."
  }

  Set-Content -LiteralPath $File -Value $code -Encoding UTF8
}

# Try default guess; if not exists, search whole repo
if (Test-Path -LiteralPath $PathGuess) {
  Inject-Logging -File $PathGuess
} else {
  $candidates = Get-ChildItem -LiteralPath . -Recurse -Filter "executor_service.py" | Select-Object -ExpandProperty FullName
  if (-not $candidates) {
    Write-Warning "executor_service.py not found anywhere; skipping."
    exit 0
  }
  foreach ($f in $candidates) { Inject-Logging -File $f }
}
