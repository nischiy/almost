param([string]$Path = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $Path).Path
Get-ChildItem -LiteralPath $root -Recurse | ForEach-Object {
  $indent = "  " * ($_.FullName.Replace($root,"").Split([IO.Path]::DirectorySeparatorChar).Where({$_}).Count - 1)
  "{0}{1}" -f $indent, $_.Name
}
