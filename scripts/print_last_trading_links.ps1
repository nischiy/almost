function To-Uri([string]$p) { "file:///" + $p.Replace('\','/') }
$root = (Resolve-Path ".").Path
$healthRoot = Join-Path $root "logs\health"
if (Test-Path $healthRoot) {
  $dateDirs = Get-ChildItem -Path $healthRoot -Directory | Sort-Object Name -Descending
  if ($dateDirs.Count -gt 0) {
    $latest = $dateDirs[0].FullName
    $jsonl = Get-ChildItem -Path $latest -Filter "health_*.jsonl" | Sort-Object Name -Descending | Select-Object -First 1
    $md    = Get-ChildItem -Path $latest -Filter "health_*.md"    | Sort-Object Name -Descending | Select-Object -First 1
    "Latest health folder: $latest"
    if ($jsonl) { "JSONL URI: " + (To-Uri $jsonl.FullName) }
    if ($md)    { "MD URI:    " + (To-Uri $md.FullName) }
  } else { "No dated subfolders under logs\health" }
} else { "No health logs yet" }
$ordersDir = Join-Path $root "logs\orders"
if (Test-Path $ordersDir) {
  $lastOrder = Get-ChildItem -Path $ordersDir -Filter "*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($lastOrder) { "Orders CSV URI: " + (To-Uri $lastOrder.FullName) } else { "No order CSVs yet" }
} else { "No orders dir" }
$equityDir = Join-Path $root "logs\equity"
if (Test-Path $equityDir) {
  $lastEq = Get-ChildItem -Path $equityDir -Filter "*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($lastEq) { "Equity CSV URI: " + (To-Uri $lastEq.FullName) } else { "No equity CSVs yet" }
} else { "No equity dir" }