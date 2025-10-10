param(
  [ValidateSet("modern","legacy")]
  [string]$Policy = "modern",
  [string]$ProjectRoot = ".",
  [switch]$VerboseLog = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Log([string]$m) { if ($VerboseLog) { Write-Host $m } }

function Ensure-Directory([string]$p) {
  $full = Join-Path $ProjectRoot $p
  $dir = Split-Path -LiteralPath $full -Parent
  if (!(Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  return $full
}

function Upsert-Requirement([string]$reqPath, [string]$spec) {
  if (!(Test-Path -LiteralPath $reqPath)) {
    Log "[REQ] requirements.txt not found, creating new"
    $spec | Out-File -LiteralPath $reqPath -Encoding utf8
    return
  }
  $lines = Get-Content -LiteralPath $reqPath -Encoding utf8
  $match = $lines | Select-String -Pattern '^\s*websockets(\[.*\])?\s*([<>=!~]=?.*)?$' -SimpleMatch:$false | Select-Object -First 1
  if ($match) {
    $idx = [int]$match.LineNumber - 1
    $lines[$idx] = $spec
    Log "[REQ] replaced websockets spec at line $($match.LineNumber) -> $spec"
  } else {
    $lines += $spec
    Log "[REQ] appended websockets spec -> $spec"
  }
  $lines | Set-Content -LiteralPath $reqPath -Encoding utf8
}

function Append-Link-To-DocsIndex([string]$indexPath, [string]$relLink) {
  $bullet = "* [$relLink]($relLink)"
  if (!(Test-Path -LiteralPath $indexPath)) {
    Log "[DOC] docs/INDEX.md not found, creating"
    "# Документація`n`n$bullet" | Out-File -LiteralPath $indexPath -Encoding utf8
    return
  }
  $txt = Get-Content -LiteralPath $indexPath -Raw -Encoding utf8
  if ($txt -notmatch [regex]::Escape($relLink)) {
    Log "[DOC] adding link to docs/INDEX.md -> $relLink"
    "$txt`n$bullet`n" | Out-File -LiteralPath $indexPath -Encoding utf8
  } else {
    Log "[DOC] docs/INDEX.md already contains link to $relLink"
  }
}

# Paths
$req = Join-Path $ProjectRoot "requirements.txt"
$constraints = Join-Path $ProjectRoot "constraints.txt"
$sitecustomize = Join-Path $ProjectRoot "sitecustomize.py"
$upgradeDoc = Ensure-Directory "docs/WEBSOCKETS_UPGRADE.md"
$indexDoc = Ensure-Directory "docs/INDEX.md"

switch ($Policy) {
  "modern" {
    $spec = "websockets>=14,<16"
    Upsert-Requirement -reqPath $req -spec $spec

    if (Test-Path -LiteralPath $constraints) {
      $lines = Get-Content -LiteralPath $constraints -Encoding utf8
      $new = $lines | Where-Object { $_ -notmatch '^\s*websockets\s*<\s*14' }
      if ($new.Count -ne $lines.Count) {
        Log "[CONSTRAINTS] removed legacy websockets<14 pin from constraints.txt"
        $new | Set-Content -LiteralPath $constraints -Encoding utf8
      }
    }

    if (Test-Path -LiteralPath $sitecustomize) {
      Remove-Item -LiteralPath $sitecustomize -Force
      Log "[CLEAN] removed sitecustomize.py (no longer needed)"
    }

    @"
# WebSockets (`websockets`) – політика залежності

**Поточна політика:** `websockets>=14,<16` (гілка 14/15).

Проєкт не використовує застарілі імпорти `websockets.client/server/legacy`, отже додаткові шими не потрібні.
Якщо сторонні залежності підтягують старе API, використовуйте офіційні шляхи `websockets.asyncio.client/server`
або звертайтесь до документації бібліотеки.

## Інсталяція
```powershell
pip install "websockets>=14,<16"
```

## Примітка
За потреби тимчасового даунгрейду використовуйте режим *legacy* через `constraints.txt`.
"@ | Out-File -LiteralPath $upgradeDoc -Encoding utf8

    Append-Link-To-DocsIndex -indexPath $indexDoc -relLink "WEBSOCKETS_UPGRADE.md"

    Log "[DONE] policy 'modern' applied"
  }
  "legacy" {
    "websockets<14" | Out-File -LiteralPath $constraints -Encoding utf8
    Log "[CONSTRAINTS] wrote constraints.txt with websockets<14"
    Append-Link-To-DocsIndex -indexPath $indexDoc -relLink "WEBSOCKETS_UPGRADE.md"
    Log "[DONE] policy 'legacy' applied (remember to install with -c constraints.txt)"
  }
}
