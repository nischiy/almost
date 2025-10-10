# make_clean_archive.ps1
param(
  [string]$Root = (Split-Path -Parent $MyInvocation.MyCommand.Path),
  [string]$OutZip = "$(Split-Path $Root -Parent)\withouttrah_project_clean.zip"
)

# Ensure cleaned temp copy
$Temp = Join-Path $env:TEMP "withouttrah_clean_$(Get-Date -Format yyyyMMdd_HHmmss)"
if (Test-Path $Temp) { Remove-Item -Recurse -Force $Temp }
robocopy $Root $Temp /MIR /XD ".venv" ".idea" ".git" "__pycache__" ".pytest_tmp" "logs" > $null

# extra clean
powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\clean_safely.ps1") -Root $Temp | Out-Null

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Add-Type -AssemblyName 'System.IO.Compression.FileSystem'
[System.IO.Compression.ZipFile]::CreateFromDirectory($Temp, $OutZip)
Write-Host ">>> Wrote $OutZip"
