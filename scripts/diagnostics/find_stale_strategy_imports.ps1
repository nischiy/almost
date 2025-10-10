param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host ">>> ProjectRoot = $ProjectRoot"

$patterns = @(
    'from\s+core\.strategy\s+import',
    'import\s+core\.strategy',
    'from\s+core\.logic\.logic\s+import',
    'import\s+core\.logic\.logic'
)

Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -Filter *.py -ErrorAction SilentlyContinue `
| Where-Object { $_.FullName -notmatch '\\__pycache__\\' } `
| ForEach-Object {
    $txt = Get-Content -LiteralPath $_.FullName -Raw
    foreach ($p in $patterns) {
        if ($txt -match $p) {
            Write-Host ("[HIT] " + $_.FullName)
            break
        }
    }
}
Write-Host "Done."
