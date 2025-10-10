param(
  [string]$ProjectRoot = "."
)
$ErrorActionPreference = "Stop"

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$healthRoot = Join-Path -Path $root -ChildPath "logs\health"
$guardDir   = Join-Path -Path $healthRoot -ChildPath "guard"
$dailyDir   = Join-Path -Path $healthRoot -ChildPath "daily"

if (-not (Test-Path -LiteralPath $healthRoot)) {
  Write-Host "Nothing to migrate: $healthRoot not found."
  exit 0
}
New-Item -ItemType Directory -Path $guardDir -Force | Out-Null
New-Item -ItemType Directory -Path $dailyDir -Force | Out-Null

# Move files in logs\health root into guard
Get-ChildItem -LiteralPath $healthRoot -File -ErrorAction SilentlyContinue | ForEach-Object {
  $dst = Join-Path -Path $guardDir -ChildPath $_.Name
  try {
    Move-Item -LiteralPath $_.FullName -Destination $dst -Force
    Write-Host ("Moved file -> {0}" -f $dst)
  } catch {
    Write-Warning ("Skip file {0}: {1}" -f $_.FullName, $_.Exception.Message)
  }
}

# Move YYYY-MM-DD folders under daily/
$regex = '^\d{4}-\d{2}-\d{2}$'
Get-ChildItem -LiteralPath $healthRoot -Directory -ErrorAction SilentlyContinue | Where-Object {
  $_.Name -match $regex -and $_.Name -ne "guard" -and $_.Name -ne "daily"
} | ForEach-Object {
  $dst = Join-Path -Path $dailyDir -ChildPath $_.Name
  try {
    if (Test-Path -LiteralPath $dst) {
      # merge contents, then remove source
      Get-ChildItem -LiteralPath $_.FullName -Recurse | ForEach-Object {
        $rel = $_.FullName.Substring( ($_.FullName.IndexOf($_.Name)) + $_.Name.Length ).TrimStart('\')
        $target = Join-Path -Path $dst -ChildPath $rel
        if ($_.PSIsContainer) { New-Item -ItemType Directory -Path $target -Force | Out-Null }
        else {
          New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
          Move-Item -LiteralPath $_.FullName -Destination $target -Force
        }
      }
      Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    } else {
      Move-Item -LiteralPath $_.FullName -Destination $dst -Force
    }
    Write-Host ("Moved day folder -> {0}" -f $dst)
  } catch {
    Write-Warning ("Skip dir {0}: {1}" -f $_.FullName, $_.Exception.Message)
  }
}

Write-Host ("Migration complete. New layout under {0}" -f ${healthRoot})
Get-ChildItem -LiteralPath $healthRoot -Force | Format-List Name, FullName
