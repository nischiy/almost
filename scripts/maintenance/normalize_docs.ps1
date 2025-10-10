param(
  [string]$ProjectRoot = ".",
  [string[]]$SourceRoots = @("app","core","scripts","tools","tests","README"),
  [switch]$IncludeReports = $false,
  [switch]$DryRun = $false,
  [switch]$VerboseLog = $true,
  [switch]$Rollback = $false,
  [string]$RollbackPlan = ""
)
# Windows PowerShell 5.1 compatible
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) { if ($VerboseLog) { Write-Host $msg } }
function Make-Dir([string]$p) { if (-not [string]::IsNullOrWhiteSpace($p)) { if (!(Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p | Out-Null } } }
function Hash-File([string]$p) { return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }

# 0) Resolve layout
$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
Push-Location -LiteralPath $ROOT
try {
  $DOCS = Join-Path $ROOT "docs"
  Make-Dir $DOCS
  $DOCS_IMPORTED = Join-Path $DOCS "imported"
  Make-Dir $DOCS_IMPORTED

  $LOGS = Join-Path $ROOT "logs"
  Make-Dir $LOGS
  $DOCS_MOVES = Join-Path $LOGS "docs_moves"
  Make-Dir $DOCS_MOVES

  if ($IncludeReports -and -not ($SourceRoots -contains "reports")) {
    $SourceRoots = $SourceRoots + @("reports")
  }

  # Keep only those roots that actually exist and are directories
  $ExistingRoots = @()
  foreach ($r in $SourceRoots) {
    $abs = Join-Path $ROOT $r
    if (Test-Path -LiteralPath $abs -PathType Container) { $ExistingRoots += $r } else { Write-Info ("[SKIP] Root not found: {0}" -f $r) }
  }
  if ($ExistingRoots.Count -eq 0) {
    throw "No valid roots found. Checked: $($SourceRoots -join ', ')"
  }

  $ts = (Get-Date).ToString("yyyy-MM-ddTHH-mm-ss")
  $planFile = Join-Path $DOCS_MOVES ("plan_{0}.json" -f $ts)

  if ($Rollback) {
    # --- ROLLBACK MODE ---
    if ([string]::IsNullOrWhiteSpace($RollbackPlan)) {
      # auto-pick latest plan
      $candidates = @(Get-ChildItem -LiteralPath $DOCS_MOVES -Filter "plan_*.json" | Sort-Object LastWriteTime -Descending)
      if ($candidates.Count -eq 0) { throw "No rollback plans found under logs/docs_moves." }
      $RollbackPlan = $candidates[0].FullName
    }
    Write-Host ("[ROLLBACK] Using plan: {0}" -f $RollbackPlan)

    $moves = Get-Content -LiteralPath $RollbackPlan -Raw | ConvertFrom-Json
    $count = 0
    foreach ($m in $moves) {
      $src = [string]$m.From
      $dst = [string]$m.To
      if ((Test-Path -LiteralPath $dst) -and -not (Test-Path -LiteralPath $src)) {
        if (-not $DryRun) {
          $srcDir = [System.IO.Path]::GetDirectoryName($src)
          Make-Dir $srcDir
          Move-Item -LiteralPath $dst -Destination $src -Force
        }
        Write-Host ("[OK] {0} <- {1}" -f $src, $dst)
        $count++
      } else {
        Write-Info ("[SKIP] Cannot rollback (exists-src or missing-dst): {0} <- {1}" -f $src, $dst)
      }
    }
    Write-Host ("[SUMMARY] Rolled back {0} file(s). DryRun={1}" -f $count, $DryRun)
    return
  }

  # --- BUILD MOVE PLAN ---
  $plan = New-Object System.Collections.Generic.List[object]

  foreach ($rootName in $ExistingRoots) {
    $absRoot = Join-Path $ROOT $rootName
    Write-Info ("[SCAN] {0}" -f $absRoot)

    # IMPORTANT: WinPS 5.1 quirk: -Include requires wildcard or -Path with wildcard; use -Filter reliably.
    $files = Get-ChildItem -LiteralPath $absRoot -File -Recurse -Filter "*.md" | Where-Object {
      # Exclude docs/ subtree and common noise; double-check extension in case of edge cases
      $fp = $_.FullName
      ($_.Extension -ieq ".md") -and
      ($fp -notlike "*\docs\*") -and
      ($fp -notlike "*\.venv\*") -and
      ($fp -notlike "*\.git\*") -and
      ($fp -notlike "*\__pycache__\*")
    }

    foreach ($f in $files) {
      # Compute repo-relative path
      $fullResolved = (Resolve-Path -LiteralPath $f.FullName).Path
      $rel = $fullResolved.Substring($ROOT.Length).TrimStart("\/")

      # Destination under docs/imported/<rel>
      $dst = Join-Path $DOCS_IMPORTED $rel
      $srcPosix = ($f.FullName -replace "\\","/")
      $relPosix = ($rel -replace "\\","/")

      # Collision handling
      $realDst = $dst
      $n = 0
      while (Test-Path -LiteralPath $realDst) {
        $srcHash = Hash-File $f.FullName
        $dstHash = Hash-File $realDst
        if ($srcHash -eq $dstHash) { break }
        $base = [System.IO.Path]::GetFileNameWithoutExtension($dst)
        $ext  = [System.IO.Path]::GetExtension($dst)
        $dir  = [System.IO.Path]::GetDirectoryName($dst)
        $n += 1
        $realDst = Join-Path $dir ("{0}.dup{1}{2}" -f $base, $n, $ext)
      }

      $plan.Add([pscustomobject]@{
        From = $srcPosix
        To   = ($realDst -replace "\\","/")
        Rel  = $relPosix
        Group = $rootName
      })
    }
  }

  Write-Host ("[PLAN] {0} file(s) will be moved into docs/imported" -f $plan.Count)
  foreach ($m in $plan) {
    Write-Host ("[DRY] {0} -> {1}" -f $m.From, $m.To)
  }

  if (-not $DryRun) {
    # Persist plan for rollback (WinPS 5.1: use -Encoding utf8)
    ($plan | ConvertTo-Json -Depth 4) | Out-File -LiteralPath $planFile -Encoding utf8

    # Execute
    $moved = 0
    foreach ($m in $plan) {
      $src = $m.From
      $dst = $m.To
      $dstDir = [System.IO.Path]::GetDirectoryName($dst)
      Make-Dir $dstDir

      if (Test-Path -LiteralPath $dst) {
        # If same content -> remove source; else overwrite to the resolved unique path (already handled)
        $srcHash = Hash-File $src
        $dstHash = Hash-File $dst
        if ($srcHash -eq $dstHash) {
          Remove-Item -LiteralPath $src -Force
          Write-Host ("[OK] Removed duplicate {0} (already in docs)" -f $src)
        } else {
          Move-Item -LiteralPath $src -Destination $dst -Force
          Write-Host ("[OK] {0} -> {1}" -f $src, $dst)
          $moved++
        }
      } else {
        Move-Item -LiteralPath $src -Destination $dst -Force
        Write-Host ("[OK] {0} -> {1}" -f $src, $dst)
        $moved++
      }
    }
    Write-Host ("[DONE] Moved {0} file(s)." -f $moved)
  }

  # --- Generate docs/INDEX.md ---
  $idxLines = New-Object System.Collections.Generic.List[string]
  $idxLines.Add("# Documentation Index (generated)")
  $idxLines.Add("")
  $idxLines.Add( ("Generated: {0}" -f (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")) )
  $idxLines.Add( ("Roots: {0}" -f ($ExistingRoots -join ", ")) )
  $idxLines.Add("")

  # Group by source root
  $groups = $plan | Group-Object Group | Sort-Object Name
  foreach ($g in $groups) {
    $idxLines.Add("## " + $g.Name)
    foreach ($m in ($g.Group | Sort-Object Rel)) {
      # link target must be relative from docs/
      $relFromDocs = ("imported/" + $m.Rel) -replace "\\","/"
      $idxLines.Add( ("- [{0}]({1})" -f $m.Rel, $relFromDocs) )
    }
    $idxLines.Add("")
  }

  $INDEX = Join-Path $DOCS "INDEX.md"
  if (-not $DryRun) {
    ($idxLines -join [Environment]::NewLine) | Out-File -LiteralPath $INDEX -Encoding utf8
    Write-Host "[DONE] docs/INDEX.md generated."
  } else {
    Write-Host "[DRY] docs/INDEX.md would be generated."
  }

  Write-Host ("[SUMMARY] Planned={0} DryRun={1} PlanFile={2}" -f $plan.Count, $DryRun, (Split-Path -Leaf $planFile))
}
finally {
  Pop-Location
}
