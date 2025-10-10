
# run_tests.ps1
param([string]$Markers="")
python -m pip install -q pytest pandas
if ($LASTEXITCODE -ne 0) { exit 1 }
if ($Markers -ne "") {
  python -m pytest -q -m "$Markers"
} else {
  python -m pytest -q
}
