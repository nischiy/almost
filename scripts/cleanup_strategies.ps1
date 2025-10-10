param(
    [string]$ProjectRoot = ".",
    [string]$Keep = "ema_rsi_atr.py",
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectPath([string]$root) {
    return (Resolve-Path -LiteralPath $root).Path
}

function New-BackupZip([string]$root, [System.Collections.ArrayList]$filesToBackup) {
    if ($filesToBackup.Count -eq 0) { return $null }
    $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $zipPath = Join-Path $root "_backup_strategies_$stamp.zip"
    if ($WhatIf) { Write-Host "[WhatIf] Would create backup: $zipPath with $($filesToBackup.Count) files"; return $zipPath }

    Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
    $zip = [System.IO.Compression.ZipFile]::Open($zipPath, 'Create')
    try {
        foreach ($f in $filesToBackup) {
            $abs = (Resolve-Path -LiteralPath $f -ErrorAction SilentlyContinue)
            if (-not $abs) { continue }
            $abs = $abs.Path
            $rel = $abs.Substring($root.Length).TrimStart('\','/')
            if (-not $rel) { $rel = [System.IO.Path]::GetFileName($abs) }
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $abs, $rel) | Out-Null
        }
    } finally { $zip.Dispose() }
    Write-Host "[OK] Backup created: $zipPath"
    return $zipPath
}

function Get-StrategyFilesFrom([string]$dir) {
    if (-not (Test-Path $dir)) { return @() }
    $files = Get-ChildItem -LiteralPath $dir -Recurse -File -Filter *.py -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and $_.Name.ToLower() -ne '__init__.py' } |
        Select-Object -ExpandProperty FullName
    return @($files)
}

function Get-CandidateStrategyFiles([string]$root) {
    $paths = @()
    $paths += Get-StrategyFilesFrom (Join-Path $root 'core\logic')
    $paths += Get-StrategyFilesFrom (Join-Path $root 'core\strategies')
    $paths += Get-StrategyFilesFrom (Join-Path $root 'strategies')
    $paths += Get-StrategyFilesFrom (Join-Path $root 'app\logic')
    $paths += Get-StrategyFilesFrom (Join-Path $root 'app\strategies')

    $coreStrategy = Join-Path $root 'core\strategy.py'
    if (Test-Path $coreStrategy) { $paths += (Resolve-Path -LiteralPath $coreStrategy).Path }

    $paths = @($paths | Select-Object -Unique)
    return $paths
}

function Ensure-CoreLogic([string]$root) {
    $logicDir = Join-Path $root "core\logic"
    if (-not (Test-Path $logicDir)) {
        if ($WhatIf) { Write-Host "[WhatIf] Would create dir: $logicDir" }
        else { New-Item -ItemType Directory -Force -Path $logicDir | Out-Null; Write-Host "[OK] Created: $logicDir" }
    }
    return $logicDir
}

function Resolve-KeepTarget([string]$root, [string]$keep) {
    $logicDir = Join-Path $root "core\logic"
    $candidates = @()
    if ($keep -match "[\\/]" ) {
        $full = Join-Path $root $keep
        if (Test-Path $full) { $candidates += (Resolve-Path -LiteralPath $full).Path }
    } else {
        $cand = Get-CandidateStrategyFiles $root | Where-Object { ([System.IO.Path]::GetFileName($_)).ToLower() -eq $keep.ToLower() }
        $candidates += $cand
        $inLogic = Join-Path $logicDir $keep
        if (Test-Path $inLogic) { $candidates += (Resolve-Path -LiteralPath $inLogic).Path }
    }
    $candidates = @($candidates | Select-Object -Unique)
    if ($candidates.Count -eq 0) { throw "Keep target '$keep' not found. Run list_strategies.ps1 to see options." }
    if ($candidates.Count -gt 1) {
        Write-Warning "Multiple matches for Keep '$keep':"
        $candidates | ForEach-Object { Write-Host " - $_" }
        Write-Host "The first one will be used."
    }
    return $candidates[0]
}

