# clean_safely.ps1
param(
    [string]$Root = (Split-Path -Parent $MyInvocation.MyCommand.Path)
)

Write-Host ">>> Cleaning temp/junk in: $Root"

# 1) Remove __pycache__ and .pytest_tmp
Get-ChildItem -Path $Root -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $Root -Recurse -Directory -Filter ".pytest_tmp" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 2) Remove *.pyc / *.pyo
Get-ChildItem -Path $Root -Recurse -Include *.pyc,*.pyo -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# 3) Remove *.bak and files containing ".bak_" in name
Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '\.bak($|_)' -or $_.Name -like '*.bak' } | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host ">>> Done."
