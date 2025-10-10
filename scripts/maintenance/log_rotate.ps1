param(
    [int]$Days = 7
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\.."
$logRoot = Join-Path $repo "logs"
$archive = Join-Path $logRoot "archive"
New-Item -ItemType Directory -Force -Path $archive | Out-Null

$cutoff = (Get-Date).AddDays(-$Days)
$files = Get-ChildItem -Path $logRoot -Recurse -File | Where-Object { $_.LastWriteTime -lt $cutoff }
if ($files.Count -eq 0) { Write-Host "Nothing to archive (older than $Days days)." ; exit 0 }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipPath = Join-Path $archive ("logs_{0}_older_than_{1}d.zip" -f $stamp, $Days)
Compress-Archive -Path $files.FullName -DestinationPath $zipPath -Force
# Remove original files after compression
$files | Remove-Item -Force
Write-Host "Archived $($files.Count) files -> $zipPath" -ForegroundColor Green