function Move-KeepToLogic([string]$root, [string]$keepFullPath) {
    $logicDir = Ensure-CoreLogic $root
    $dest = Join-Path $logicDir ([System.IO.Path]::GetFileName($keepFullPath))
    $keepAbs = (Resolve-Path -LiteralPath $keepFullPath).Path
    $destAbsPath = (Resolve-Path -LiteralPath $dest -ErrorAction SilentlyContinue)
    if ($destAbsPath -and ($keepAbs -ieq $destAbsPath.Path)) { Write-Host "[OK] Keep file already in core\logic: $dest"; return $dest }
    if ($WhatIf) { Write-Host "[WhatIf] Would copy: $keepAbs -> $dest" }
    else { Copy-Item -LiteralPath $keepAbs -Destination $dest -Force; Write-Host "[OK] Copied keep file to core\logic: $dest" }
    return $dest
}

function Remove-OtherStrategies([string]$root, [string]$keepDestFull) {
    $keepAbs = (Resolve-Path -LiteralPath $keepDestFull).Path
    $toDelete = New-Object System.Collections.ArrayList

    foreach ($f in (Get-CandidateStrategyFiles $root)) {
        $absPathObj = (Resolve-Path -LiteralPath $f -ErrorAction SilentlyContinue)
        if (-not $absPathObj) { continue }
        $abs = $absPathObj.Path
        if ($abs -ieq $keepAbs) { continue }
        if ([System.IO.Path]::GetFileName($abs).ToLower() -eq "__init__.py") { continue }
        [void]$toDelete.Add($abs)
    }

    # Also remove any other .py in core\logic except __init__.py and keep file
    $logicDir = Join-Path $root "core\logic"
    if (Test-Path $logicDir) {
        Get-ChildItem -LiteralPath $logicDir -File -Filter *.py -ErrorAction SilentlyContinue `
            | Where-Object { $_.FullName -ine $keepAbs -and $_.Name.ToLower() -ne "__init__.py" } `
            | ForEach-Object { [void]$toDelete.Add($_.FullName) }
    }

    # De-duplicate
    $toDelete = @($toDelete | Select-Object -Unique)

    if ($toDelete.Count -eq 0) { Write-Host "[OK] Nothing to delete."; return }

    $backup = New-BackupZip $root $toDelete

    foreach ($f in $toDelete) {
        if ($WhatIf) {
            Write-Host "[WhatIf] Would delete: $f"
        } else {
            try {
                Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue
                Write-Host "[DEL] $f"
            } catch {
                Write-Warning "Skip (not found): $f"
            }
        }
    }

    # Clean empty strategy folders (but never remove core\logic itself)
    $candDirs = @("core\strategies","strategies","app\logic","app\strategies")
    foreach ($d in $candDirs) {
        $full = Join-Path $root $d
        if (Test-Path $full) {
            $hasPy = (Get-ChildItem -LiteralPath $full -Recurse -File -Include *.py -ErrorAction SilentlyContinue | Measure-Object).Count
            if ($hasPy -eq 0) {
                if ($WhatIf) { Write-Host "[WhatIf] Would remove empty dir: $full" }
                else { try { Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction SilentlyContinue } catch {}; Write-Host "[CLEAN] Removed empty dir: $full" }
            }
        }
    }

    # Show final state of core\logic
    Write-Host "`n[core\\logic] current files:"
    Get-ChildItem -LiteralPath $logicDir -File -Filter *.py -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host (" - " + $_.Name)
    }
}

# --- Main ---
$ProjectRoot = Resolve-ProjectPath $ProjectRoot
Write-Host ">>> ProjectRoot = $ProjectRoot"
Write-Host ">>> Keep = $Keep"
if ($WhatIf) { Write-Host ">>> WhatIf mode: preview only" }

$keepFull = Resolve-KeepTarget $ProjectRoot $Keep
$dest = Move-KeepToLogic $ProjectRoot $keepFull
Remove-OtherStrategies $ProjectRoot $dest

Write-Host "[DONE] Strategy cleanup complete. Only keep file should remain in core\logic."
