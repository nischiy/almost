# scripts/tools/load_env.ps1  (v2 — strips BOM/zero-width, masks secrets)
param([Parameter(Mandatory=$true)][string]$Path)

if (-not (Test-Path $Path)) { throw "File not found: $Path" }

# Read as bytes to strip UTF-8 BOM if present
[byte[]]$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $Path))
# UTF-8 BOM: EF BB BF
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
  $bytes = $bytes[3..($bytes.Length-1)]
}
$content = [System.Text.Encoding]::UTF8.GetString($bytes)

# Normalize newlines
$content -split "(`r`n|`n|`r)" | ForEach-Object {
  $line = $_
  if ($null -eq $line) { return }
  $line = $line.Trim()

  if ($line -eq "" -or $line.StartsWith("#")) { return }
  $idx = $line.IndexOf("=")
  if ($idx -lt 1) { return }

  # Strip zero-width/BOM-like chars from key
  $name = $line.Substring(0, $idx).Trim() -replace "^[`uFEFF`u200B`u200E`u200F]+",""
  $val  = $line.Substring($idx+1).Trim()

  # Remove inline comment if value has " # ..." and is not quoted
  if (-not ($val.StartsWith('"') -or $val.StartsWith("'"))) {
    $hashIdx = $val.IndexOf(" # ")
    if ($hashIdx -ge 0) { $val = $val.Substring(0, $hashIdx).Trim() }
  }

  # strip optional quotes
  if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Substring(1, $val.Length-2) }
  if ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Substring(1, $val.Length-2) }

  Set-Item -Path Env:$name -Value $val

  # Mask sensitive output
  $masked = $val
  if ($name -match "SECRET|API_KEY|TOKEN") {
    if ($val.Length -gt 6) { $masked = ("*" * ($val.Length-4)) + $val.Substring($val.Length-4) }
    else { $masked = "***" }
  }
  Write-Host ("set {0} = {1}" -f $name, $masked)
}

Write-Host "Loaded .env into session ✅"
