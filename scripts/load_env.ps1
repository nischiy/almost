param(
  [string]$Path = ".env"
)

if (-not (Test-Path $Path)) {
  Write-Host "No .env found at $Path" -ForegroundColor Yellow
  exit 1
}

Get-Content $Path | ForEach-Object {
  $line = $_.Trim()
  if ($line -match '^\s*#') { return }
  if ($line -eq "") { return }
  $kv = $line -split '=', 2
  if ($kv.Length -eq 2) {
    $name = $kv[0].Trim()
    $value = $kv[1].Trim()
    [Environment]::SetEnvironmentVariable($name, $value, "Process")
  }
}

Write-Host "[env] loaded from $Path"
